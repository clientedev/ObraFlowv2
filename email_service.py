"""
Sistema de envio de e-mails para relatórios
Suporte para SMTP (Gmail, Outlook) e APIs (SendGrid, Amazon SES)
"""

import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import requests
from flask import current_app
from flask_mail import Mail, Message
from models import LogEnvioEmail, ConfiguracaoEmail, EmailCliente
from app import db

class EmailService:
    def __init__(self):
        self.mail = None
    
    def configure_smtp(self, config):
        """Configurar SMTP baseado na configuração"""
        current_app.config['MAIL_SERVER'] = config.servidor_smtp
        current_app.config['MAIL_PORT'] = config.porta_smtp
        current_app.config['MAIL_USE_TLS'] = config.use_tls
        current_app.config['MAIL_USE_SSL'] = config.use_ssl
        current_app.config['MAIL_USERNAME'] = config.email_remetente
        current_app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
        current_app.config['MAIL_DEFAULT_SENDER'] = (config.nome_remetente, config.email_remetente)
        
        self.mail = Mail(current_app)
        return True
    
    def get_configuracao_ativa(self):
        """Buscar configuração de email ativa"""
        return ConfiguracaoEmail.query.filter_by(ativo=True).first()
    
    def enviar_relatorio_por_email(self, relatorio, destinatarios_data, usuario_id):
        """
        Enviar relatório por e-mail
        
        Args:
            relatorio: Objeto Relatorio
            destinatarios_data: {
                'destinatarios': ['email1@test.com'],
                'cc': ['email2@test.com'],
                'bcc': ['email3@test.com'],
                'assunto_custom': 'Assunto personalizado',
                'corpo_custom': 'Corpo personalizado'
            }
            usuario_id: ID do usuário que está enviando
        """
        try:
            # Buscar configuração ativa
            config = self.get_configuracao_ativa()
            if not config:
                raise Exception("Nenhuma configuração de e-mail ativa encontrada")
            
            # Configurar SMTP
            self.configure_smtp(config)
            
            # Preparar dados do e-mail
            projeto = relatorio.projeto
            data_visita = relatorio.data_visita.strftime('%d/%m/%Y') if relatorio.data_visita else 'N/A'
            data_atual = datetime.now().strftime('%d/%m/%Y')
            
            # Gerar assunto
            assunto = destinatarios_data.get('assunto_custom') or config.template_assunto.format(
                projeto_nome=projeto.nome,
                data=data_atual
            )
            
            # Gerar corpo do e-mail
            corpo_base = destinatarios_data.get('corpo_custom') or config.template_corpo
            
            # Lista para armazenar logs de cada envio
            logs_envio = []
            
            # Enviar para cada destinatário principal
            for email_dest in destinatarios_data.get('destinatarios', []):
                try:
                    # Buscar dados do cliente se disponível
                    email_cliente = EmailCliente.query.filter_by(
                        projeto_id=projeto.id, 
                        email=email_dest
                    ).first()
                    
                    nome_cliente = email_cliente.nome_contato if email_cliente else "Cliente"
                    
                    # Personalizar corpo do e-mail
                    corpo_html = corpo_base.format(
                        nome_cliente=nome_cliente,
                        data_visita=data_visita,
                        projeto_nome=projeto.nome
                    )
                    
                    # Criar mensagem
                    msg = Message(
                        subject=assunto,
                        recipients=[email_dest],
                        cc=destinatarios_data.get('cc', []),
                        bcc=destinatarios_data.get('bcc', []),
                        html=corpo_html
                    )
                    
                    # Gerar e anexar PDF
                    from pdf_generator_weasy import gerar_pdf_relatorio_weasy
                    pdf_path = gerar_pdf_relatorio_weasy(relatorio.id)
                    
                    if pdf_path and os.path.exists(pdf_path):
                        with current_app.open_resource(pdf_path, 'rb') as f:
                            msg.attach(
                                filename=f"Relatorio_{projeto.numero}_{data_atual.replace('/', '')}.pdf",
                                content_type='application/pdf',
                                data=f.read()
                            )
                    
                    # Enviar e-mail
                    self.mail.send(msg)
                    
                    # Log de sucesso
                    log_envio = LogEnvioEmail(
                        projeto_id=projeto.id,
                        relatorio_id=relatorio.id,
                        usuario_id=usuario_id,
                        destinatarios=json.dumps([email_dest]),
                        cc=json.dumps(destinatarios_data.get('cc', [])),
                        bcc=json.dumps(destinatarios_data.get('bcc', [])),
                        assunto=assunto,
                        status='enviado'
                    )
                    logs_envio.append(log_envio)
                    
                    # Limpar arquivo PDF temporário
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            os.remove(pdf_path)
                        except:
                            pass
                    
                except Exception as e:
                    # Log de erro
                    log_envio = LogEnvioEmail(
                        projeto_id=projeto.id,
                        relatorio_id=relatorio.id,
                        usuario_id=usuario_id,
                        destinatarios=json.dumps([email_dest]),
                        cc=json.dumps(destinatarios_data.get('cc', [])),
                        bcc=json.dumps(destinatarios_data.get('bcc', [])),
                        assunto=assunto,
                        status='falhou',
                        erro_detalhes=str(e)
                    )
                    logs_envio.append(log_envio)
            
            # Salvar todos os logs
            for log in logs_envio:
                db.session.add(log)
            db.session.commit()
            
            # Retornar resultado
            sucessos = sum(1 for log in logs_envio if log.status == 'enviado')
            falhas = sum(1 for log in logs_envio if log.status == 'falhou')
            
            return {
                'success': sucessos > 0,
                'total_destinatarios': len(destinatarios_data.get('destinatarios', [])),
                'sucessos': sucessos,
                'falhas': falhas,
                'logs': logs_envio
            }
            
        except Exception as e:
            # Log geral de erro
            log_envio = LogEnvioEmail(
                projeto_id=relatorio.projeto.id,
                relatorio_id=relatorio.id,
                usuario_id=usuario_id,
                destinatarios=json.dumps(destinatarios_data.get('destinatarios', [])),
                cc=json.dumps(destinatarios_data.get('cc', [])),
                bcc=json.dumps(destinatarios_data.get('bcc', [])),
                assunto=destinatarios_data.get('assunto_custom', 'Erro ao gerar assunto'),
                status='falhou',
                erro_detalhes=str(e)
            )
            db.session.add(log_envio)
            db.session.commit()
            
            return {
                'success': False,
                'error': str(e),
                'total_destinatarios': len(destinatarios_data.get('destinatarios', [])),
                'sucessos': 0,
                'falhas': len(destinatarios_data.get('destinatarios', [])),
                'logs': [log_envio]
            }
    
    def validar_emails(self, emails):
        """Validar lista de e-mails"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        emails_validos = []
        emails_invalidos = []
        
        for email in emails:
            email = email.strip()
            if re.match(email_pattern, email):
                emails_validos.append(email)
            else:
                emails_invalidos.append(email)
        
        return emails_validos, emails_invalidos
    
    def buscar_emails_projeto(self, projeto_id):
        """Buscar todos os e-mails vinculados ao projeto"""
        emails = EmailCliente.query.filter_by(
            projeto_id=projeto_id,
            ativo=True,
            receber_relatorios=True
        ).all()
        
        return emails

# Instância global do serviço
email_service = EmailService()