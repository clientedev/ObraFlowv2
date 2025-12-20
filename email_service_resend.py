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
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('RESEND_FROM_EMAIL', 'relatorios@elpconsultoria.eng.br')
        self.resend_endpoint = "https://api.resend.com/emails"
        
        current_app.logger.info(f"📧 Resend Service inicializado com: {self.from_email}")
    
    def _get_recipients_for_report(self, relatorio):
        """
        Coleta TODOS os destinatários relacionados ao relatório.
        Retorna lista de emails únicos com logs detalhados.
        
        Destinatários OBRIGATÓRIOS:
        - Pessoa que criou o relatório (autor) ✅
        - Aprovador global ✅
        - Contato de email da obra ✅
        - Todos os acompanhantes da visita vinculados ao relatório ✅
        """
        recipients = set()
        
        try:
            current_app.logger.info(f"🔍 Coletando destinatários para relatório {relatorio.numero}")
            relatorio_type = type(relatorio).__name__
            current_app.logger.info(f"📋 Tipo de relatório: {relatorio_type}")
            
            # ===== 1. AUTOR DO RELATÓRIO (OBRIGATÓRIO) =====
            try:
                # Forçar carregamento da relação
                autor = relatorio.autor
                if not autor:
                    from models import User
                    if hasattr(relatorio, 'autor_id') and relatorio.autor_id:
                        autor = User.query.get(relatorio.autor_id)
                
                if autor and autor.email:
                    recipients.add(autor.email)
                    current_app.logger.info(f"✅ [AUTOR] {autor.nome_completo or autor.username} ({autor.email})")
                else:
                    current_app.logger.warning(f"⚠️ [AUTOR] Sem email encontrado para autor_id={relatorio.autor_id}")
            except Exception as autor_err:
                current_app.logger.warning(f"⚠️ [AUTOR] Erro ao processar: {autor_err}")
            
            # ===== 2. APROVADOR GLOBAL (OBRIGATÓRIO) =====
            try:
                # Forçar carregamento da relação
                aprovador = relatorio.aprovador
                if not aprovador:
                    from models import User
                    if hasattr(relatorio, 'aprovador_id') and relatorio.aprovador_id:
                        aprovador = User.query.get(relatorio.aprovador_id)
                
                if aprovador and aprovador.email:
                    recipients.add(aprovador.email)
                    current_app.logger.info(f"✅ [APROVADOR] {aprovador.nome_completo or aprovador.username} ({aprovador.email})")
                else:
                    current_app.logger.warning(f"⚠️ [APROVADOR] Sem email para aprovador_id={relatorio.aprovador_id}")
            except Exception as apr_err:
                current_app.logger.warning(f"⚠️ [APROVADOR] Erro ao processar: {apr_err}")
            
            # ===== 3. CONTATO DE EMAIL DA OBRA (OBRIGATÓRIO) =====
            try:
                obra_email = None
                
                # Para RelatorioExpress - email direto
                if hasattr(relatorio, 'obra_email'):
                    obra_email = (relatorio.obra_email or '').strip()
                    if obra_email:
                        current_app.logger.info(f"📧 [OBRA EXPRESS] Email direto encontrado: {obra_email}")
                
                # Para Relatório Normal - via projeto
                if not obra_email and hasattr(relatorio, 'projeto') and relatorio.projeto:
                    projeto = relatorio.projeto
                    if hasattr(projeto, 'email') and projeto.email:
                        obra_email = (projeto.email or '').strip()
                        current_app.logger.info(f"📧 [OBRA PROJETO] Email via projeto: {obra_email}")
                
                if obra_email:
                    recipients.add(obra_email)
                    current_app.logger.info(f"✅ [OBRA] Contato registrado: {obra_email}")
                else:
                    current_app.logger.warning(f"⚠️ [OBRA] Sem email de contato registrado")
            except Exception as obra_err:
                current_app.logger.warning(f"⚠️ [OBRA] Erro ao processar: {obra_err}")
            
            # ===== 4. ACOMPANHANTES DA VISITA (TODOS!) =====
            try:
                acompanhantes_data = relatorio.acompanhantes
                current_app.logger.info(f"🔍 Processando acompanhantes - Tipo: {type(acompanhantes_data)}, Valor: {acompanhantes_data}")
                
                acompanhantes_list = []
                
                if acompanhantes_data:
                    # Se for lista
                    if isinstance(acompanhantes_data, list):
                        acompanhantes_list = acompanhantes_data
                        current_app.logger.info(f"✅ Acompanhantes já é lista: {len(acompanhantes_list)} itens")
                    # Se for string JSON
                    elif isinstance(acompanhantes_data, str):
                        try:
                            parsed = json.loads(acompanhantes_data)
                            if isinstance(parsed, list):
                                acompanhantes_list = parsed
                                current_app.logger.info(f"✅ Acompanhantes parseado de JSON: {len(acompanhantes_list)} itens")
                            else:
                                current_app.logger.warning(f"⚠️ JSON parseado não é lista: {type(parsed)}")
                        except json.JSONDecodeError as je:
                            current_app.logger.warning(f"⚠️ Falha ao parsear JSON: {je}")
                    else:
                        current_app.logger.warning(f"⚠️ Tipo inesperado de acompanhantes: {type(acompanhantes_data)}")
                
                if acompanhantes_list:
                    current_app.logger.info(f"📋 Total de acompanhantes para processar: {len(acompanhantes_list)}")
                    
                    from models import VisitaAcompanhante
                    acompanhantes_email_count = 0
                    
                    for idx, acompanhante_id in enumerate(acompanhantes_list, 1):
                        try:
                            acompanhante = VisitaAcompanhante.query.get(acompanhante_id)
                            
                            if not acompanhante:
                                current_app.logger.warning(f"⚠️ [ACOMP {idx}] VisitaAcompanhante ID {acompanhante_id} não encontrado")
                                continue
                            
                            email = (acompanhante.email or '').strip() if hasattr(acompanhante, 'email') else ''
                            
                            if email and '@' in email:
                                recipients.add(email)
                                acompanhantes_email_count += 1
                                current_app.logger.info(f"✅ [ACOMP {idx}] {acompanhante.nome or f'ID {acompanhante_id}'} → {email}")
                            else:
                                current_app.logger.warning(f"⚠️ [ACOMP {idx}] {acompanhante.nome or f'ID {acompanhante_id}'} - Sem email válido")
                        
                        except Exception as acomp_err:
                            current_app.logger.warning(f"⚠️ [ACOMP {idx}] ID {acompanhante_id} - Erro: {acomp_err}")
                    
                    current_app.logger.info(f"📊 Acompanhantes com email: {acompanhantes_email_count}/{len(acompanhantes_list)}")
                else:
                    current_app.logger.info(f"ℹ️ [ACOMPANHANTES] Nenhum acompanhante registrado")
            
            except Exception as acomp_general_err:
                current_app.logger.warning(f"⚠️ [ACOMPANHANTES] Erro geral: {acomp_general_err}", exc_info=True)
            
            # ===== LIMPEZA E RESULTADO FINAL =====
            # Filtrar emails válidos
            recipients = set(email.strip().lower() for email in recipients if email and '@' in email)
            
            current_app.logger.info(f"\n{'='*60}")
            current_app.logger.info(f"📨 RESUMO FINAL DE DESTINATÁRIOS")
            current_app.logger.info(f"{'='*60}")
            current_app.logger.info(f"✅ Total de destinatários únicos: {len(recipients)}")
            for idx, email in enumerate(sorted(recipients), 1):
                current_app.logger.info(f"  {idx}. {email}")
            current_app.logger.info(f"{'='*60}\n")
            
            return list(recipients)
        
        except Exception as e:
            current_app.logger.error(f"❌ ERRO CRÍTICO ao coletar destinatários: {e}", exc_info=True)
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
