"""
Serviço de envio de e-mail SMTP para relatórios aprovados.
Envia e-mails para todos os envolvidos quando um relatório é aprovado.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from flask import current_app


class ReportApprovalEmailService:
    """Serviço de envio de e-mails após aprovação de relatório"""
    
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.from_email = "relatorios@elpconsultoria.eng.br"
        self.from_password = "1234567890"
    
    def _get_recipients_for_report(self, relatorio):
        """
        Coleta todos os destinatários relacionados ao relatório.
        Retorna lista de emails únicos.
        """
        recipients = set()  # usar set para evitar duplicatas
        
        try:
            # 1. Autor do relatório
            if relatorio.autor and relatorio.autor.email:
                recipients.add(relatorio.autor.email)
                current_app.logger.info(f"✉️ Adicionado autor: {relatorio.autor.email}")
            
            # 2. Aprovador global
            if relatorio.aprovador and relatorio.aprovador.email:
                recipients.add(relatorio.aprovador.email)
                current_app.logger.info(f"✉️ Adicionado aprovador: {relatorio.aprovador.email}")
            
            # 3. Acompanhantes da visita vinculados ao relatório
            if relatorio.acompanhantes:
                try:
                    acompanhantes_list = relatorio.acompanhantes if isinstance(relatorio.acompanhantes, list) else []
                    for acomp in acompanhantes_list:
                        if isinstance(acomp, dict) and acomp.get('email'):
                            email = acomp['email'].strip()
                            if email:
                                recipients.add(email)
                                current_app.logger.info(f"✉️ Adicionado acompanhante: {email}")
                except Exception as e:
                    current_app.logger.warning(f"⚠️ Erro ao processar acompanhantes: {e}")
            
            # 4. Responsável da obra (se existir projeto)
            if relatorio.projeto and relatorio.projeto.responsavel and relatorio.projeto.responsavel.email:
                recipients.add(relatorio.projeto.responsavel.email)
                current_app.logger.info(f"✉️ Adicionado responsável da obra: {relatorio.projeto.responsavel.email}")
            
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao coletar destinatários: {e}")
        
        return list(recipients)
    
    def _format_email_body(self, destinatario_nome, nome_obra, data_aprovacao):
        """Formata o corpo do e-mail de aprovação"""
        data_formatada = data_aprovacao.strftime("%d/%m/%Y às %H:%M") if data_aprovacao else "data não disponível"
        
        corpo = f"""Olá {destinatario_nome},

O relatório da obra "{nome_obra}" foi aprovado em {data_formatada}.

Segue em anexo o arquivo PDF do relatório aprovado.

Este é um e-mail automático.
Por favor, não responda este e-mail.

---
ELP Consultoria
relatorios@elpconsultoria.eng.br
"""
        return corpo
    
    def send_approval_email(self, relatorio, pdf_path):
        """
        Envia e-mail de aprovação para todos os envolvidos.
        Retorna dicionário com resultado: {'success': bool, 'enviados': int, 'error': str}
        """
        try:
            recipients = self._get_recipients_for_report(relatorio)
            
            if not recipients:
                current_app.logger.warning(f"⚠️ Nenhum destinatário encontrado para relatório {relatorio.numero}")
                return {
                    'success': False,
                    'enviados': 0,
                    'error': 'Nenhum destinatário válido encontrado'
                }
            
            obra_nome = relatorio.projeto.nome if relatorio.projeto else "Obra"
            assunto = f"Relatório aprovado – Obra {obra_nome}"
            
            current_app.logger.info(f"📧 Iniciando envio de e-mail para relatório {relatorio.numero}")
            current_app.logger.info(f"📧 Destinatários: {recipients}")
            current_app.logger.info(f"📧 PDF path: {pdf_path}")
            
            # Verificar se PDF existe
            if not os.path.exists(pdf_path):
                current_app.logger.warning(f"⚠️ PDF não encontrado: {pdf_path}")
                return {
                    'success': False,
                    'enviados': 0,
                    'error': f'Arquivo PDF não encontrado: {pdf_path}'
                }
            
            enviados = 0
            
            # Enviar e-mail para cada destinatário individualmente
            for recipient_email in recipients:
                try:
                    # Obter nome do destinatário
                    destinatario_nome = recipient_email.split('@')[0]  # fallback
                    
                    # Tentar encontrar nome completo do usuário
                    from models import User
                    user = User.query.filter_by(email=recipient_email).first()
                    if user:
                        destinatario_nome = user.nome_completo or user.username
                    
                    # Preparar e-mail
                    msg = MIMEMultipart()
                    msg['From'] = self.from_email
                    msg['To'] = recipient_email
                    msg['Subject'] = assunto
                    
                    # Corpo do e-mail
                    corpo = self._format_email_body(destinatario_nome, obra_nome, relatorio.data_aprovacao)
                    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
                    
                    # Anexar PDF se existir
                    if os.path.exists(pdf_path):
                        try:
                            with open(pdf_path, 'rb') as attachment:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())
                            
                            encoders.encode_base64(part)
                            pdf_filename = os.path.basename(pdf_path)
                            part.add_header('Content-Disposition', f'attachment; filename= {pdf_filename}')
                            msg.attach(part)
                        except Exception as e:
                            current_app.logger.warning(f"⚠️ Erro ao anexar PDF: {e}")
                    
                    # Enviar e-mail via SMTP
                    try:
                        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                        server.starttls()
                        server.login(self.from_email, self.from_password)
                        server.send_message(msg)
                        server.quit()
                        
                        enviados += 1
                        current_app.logger.info(f"✅ E-mail enviado para {recipient_email}")
                    
                    except smtplib.SMTPAuthenticationError:
                        current_app.logger.error(f"❌ Erro de autenticação SMTP para {recipient_email}")
                    except smtplib.SMTPException as e:
                        current_app.logger.error(f"❌ Erro SMTP para {recipient_email}: {e}")
                    except Exception as e:
                        current_app.logger.error(f"❌ Erro ao enviar e-mail para {recipient_email}: {e}")
                
                except Exception as e:
                    current_app.logger.error(f"❌ Erro ao processar destinatário {recipient_email}: {e}")
            
            if enviados > 0:
                current_app.logger.info(f"✅ Sucesso: {enviados} e-mail(s) enviado(s) para relatório {relatorio.numero}")
                return {
                    'success': True,
                    'enviados': enviados,
                    'error': None
                }
            else:
                current_app.logger.error(f"❌ Falha ao enviar e-mails para relatório {relatorio.numero}")
                return {
                    'success': False,
                    'enviados': 0,
                    'error': 'Falha ao enviar e-mails para todos os destinatários'
                }
        
        except Exception as e:
            current_app.logger.error(f"💥 Erro geral ao enviar e-mail para relatório: {e}")
            return {
                'success': False,
                'enviados': 0,
                'error': str(e)
            }
