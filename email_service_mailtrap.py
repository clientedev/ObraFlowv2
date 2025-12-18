"""
Serviço de envio de e-mail via API Mailtrap para relatórios aprovados.
Envia e-mails para todos os envolvidos quando um relatório é aprovado.
"""
import os
import requests
import base64
from datetime import datetime
from flask import current_app


class ReportApprovalEmailService:
    """Serviço de envio de e-mails via API Mailtrap"""
    
    def __init__(self):
        self.api_token = "3a14951232f792c2c8117e3f05dae09a"
        self.api_url = "https://send.api.mailtrap.io/api/send"
        self.from_email = "relatorios@elpconsultoria.eng.br"
        self.from_name = "ELP Consultoria - Relatórios"
    
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
    
    def _encode_file_to_base64(self, pdf_path):
        """Converte arquivo PDF para base64"""
        try:
            with open(pdf_path, 'rb') as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao codificar PDF: {e}")
            return None
    
    def send_approval_email(self, relatorio, pdf_path):
        """
        Envia e-mail de aprovação para todos os envolvidos via API Mailtrap.
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
            
            # Codificar PDF para base64
            pdf_base64 = self._encode_file_to_base64(pdf_path)
            if not pdf_base64:
                return {
                    'success': False,
                    'enviados': 0,
                    'error': 'Erro ao processar arquivo PDF'
                }
            
            pdf_filename = os.path.basename(pdf_path)
            
            enviados = 0
            
            # Enviar e-mail para cada destinatário via API Mailtrap
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
                    
                    # Preparar payload para API Mailtrap
                    payload = {
                        "from": {
                            "email": self.from_email,
                            "name": self.from_name
                        },
                        "to": [
                            {
                                "email": recipient_email
                            }
                        ],
                        "subject": assunto,
                        "text": corpo,
                        "attachments": [
                            {
                                "filename": pdf_filename,
                                "type": "application/pdf",
                                "content": pdf_base64
                            }
                        ],
                        "category": "report-approval"
                    }
                    
                    # Fazer requisição para API Mailtrap
                    headers = {
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    }
                    
                    response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        enviados += 1
                        current_app.logger.info(f"✅ E-mail enviado para {recipient_email} via Mailtrap")
                    else:
                        current_app.logger.error(f"❌ Erro ao enviar via Mailtrap para {recipient_email}: {response.status_code} - {response.text}")
                
                except requests.exceptions.RequestException as e:
                    current_app.logger.error(f"❌ Erro de requisição ao enviar para {recipient_email}: {e}")
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
