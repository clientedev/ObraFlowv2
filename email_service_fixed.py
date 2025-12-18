"""
Serviço de envio de e-mail robusto para relatórios aprovados.
Usa SMTP com retry automático e melhor tratamento de erros.
Funciona tanto localmente quanto na produção.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone, timedelta
from flask import current_app
import time


class ReportApprovalEmailService:
    """Serviço robusto de envio de e-mails com retry automático"""
    
    def __init__(self):
        self.from_email = os.getenv('GMAIL_EMAIL', "relatorioselpconsultoria@gmail.com")
        self.from_password = os.getenv('GMAIL_PASSWORD', "ipbs dkwc osyn vixg")
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 587  # TLS (mais compatível com produção que SSL)
        self.timeout = 30
        self.max_retries = 3
        
        current_app.logger.info(f"📧 Email Service inicializado: {self.from_email}")
    
    def _get_smtp_connection(self):
        """Estabelece conexão SMTP com retry automático"""
        for attempt in range(self.max_retries):
            try:
                current_app.logger.info(f"🔌 Tentativa {attempt+1}/{self.max_retries} de conexão SMTP...")
                
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout)
                server.starttls()  # Usar TLS
                server.login(self.from_email, self.from_password)
                
                current_app.logger.info(f"✅ Conexão SMTP estabelecida com sucesso!")
                return server
            
            except smtplib.SMTPAuthenticationError as e:
                current_app.logger.error(f"❌ Erro de autenticação: {e}")
                raise
            except (smtplib.SMTPException, OSError) as e:
                current_app.logger.warning(f"⚠️ Erro de conexão (tentativa {attempt+1}): {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Backoff exponencial: 1s, 2s, 4s
                    current_app.logger.info(f"⏳ Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    current_app.logger.error(f"❌ Falha após {self.max_retries} tentativas")
                    raise
        
        raise Exception("Impossível conectar ao servidor SMTP")
    
    def _get_recipients_for_report(self, relatorio):
        """Coleta os destinatários do relatório"""
        recipients = set()
        
        try:
            current_app.logger.info(f"🔍 Coletando destinatários para relatório {relatorio.numero}")
            
            # 1. Autor do relatório
            if relatorio.autor and relatorio.autor.email:
                recipients.add(relatorio.autor.email)
                current_app.logger.info(f"✉️ [AUTOR] {relatorio.autor.email}")
            
            # 2. Aprovador
            if relatorio.aprovador and relatorio.aprovador.email:
                recipients.add(relatorio.aprovador.email)
                current_app.logger.info(f"✉️ [APROVADOR] {relatorio.aprovador.email}")
            
            # 3. Email da obra
            if hasattr(relatorio, 'obra_email') and relatorio.obra_email:
                recipients.add(relatorio.obra_email)
                current_app.logger.info(f"✉️ [OBRA] {relatorio.obra_email}")
            elif hasattr(relatorio, 'projeto') and relatorio.projeto and relatorio.projeto.email:
                recipients.add(relatorio.projeto.email)
                current_app.logger.info(f"✉️ [PROJETO] {relatorio.projeto.email}")
            
            # 4. Acompanhantes
            if hasattr(relatorio, 'acompanhantes') and relatorio.acompanhantes:
                try:
                    import json
                    acompanhantes_list = []
                    
                    if isinstance(relatorio.acompanhantes, str):
                        try:
                            acompanhantes_list = json.loads(relatorio.acompanhantes)
                        except:
                            acompanhantes_list = []
                    elif isinstance(relatorio.acompanhantes, list):
                        acompanhantes_list = relatorio.acompanhantes
                    
                    if isinstance(acompanhantes_list, list):
                        for acomp in acompanhantes_list:
                            if isinstance(acomp, dict) and acomp.get('email'):
                                recipients.add(acomp['email'])
                                current_app.logger.info(f"✉️ [ACOMPANHANTE] {acomp['email']}")
                except Exception as e:
                    current_app.logger.warning(f"⚠️ Erro ao processar acompanhantes: {e}")
            
            current_app.logger.info(f"📊 Total de {len(recipients)} destinatário(s)")
            return list(recipients)
        
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao coletar destinatários: {e}")
            return []
    
    def _format_email_body(self, destinatario_nome, nome_obra, data_aprovacao):
        """Formata o corpo do e-mail"""
        if data_aprovacao:
            try:
                brasilia_tz = timezone(timedelta(hours=-3))
                data_brasilia = data_aprovacao.replace(tzinfo=timezone.utc).astimezone(brasilia_tz)
                data_formatada = data_brasilia.strftime("%d/%m/%Y às %H:%M")
            except:
                data_formatada = "data não disponível"
        else:
            data_formatada = "data não disponível"
        
        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Relatório Aprovado</h2>
                <p>Olá {destinatario_nome},</p>
                <p>O relatório da obra <strong>"{nome_obra}"</strong> foi aprovado em <strong>{data_formatada}</strong>.</p>
                <p>Segue em anexo o arquivo PDF do relatório aprovado.</p>
                <hr>
                <p><small>Este é um e-mail automático. Por favor, não responda este e-mail.</small></p>
            </body>
        </html>
        """
        return corpo_html
    
    def send_approval_email(self, relatorio, pdf_path):
        """Envia e-mail de aprovação com retry automático"""
        try:
            recipients = self._get_recipients_for_report(relatorio)
            
            if not recipients:
                current_app.logger.warning(f"⚠️ Nenhum destinatário encontrado")
                return {'success': False, 'enviados': 0, 'error': 'Nenhum destinatário válido'}
            
            # Verificar se PDF existe
            if not os.path.exists(pdf_path):
                current_app.logger.warning(f"⚠️ PDF não encontrado: {pdf_path}")
                return {'success': False, 'enviados': 0, 'error': f'PDF não encontrado'}
            
            # Obter nome da obra
            obra_nome = "Obra"
            if hasattr(relatorio, 'projeto') and relatorio.projeto:
                obra_nome = relatorio.projeto.nome
            elif hasattr(relatorio, 'obra_nome'):
                obra_nome = relatorio.obra_nome
            
            assunto = f"Relatório aprovado – Obra {obra_nome}"
            
            current_app.logger.info(f"📧 Iniciando envio para {len(recipients)} destinatário(s)")
            
            # Obter conexão SMTP com retry
            server = self._get_smtp_connection()
            
            enviados = 0
            erros = []
            
            try:
                for idx, recipient_email in enumerate(recipients, 1):
                    try:
                        # Criar mensagem
                        msg = MIMEMultipart()
                        msg['From'] = self.from_email
                        msg['To'] = recipient_email
                        msg['Subject'] = assunto
                        
                        # Obter nome do destinatário
                        destinatario_nome = recipient_email.split('@')[0]
                        try:
                            from models import User
                            user = User.query.filter_by(email=recipient_email).first()
                            if user and user.nome_completo:
                                destinatario_nome = user.nome_completo
                        except:
                            pass
                        
                        # Body HTML
                        corpo = self._format_email_body(destinatario_nome, obra_nome, relatorio.data_aprovacao)
                        msg.attach(MIMEText(corpo, 'html'))
                        
                        # Anexar PDF
                        with open(pdf_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(pdf_path)}')
                            msg.attach(part)
                        
                        # Enviar
                        server.send_message(msg)
                        enviados += 1
                        current_app.logger.info(f"✅ Email {idx}/{len(recipients)} enviado: {recipient_email}")
                    
                    except Exception as e:
                        erro = f"Erro ao enviar para {recipient_email}: {str(e)}"
                        erros.append(erro)
                        current_app.logger.error(f"❌ {erro}")
            
            finally:
                server.quit()
            
            if enviados > 0:
                current_app.logger.info(f"✅ SUCESSO: {enviados}/{len(recipients)} e-mail(s) enviado(s)")
                return {'success': True, 'enviados': enviados, 'total': len(recipients), 'error': None}
            else:
                erro_final = "; ".join(erros) if erros else "Falha ao enviar e-mails"
                return {'success': False, 'enviados': 0, 'total': len(recipients), 'error': erro_final}
        
        except Exception as e:
            current_app.logger.error(f"💥 Erro geral: {e}", exc_info=True)
            return {'success': False, 'enviados': 0, 'error': str(e)}
