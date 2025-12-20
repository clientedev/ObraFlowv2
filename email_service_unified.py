"""
Serviço unificado de envio de emails para relatórios via Resend.
Implementação robusta que garante envio para TODOS os destinatários.
"""
import os
import json
import base64
import requests
import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


class UnifiedReportEmailService:
    """Serviço centralizado de envio de emails para relatórios"""
    
    def __init__(self):
        # API key vem das variáveis de ambiente ou fallback
        self.api_key = os.getenv('RESEND_API_KEY') or 're_Y7ESk4Tk_3oyhaqCqWTPWTVMcy8TtfVje'
        self.from_email = os.getenv('RESEND_FROM_EMAIL', 'relatorios@elpconsultoria.eng.br')
        self.resend_endpoint = "https://api.resend.com/emails"
        
        logger.info(f"📧 Serviço Unified de Email inicializado")
        logger.info(f"📮 De: {self.from_email}")
        logger.info(f"🔑 API KEY: {self.api_key[:15]}...")
    
    def _collect_all_recipients(self, relatorio):
        """
        Coleta TODOS os destinatários do relatório com logging detalhado.
        
        Retorna:
            dict com 'emails' (lista de strings) e 'por_tipo' (dict com contagem)
        """
        recipients = set()
        recipients_by_type = {
            'autor': [],
            'aprovador': [],
            'obra': [],
            'acompanhantes': []
        }
        
        try:
            tipo_relatorio = type(relatorio).__name__
            logger.info(f"\n{'='*70}")
            logger.info(f"🔍 COLETANDO DESTINATÁRIOS - {tipo_relatorio}")
            logger.info(f"{'='*70}")
            
            # 1. AUTOR DO RELATÓRIO
            try:
                autor = getattr(relatorio, 'autor', None)
                if not autor and hasattr(relatorio, 'autor_id'):
                    from models import User
                    autor = User.query.get(relatorio.autor_id)
                
                if autor and hasattr(autor, 'email') and autor.email:
                    email_clean = autor.email.strip().lower()
                    if '@' in email_clean:
                        recipients.add(email_clean)
                        recipients_by_type['autor'].append(email_clean)
                        nome = getattr(autor, 'nome_completo', None) or getattr(autor, 'username', 'Autor')
                        logger.info(f"✅ [AUTOR] {nome} → {email_clean}")
                    else:
                        logger.warning(f"⚠️ [AUTOR] Email inválido: {autor.email}")
                else:
                    logger.warning(f"⚠️ [AUTOR] Sem email - autor_id={getattr(relatorio, 'autor_id', None)}")
            except Exception as e:
                logger.warning(f"⚠️ [AUTOR] Erro: {e}")
            
            # 2. APROVADOR
            try:
                aprovador = getattr(relatorio, 'aprovador', None)
                if not aprovador and hasattr(relatorio, 'aprovador_id'):
                    from models import User
                    aprovador = User.query.get(relatorio.aprovador_id)
                
                if aprovador and hasattr(aprovador, 'email') and aprovador.email:
                    email_clean = aprovador.email.strip().lower()
                    if '@' in email_clean:
                        recipients.add(email_clean)
                        recipients_by_type['aprovador'].append(email_clean)
                        nome = getattr(aprovador, 'nome_completo', None) or getattr(aprovador, 'username', 'Aprovador')
                        logger.info(f"✅ [APROVADOR] {nome} → {email_clean}")
                    else:
                        logger.warning(f"⚠️ [APROVADOR] Email inválido: {aprovador.email}")
                else:
                    logger.warning(f"⚠️ [APROVADOR] Sem email - aprovador_id={getattr(relatorio, 'aprovador_id', None)}")
            except Exception as e:
                logger.warning(f"⚠️ [APROVADOR] Erro: {e}")
            
            # 3. CONTATO DA OBRA
            try:
                obra_email = None
                
                # Express: email direto
                if hasattr(relatorio, 'obra_email'):
                    obra_email = (getattr(relatorio, 'obra_email', '') or '').strip()
                
                # Normal: via projeto
                if not obra_email and hasattr(relatorio, 'projeto'):
                    projeto = getattr(relatorio, 'projeto', None)
                    if projeto and hasattr(projeto, 'email'):
                        obra_email = (getattr(projeto, 'email', '') or '').strip()
                
                if obra_email and '@' in obra_email:
                    email_clean = obra_email.lower()
                    recipients.add(email_clean)
                    recipients_by_type['obra'].append(email_clean)
                    logger.info(f"✅ [OBRA] {email_clean}")
                elif obra_email:
                    logger.warning(f"⚠️ [OBRA] Email inválido: {obra_email}")
                else:
                    logger.info(f"ℹ️ [OBRA] Sem email de contato")
            except Exception as e:
                logger.warning(f"⚠️ [OBRA] Erro: {e}")
            
            # 4. ACOMPANHANTES
            try:
                acompanhantes_data = getattr(relatorio, 'acompanhantes', None)
                acompanhantes_list = []
                
                if acompanhantes_data:
                    # Se for lista
                    if isinstance(acompanhantes_data, list):
                        acompanhantes_list = acompanhantes_data
                    # Se for string JSON
                    elif isinstance(acompanhantes_data, str):
                        try:
                            parsed = json.loads(acompanhantes_data)
                            if isinstance(parsed, list):
                                acompanhantes_list = parsed
                        except:
                            pass
                
                if acompanhantes_list:
                    logger.info(f"📋 Processando {len(acompanhantes_list)} acompanhantes...")
                    
                    for idx, acomp in enumerate(acompanhantes_list, 1):
                        try:
                            email = None
                            nome = None
                            
                            # Dict com email
                            if isinstance(acomp, dict):
                                email = (acomp.get('email') or '').strip()
                                nome = acomp.get('nome') or acomp.get('name', f'Acompanhante {idx}')
                            # Objeto com atributo email
                            elif hasattr(acomp, 'email'):
                                email = (getattr(acomp, 'email', '') or '').strip()
                                nome = getattr(acomp, 'nome', None) or getattr(acomp, 'name', f'Acompanhante {idx}')
                            # ID de usuário
                            elif isinstance(acomp, (int, str)):
                                try:
                                    from models import User
                                    user = User.query.get(int(acomp))
                                    if user and hasattr(user, 'email') and user.email:
                                        email = user.email.strip()
                                        nome = getattr(user, 'nome_completo', None) or getattr(user, 'username', f'Acompanhante {idx}')
                                except:
                                    pass
                            
                            if email and '@' in email:
                                email_clean = email.lower()
                                recipients.add(email_clean)
                                recipients_by_type['acompanhantes'].append(email_clean)
                                logger.info(f"✅ [ACOMP {idx}] {nome} → {email_clean}")
                            else:
                                logger.warning(f"⚠️ [ACOMP {idx}] {nome or str(acomp)[:30]} - Sem email válido")
                        
                        except Exception as e:
                            logger.warning(f"⚠️ [ACOMP {idx}] Erro ao processar: {e}")
                else:
                    logger.info(f"ℹ️ [ACOMPANHANTES] Nenhum registrado")
            except Exception as e:
                logger.warning(f"⚠️ [ACOMPANHANTES] Erro geral: {e}")
            
            # Resultado final
            resultado = {
                'emails': sorted(list(recipients)),
                'por_tipo': recipients_by_type,
                'total': len(recipients)
            }
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 RESUMO - Total: {resultado['total']} destinatários únicos")
            logger.info(f"   - Autor: {len(resultado['por_tipo']['autor'])}")
            logger.info(f"   - Aprovador: {len(resultado['por_tipo']['aprovador'])}")
            logger.info(f"   - Obra: {len(resultado['por_tipo']['obra'])}")
            logger.info(f"   - Acompanhantes: {len(resultado['por_tipo']['acompanhantes'])}")
            for email in sorted(resultado['emails']):
                logger.info(f"   • {email}")
            logger.info(f"{'='*70}\n")
            
            return resultado
        
        except Exception as e:
            logger.error(f"❌ ERRO ao coletar destinatários: {e}", exc_info=True)
            return {'emails': [], 'por_tipo': {}, 'total': 0}
    
    def _build_html_body(self, destinatario_nome, obra_nome, data_aprovacao):
        """Cria HTML do email com styling profissional"""
        if not data_aprovacao:
            data_aprovacao = datetime.now()
        
        data_str = data_aprovacao.strftime("%d/%m/%Y às %H:%M") if hasattr(data_aprovacao, 'strftime') else str(data_aprovacao)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }}
        .wrapper {{ background: #f5f5f5; padding: 20px 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .content {{ padding: 40px 20px; line-height: 1.6; color: #333; }}
        .content p {{ margin-bottom: 15px; }}
        .highlight {{ color: #667eea; font-weight: bold; }}
        .info-box {{ background: #f9f9f9; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; }}
        .footer {{ background: #f5f5f5; padding: 20px; font-size: 12px; text-align: center; color: #666; border-top: 1px solid #ddd; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="container">
            <div class="header">
                <h1>✅ Relatório Aprovado</h1>
                <p>Documentação oficial</p>
            </div>
            
            <div class="content">
                <p>Olá <span class="highlight">{destinatario_nome}</span>,</p>
                
                <p>Temos o prazer em informar que o relatório da obra <span class="highlight">{obra_nome}</span> foi <strong>aprovado com sucesso</strong>!</p>
                
                <div class="info-box">
                    <strong>Data de aprovação:</strong><br/>
                    {data_str}
                </div>
                
                <p>O documento em PDF está anexado a este email e contém todas as informações completas sobre o relatório aprovado.</p>
                
                <p>Em caso de dúvidas ou necessidade de esclarecimentos, favor entrar em contato conosco.</p>
                
                <p style="margin-top: 30px;">Atenciosamente,<br/>
                <strong>ELP Consultoria Engenharia</strong></p>
            </div>
            
            <div class="footer">
                <p>Este é um email automático. Por favor, não responda este mensagem.</p>
                <p>© 2025 ELP Consultoria. Todos os direitos reservados.</p>
            </div>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def send_approval_email(self, relatorio, pdf_path):
        """
        Envia email de aprovação de forma SÍNCRONA para TODOS os destinatários.
        
        Retorna:
            dict com 'success', 'enviados', 'total', 'erros'
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"📧 INICIANDO ENVIO DE EMAIL")
            logger.info(f"{'='*70}")
            logger.info(f"Relatório: {getattr(relatorio, 'numero', 'N/A')}")
            logger.info(f"Tipo: {type(relatorio).__name__}")
            logger.info(f"PDF: {pdf_path}")
            
            # Coletar destinatários
            recipients_data = self._collect_all_recipients(relatorio)
            recipients = recipients_data['emails']
            
            if not recipients:
                logger.warning(f"⚠️ Nenhum destinatário encontrado para {getattr(relatorio, 'numero', 'relatório')}")
                return {'success': True, 'enviados': 0, 'total': 0, 'erros': []}
            
            # Obter nome da obra
            obra_nome = "Obra"
            if hasattr(relatorio, 'obra_nome'):
                obra_nome = relatorio.obra_nome or "Obra"
            elif hasattr(relatorio, 'projeto') and relatorio.projeto:
                obra_nome = relatorio.projeto.nome or "Obra"
            
            # Validar PDF
            if not os.path.exists(pdf_path):
                logger.error(f"❌ PDF não encontrado: {pdf_path}")
                return {'success': False, 'enviados': 0, 'total': len(recipients), 'erros': ['PDF não encontrado']}
            
            # Ler PDF
            try:
                with open(pdf_path, 'rb') as f:
                    pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
                logger.info(f"✅ PDF lido com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao ler PDF: {e}")
                return {'success': False, 'enviados': 0, 'total': len(recipients), 'erros': [f'Erro ao ler PDF: {e}']}
            
            # Preparar assunto
            assunto = f"✅ Relatório Aprovado – {obra_nome}"
            
            # Enviar para cada destinatário
            enviados = 0
            erros = []
            
            for recipient_email in recipients:
                try:
                    # Obter nome do destinatário
                    destinatario_nome = recipient_email.split('@')[0].title()
                    try:
                        from models import User
                        user = User.query.filter_by(email=recipient_email).first()
                        if user and hasattr(user, 'nome_completo') and user.nome_completo:
                            destinatario_nome = user.nome_completo
                    except:
                        pass
                    
                    # Montar HTML do corpo
                    corpo_html = self._build_html_body(destinatario_nome, obra_nome, getattr(relatorio, 'data_aprovacao', None))
                    
                    # Preparar payload
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
                    
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    logger.info(f"📤 Enviando para {recipient_email}...")
                    
                    # POST para Resend
                    response = requests.post(
                        self.resend_endpoint,
                        json=payload,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        email_id = response_data.get('id', 'N/A')
                        enviados += 1
                        logger.info(f"✅ Email enviado para {recipient_email} (ID: {email_id})")
                    else:
                        erro = f"HTTP {response.status_code}: {response.text[:100]}"
                        erros.append(f"{recipient_email}: {erro}")
                        logger.error(f"❌ Erro ao enviar para {recipient_email}: {erro}")
                
                except Exception as e:
                    erro = f"{type(e).__name__}: {str(e)}"
                    erros.append(f"{recipient_email}: {erro}")
                    logger.error(f"❌ Exceção ao enviar para {recipient_email}: {erro}", exc_info=True)
            
            # Resultado final
            resultado = {
                'success': enviados > 0,
                'enviados': enviados,
                'total': len(recipients),
                'erros': erros
            }
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 RESULTADO FINAL")
            logger.info(f"{'='*70}")
            logger.info(f"✅ Enviados: {resultado['enviados']}/{resultado['total']}")
            if erros:
                logger.info(f"❌ Erros ({len(erros)}):")
                for erro in erros:
                    logger.info(f"   - {erro}")
            logger.info(f"{'='*70}\n")
            
            return resultado
        
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO ao enviar emails: {e}", exc_info=True)
            return {'success': False, 'enviados': 0, 'total': 0, 'erros': [str(e)]}


# Singleton global
_email_service = None

def get_email_service():
    global _email_service
    if _email_service is None:
        _email_service = UnifiedReportEmailService()
    return _email_service
