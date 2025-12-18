"""
Serviço de envio de e-mail usando SendGrid para relatórios aprovados.
Alternativa segura e confiável ao SMTP do Gmail.
"""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import os
import base64
from flask import current_app


class ReportApprovalEmailServiceSendGrid:
    """Serviço de envio de e-mails após aprovação de relatório usando SendGrid"""
    
    def __init__(self):
        """Inicializa o serviço com API key do SendGrid"""
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = "relatorios@elpconsultoria.eng.br"
        
        if not self.api_key:
            current_app.logger.warning("⚠️ SENDGRID_API_KEY não configurada")
    
    def _get_recipients_for_report(self, relatorio):
        """
        Coleta todos os destinatários relacionados ao relatório.
        Retorna lista de emails únicos.
        """
        recipients = set()
        
        try:
            # 1. Autor do relatório
            if relatorio.autor and relatorio.autor.email:
                recipients.add(relatorio.autor.email)
                current_app.logger.info(f"✉️ Adicionado autor: {relatorio.autor.email}")
            
            # 2. Aprovador global
            if relatorio.aprovador and relatorio.aprovador.email:
                recipients.add(relatorio.aprovador.email)
                current_app.logger.info(f"✉️ Adicionado aprovador: {relatorio.aprovador.email}")
            
            # 3. Acompanhantes da visita
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
            
            # 4. Responsável da obra
            if relatorio.projeto and relatorio.projeto.responsavel and relatorio.projeto.responsavel.email:
                recipients.add(relatorio.projeto.responsavel.email)
                current_app.logger.info(f"✉️ Adicionado responsável da obra: {relatorio.projeto.responsavel.email}")
            
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao coletar destinatários: {e}")
        
        return list(recipients)
    
    def send_approval_email(self, relatorio, pdf_path):
        """
        Envia e-mail de aprovação usando SendGrid.
        Retorna dicionário com resultado: {'success': bool, 'enviados': int, 'error': str}
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'enviados': 0,
                    'error': 'SENDGRID_API_KEY não configurada'
                }
            
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
            
            current_app.logger.info(f"📧 Iniciando envio via SendGrid para relatório {relatorio.numero}")
            current_app.logger.info(f"📧 Destinatários: {recipients}")
            
            # Verificar se PDF existe
            if not os.path.exists(pdf_path):
                current_app.logger.warning(f"⚠️ PDF não encontrado: {pdf_path}")
                return {
                    'success': False,
                    'enviados': 0,
                    'error': f'Arquivo PDF não encontrado: {pdf_path}'
                }
            
            sg = SendGridAPIClient(self.api_key)
            enviados = 0
            
            # Ler PDF para anexar
            with open(pdf_path, 'rb') as attachment_file:
                attachment_data = base64.b64encode(attachment_file.read()).decode()
            
            pdf_filename = os.path.basename(pdf_path)
            
            # Enviar para cada destinatário
            for recipient_email in recipients:
                try:
                    message = Mail(
                        from_email=self.from_email,
                        to_emails=recipient_email,
                        subject=assunto,
                        plain_text_content=self._format_email_body(
                            recipient_email.split('@')[0],
                            obra_nome,
                            relatorio.data_aprovacao
                        )
                    )
                    
                    # Anexar PDF
                    attachment = Attachment(
                        FileContent(attachment_data),
                        FileName(pdf_filename),
                        FileType('application/pdf'),
                        Disposition('attachment')
                    )
                    message.attachment = attachment
                    
                    # Enviar
                    sg.send(message)
                    enviados += 1
                    current_app.logger.info(f"✅ E-mail enviado para {recipient_email} via SendGrid")
                
                except Exception as e:
                    current_app.logger.error(f"❌ Erro ao enviar para {recipient_email}: {e}")
            
            if enviados > 0:
                current_app.logger.info(f"✅ Sucesso: {enviados} e-mail(s) enviado(s) via SendGrid")
                return {
                    'success': True,
                    'enviados': enviados,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'enviados': 0,
                    'error': 'Falha ao enviar e-mails'
                }
        
        except Exception as e:
            current_app.logger.error(f"💥 Erro geral ao enviar e-mail: {e}")
            return {
                'success': False,
                'enviados': 0,
                'error': str(e)
            }
    
    def _format_email_body(self, destinatario_nome, nome_obra, data_aprovacao):
        """Formata o corpo do e-mail de aprovação"""
        from datetime import datetime
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
