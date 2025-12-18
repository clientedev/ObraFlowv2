"""
Serviço de envio de e-mail via yagmail para relatórios aprovados.
Usa conta Gmail fixa: relatorioselp@gmail.com
Envia e-mails para os envolvidos quando um relatório é aprovado.
"""
import os
import yagmail
from datetime import datetime
from flask import current_app


class ReportApprovalEmailService:
    """Serviço de envio de e-mails via yagmail"""
    
    def __init__(self):
        self.from_email = "relatorioselp@gmail.com"
        # Use App Password gerada em https://myaccount.google.com/apppasswords
        # Se 2FA estiver ativado, a senha comum NÃO funciona
        self.from_password = "Relatorios#2025"
        self.yag = None
    
    def _get_yag_connection(self):
        """Obter conexão yagmail (lazy connection)"""
        if self.yag is None:
            try:
                self.yag = yagmail.SMTP(self.from_email, self.from_password)
                current_app.logger.info(f"✅ Conexão yagmail estabelecida com {self.from_email}")
            except Exception as e:
                current_app.logger.error(f"❌ Erro ao conectar com yagmail: {e}")
                raise
        return self.yag
    
    def _get_recipients_for_report(self, relatorio):
        """
        Coleta APENAS os destinatários relacionados ao relatório.
        Retorna lista de emails únicos.
        
        Destinatários:
        - Pessoa que criou o relatório (autor)
        - Aprovador global
        - Todos os acompanhantes da visita vinculados ao relatório
        
        NÃO inclui funcionários da obra, apenas os envolvidos no relatório.
        """
        recipients = set()  # usar set para evitar duplicatas
        
        try:
            # 1. Autor do relatório
            if relatorio.autor and relatorio.autor.email:
                recipients.add(relatorio.autor.email)
                current_app.logger.info(f"✉️ Autor adicionado: {relatorio.autor.email}")
            
            # 2. Aprovador global
            if relatorio.aprovador and relatorio.aprovador.email:
                recipients.add(relatorio.aprovador.email)
                current_app.logger.info(f"✉️ Aprovador adicionado: {relatorio.aprovador.email}")
            
            # 3. Acompanhantes da visita vinculados ao relatório
            if relatorio.acompanhantes:
                try:
                    acompanhantes_list = relatorio.acompanhantes if isinstance(relatorio.acompanhantes, list) else []
                    for acomp in acompanhantes_list:
                        if isinstance(acomp, dict) and acomp.get('email'):
                            email = acomp['email'].strip()
                            if email:
                                recipients.add(email)
                                current_app.logger.info(f"✉️ Acompanhante adicionado: {email}")
                except Exception as e:
                    current_app.logger.warning(f"⚠️ Erro ao processar acompanhantes: {e}")
        
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
"""
        return corpo
    
    def send_approval_email(self, relatorio, pdf_path):
        """
        Envia e-mail de aprovação para todos os envolvidos via yagmail.
        Um email por destinatário (sem CC/BCC).
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
            
            # Obter conexão yagmail
            yag = self._get_yag_connection()
            
            enviados = 0
            
            # Enviar e-mail individual para cada destinatário
            for recipient_email in recipients:
                try:
                    # Obter nome do destinatário
                    destinatario_nome = recipient_email.split('@')[0]  # fallback
                    
                    # Tentar encontrar nome completo do usuário
                    from models import User
                    user = User.query.filter_by(email=recipient_email).first()
                    if user:
                        destinatario_nome = user.nome_completo or user.username
                    
                    # Corpo do e-mail
                    corpo = self._format_email_body(destinatario_nome, obra_nome, relatorio.data_aprovacao)
                    
                    # Enviar via yagmail
                    # yagmail.send(to, subject, contents, attachments)
                    yag.send(
                        to=recipient_email,
                        subject=assunto,
                        contents=corpo,
                        attachments=pdf_path
                    )
                    
                    enviados += 1
                    current_app.logger.info(f"✅ E-mail enviado com sucesso para {recipient_email}")
                
                except Exception as e:
                    current_app.logger.error(f"❌ Erro ao enviar e-mail para {recipient_email}: {e}")
                    # Continua tentando os outros destinatários
            
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
