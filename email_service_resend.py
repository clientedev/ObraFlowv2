"""
Serviço de envio de e-mail via Resend API para relatórios aprovados.
Substitui yagmail com HTTP POST para Resend em thread daemon.
"""
import os
import json
import base64
import requests
import threading
from datetime import datetime
from flask import current_app


class ReportApprovalEmailService:
    """Serviço de envio de e-mails via Resend API"""
    
    def __init__(self):
        self.api_key = os.getenv('RESEND_API_KEY', 're_KBL5z16g_8CKfLhWgFJxwvGUiX6XroKBg')
        self.from_email = "noreply@elpconsultoria.pro"
        self.resend_endpoint = "https://api.resend.com/emails"
        
        current_app.logger.info(f"📧 Resend Service inicializado com: {self.from_email}")
    
    def _get_recipients_for_report(self, relatorio):
        """
        Coleta APENAS os destinatários relacionados ao relatório.
        Retorna lista de emails únicos com logs detalhados.
        
        Destinatários:
        - Pessoa que criou o relatório (autor)
        - Aprovador global
        - Contato de email da obra
        - Todos os acompanhantes da visita vinculados ao relatório
        
        NÃO inclui funcionários da obra, apenas os envolvidos no relatório.
        """
        recipients = set()
        
        try:
            current_app.logger.info(f"🔍 Coletando destinatários para relatório {relatorio.numero}")
            
            # 1. Autor do relatório
            if relatorio.autor and relatorio.autor.email:
                recipients.add(relatorio.autor.email)
                current_app.logger.info(f"✉️ [AUTOR] {relatorio.autor.nome_completo or relatorio.autor.username} ({relatorio.autor.email})")
            else:
                current_app.logger.warning(f"⚠️ [AUTOR] Sem email encontrado")
            
            # 2. Aprovador global
            if relatorio.aprovador and relatorio.aprovador.email:
                recipients.add(relatorio.aprovador.email)
                current_app.logger.info(f"✉️ [APROVADOR] {relatorio.aprovador.nome_completo or relatorio.aprovador.username} ({relatorio.aprovador.email})")
            else:
                current_app.logger.warning(f"⚠️ [APROVADOR] Sem email ou não atribuído")
            
            # 3. Contato de email da obra
            obra_email = None
            if hasattr(relatorio, 'obra_email'):
                obra_email = (relatorio.obra_email or '').strip()
            elif hasattr(relatorio, 'projeto') and relatorio.projeto and hasattr(relatorio.projeto, 'email'):
                obra_email = (relatorio.projeto.email or '').strip()
            
            if obra_email:
                recipients.add(obra_email)
                current_app.logger.info(f"✉️ [OBRA] Contato da obra ({obra_email})")
            else:
                current_app.logger.info(f"ℹ️ [OBRA] Sem email de contato registrado")
            
            # 4. Acompanhantes da visita vinculados ao relatório
            if relatorio.acompanhantes:
                current_app.logger.info(f"🔍 Processando acompanhantes: {type(relatorio.acompanhantes)}")
                acompanhantes_list = []
                
                # Converter para lista se necessário
                if isinstance(relatorio.acompanhantes, list):
                    acompanhantes_list = relatorio.acompanhantes
                    current_app.logger.info(f"✅ Acompanhantes é uma lista")
                elif isinstance(relatorio.acompanhantes, str):
                    try:
                        acompanhantes_list = json.loads(relatorio.acompanhantes)
                        if not isinstance(acompanhantes_list, list):
                            acompanhantes_list = []
                        current_app.logger.info(f"✅ Acompanhantes parseado de JSON string")
                    except json.JSONDecodeError:
                        current_app.logger.warning(f"⚠️ Falha ao parsear acompanhantes JSON")
                
                for acompanhante_id in acompanhantes_list:
                    try:
                        from models import VisitaAcompanhante
                        acompanhante = VisitaAcompanhante.query.get(acompanhante_id)
                        if acompanhante and acompanhante.email:
                            email = acompanhante.email.strip()
                            if email:
                                recipients.add(email)
                                current_app.logger.info(f"✉️ [ACOMPANHANTE] {acompanhante.nome or acompanhante_id} ({email})")
                    except Exception as e:
                        current_app.logger.warning(f"⚠️ Erro ao processar acompanhante {acompanhante_id}: {e}")
            
            # Filtrar emails inválidos
            recipients = set(email.strip() for email in recipients if email and '@' in email)
            current_app.logger.info(f"✅ Total de destinatários únicos: {len(recipients)}")
            
            return list(recipients)
        
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao coletar destinatários: {e}", exc_info=True)
            return []
    
    def _format_email_body(self, nome_destinatario, obra_nome, data_aprovacao):
        """Formato HTML do corpo do e-mail"""
        if not data_aprovacao:
            data_aprovacao = datetime.now()
        
        data_formatada = data_aprovacao.strftime("%d/%m/%Y às %H:%M") if hasattr(data_aprovacao, 'strftime') else str(data_aprovacao)
        
        corpo_html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 20px auto; background-color: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                    .content {{ padding: 20px; line-height: 1.6; color: #333; }}
                    .footer {{ background-color: #f9f9f9; padding: 10px; font-size: 12px; text-align: center; color: #666; border-top: 1px solid #ddd; margin-top: 20px; }}
                    .highlight {{ color: #667eea; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>✅ Relatório Aprovado</h2>
                    </div>
                    <div class="content">
                        <p>Olá <span class="highlight">{nome_destinatario}</span>,</p>
                        <p>Temos o prazer de informar que o relatório da obra <span class="highlight">{obra_nome}</span> foi <span class="highlight">aprovado com sucesso</span>.</p>
                        <p><strong>Data de aprovação:</strong> {data_formatada}</p>
                        <p>O documento está em anexo para sua conveniência.</p>
                        <p>Em caso de dúvidas ou necessidade de revisões, por favor entre em contato com o setor responsável.</p>
                        <p>Atenciosamente,<br><strong>ELP Consultoria</strong></p>
                    </div>
                    <div class="footer">
                        <p>Por favor, não responda este e-mail. Este é um e-mail automático.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return corpo_html
    
    def send_approval_email(self, relatorio, pdf_path):
        """
        Envia e-mail de aprovação com Resend (não bloqueia a requisição).
        Retorna sucesso mesmo que falhe (email é enviado em background).
        """
        try:
            current_app.logger.info(f"📧 Iniciando envio de email para relatório {relatorio.numero}")
            
            recipients = self._get_recipients_for_report(relatorio)
            
            if not recipients:
                current_app.logger.warning(f"⚠️ Nenhum destinatário para {relatorio.numero}")
                return {'success': True, 'enviados': 0, 'error': None}
            
            # Obter nome da obra
            obra_nome = "Obra"
            if hasattr(relatorio, 'projeto') and relatorio.projeto:
                obra_nome = relatorio.projeto.nome
            elif hasattr(relatorio, 'obra_nome'):
                obra_nome = relatorio.obra_nome or "Obra"
            
            # PDF existe?
            if not os.path.exists(pdf_path):
                current_app.logger.warning(f"⚠️ PDF não encontrado: {pdf_path}")
                return {'success': True, 'enviados': 0, 'error': None}
            
            assunto = f"Relatório aprovado – Obra {obra_nome}"
            
            # Executar em thread daemon (não bloqueia)
            def enviar_emails_resend():
                try:
                    current_app.logger.info(f"[THREAD] 🧵 Thread iniciada - Resend API")
                    
                    # Ler PDF e converter para base64
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')
                    
                    enviados = 0
                    
                    for recipient_email in recipients:
                        try:
                            destinatario_nome = recipient_email.split('@')[0]
                            try:
                                from models import User
                                user = User.query.filter_by(email=recipient_email).first()
                                if user and user.nome_completo:
                                    destinatario_nome = user.nome_completo
                            except:
                                pass
                            
                            corpo_html = self._format_email_body(destinatario_nome, obra_nome, relatorio.data_aprovacao)
                            
                            current_app.logger.info(f"[THREAD] 📤 Enviando para {recipient_email}...")
                            
                            # Payload para Resend
                            payload = {
                                "from": self.from_email,
                                "to": recipient_email,
                                "subject": assunto,
                                "html": corpo_html,
                                "attachments": [
                                    {
                                        "filename": os.path.basename(pdf_path),
                                        "content": pdf_base64
                                    }
                                ]
                            }
                            
                            # Headers com API key
                            headers = {
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            }
                            
                            # Fazer POST para Resend
                            response = requests.post(
                                self.resend_endpoint,
                                json=payload,
                                headers=headers,
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                enviados += 1
                                current_app.logger.info(f"[THREAD] ✅ Email enviado para {recipient_email}")
                            else:
                                error_msg = response.text if response.text else "Status " + str(response.status_code)
                                current_app.logger.warning(f"[THREAD] ⚠️ Erro ao enviar para {recipient_email}: {error_msg}")
                        
                        except Exception as e:
                            current_app.logger.warning(f"[THREAD] ⚠️ Erro ao enviar para {recipient_email}: {type(e).__name__}: {e}")
                    
                    if enviados > 0:
                        current_app.logger.info(f"[THREAD] ✅ SUCESSO: {enviados}/{len(recipients)} emails enviados")
                
                except Exception as e:
                    current_app.logger.warning(f"[THREAD] ⚠️ Erro geral no envio: {type(e).__name__}: {e}")
            
            thread = threading.Thread(target=enviar_emails_resend, daemon=True)
            thread.start()
            
            # Retornar SUCESSO IMEDIATAMENTE (não espera a thread)
            return {'success': True, 'enviados': len(recipients), 'error': None}
        
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao iniciar envio: {e}")
            return {'success': True, 'enviados': 0, 'error': None}
