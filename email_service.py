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
    
    def configure_smtp(self, config, user_config=None):
        """Configurar SMTP baseado na configuração do sistema ou usuário"""
        if user_config:
            # Usar configuração específica do usuário
            current_app.config['MAIL_SERVER'] = user_config.smtp_server
            current_app.config['MAIL_PORT'] = user_config.smtp_port
            current_app.config['MAIL_USE_TLS'] = user_config.use_tls
            current_app.config['MAIL_USE_SSL'] = user_config.use_ssl
            current_app.config['MAIL_USERNAME'] = user_config.email_address
            current_app.config['MAIL_PASSWORD'] = user_config.get_password()
            current_app.config['MAIL_DEFAULT_SENDER'] = user_config.email_address
        else:
            # Usar configuração do sistema (fallback)
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
    
    def get_user_email_config(self, user_id):
        """Buscar configuração de email específica do usuário"""
        from models import UserEmailConfig
        return UserEmailConfig.query.filter_by(user_id=user_id, is_active=True).first()
    
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
            # Buscar configuração específica do usuário primeiro
            user_config = self.get_user_email_config(usuario_id)
            
            # Se não houver configuração do usuário, usar configuração do sistema
            system_config = None
            if not user_config:
                system_config = self.get_configuracao_ativa()
                if not system_config:
                    raise Exception("Nenhuma configuração de e-mail encontrada (nem do usuário nem do sistema)")
            
            # Configurar SMTP (prioridade: usuário > sistema)
            self.configure_smtp(system_config, user_config)
            
            # Determinar qual configuração está sendo usada para logging
            config_usado = user_config if user_config else system_config
            email_remetente = user_config.email_address if user_config else system_config.email_remetente
            
            # Preparar dados do e-mail
            projeto = relatorio.projeto
            # Obter data da visita: se houver visita associada, usar data_inicio da visita, senão usar data_relatorio
            if relatorio.visita and relatorio.visita.data_inicio:
                data_visita = relatorio.visita.data_inicio.strftime('%d/%m/%Y')
            elif relatorio.data_relatorio:
                data_visita = relatorio.data_relatorio.strftime('%d/%m/%Y')
            else:
                data_visita = 'N/A'
            data_atual = datetime.now().strftime('%d/%m/%Y')
            
            # Gerar assunto (usar templates do sistema se disponível)
            if destinatarios_data.get('assunto_custom'):
                assunto = destinatarios_data['assunto_custom']
            elif system_config and system_config.template_assunto:
                assunto = system_config.template_assunto.format(
                    projeto_nome=projeto.nome,
                    data=data_atual
                )
            else:
                assunto = f"Relatório de Visita - {projeto.nome} - {data_atual}"
            
            # Gerar corpo do e-mail (usar templates do sistema se disponível)
            if destinatarios_data.get('corpo_custom'):
                corpo_base = destinatarios_data['corpo_custom']
            elif system_config and system_config.template_corpo:
                corpo_base = system_config.template_corpo
            else:
                corpo_base = """
                <p>Olá {nome_cliente},</p>
                <p>Segue anexo o relatório de visita do projeto {projeto_nome} realizada em {data_visita}.</p>
                <p>Atenciosamente,<br>Equipe ELP Consultoria</p>
                """
            
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
                    
                    # Implementar CC automático conforme Item 34
                    cc_emails = destinatarios_data.get('cc', []).copy()
                    
                    # Auto-CC: Sempre adicionar o outro usuário envolvido (preenchedor ou aprovador)
                    relatorio_autor_email = relatorio.autor.email if relatorio.autor else None
                    aprovador_email = None
                    
                    # Buscar e-mail do aprovador se relatório foi aprovado
                    if hasattr(relatorio, 'aprovador') and relatorio.aprovador:
                        aprovador_email = relatorio.aprovador.email
                    elif hasattr(relatorio, 'aprovado_por') and relatorio.aprovado_por:
                        from models import User
                        aprovador = User.query.get(relatorio.aprovado_por)
                        if aprovador:
                            aprovador_email = aprovador.email
                    
                    # Auto-CC: Se usuário atual é o preenchedor, adicionar aprovador na cópia
                    # Se usuário atual é o aprovador, adicionar preenchedor na cópia
                    user_email = user_config.email_address if user_config else email_remetente
                    
                    if relatorio_autor_email and relatorio_autor_email != user_email and relatorio_autor_email not in cc_emails:
                        cc_emails.append(relatorio_autor_email)
                        
                    if aprovador_email and aprovador_email != user_email and aprovador_email not in cc_emails:
                        cc_emails.append(aprovador_email)
                    
                    # Se usando configuração pessoal, garantir que a conta pessoal está no CC
                    if user_config and user_config.email_address not in cc_emails:
                        cc_emails.append(user_config.email_address)
                    
                    # CC Centralizada (Luciana): Adicionar e-mail admin do sistema se configurado
                    admin_cc_email = os.environ.get('ADMIN_CC_EMAIL')
                    if admin_cc_email and admin_cc_email not in cc_emails:
                        cc_emails.append(admin_cc_email)
                    elif system_config and hasattr(system_config, 'cc_admin') and system_config.cc_admin and system_config.cc_admin not in cc_emails:
                        cc_emails.append(system_config.cc_admin)
                    
                    # Criar mensagem
                    msg = Message(
                        subject=assunto,
                        recipients=[email_dest],
                        cc=cc_emails,
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
                    
                    # Log de sucesso com informação da conta usada
                    log_envio = LogEnvioEmail(
                        projeto_id=projeto.id,
                        relatorio_id=relatorio.id,
                        usuario_id=usuario_id,
                        destinatarios=json.dumps([email_dest]),
                        cc=json.dumps(cc_emails),
                        bcc=json.dumps(destinatarios_data.get('bcc', [])),
                        assunto=assunto,
                        status='enviado'
                    )
                    # Adicionar informação da conta utilizada para envio nos logs
                    log_envio.erro_detalhes = f"Enviado via: {email_remetente} ({'Conta pessoal' if user_config else 'Conta sistema'})"
                    logs_envio.append(log_envio)
                    
                    # Limpar arquivo PDF temporário
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            os.remove(pdf_path)
                        except:
                            pass
                    
                except Exception as e:
                    # Para erros, usar CC original pois cc_emails pode não estar definido
                    cc_fallback = destinatarios_data.get('cc', [])
                    
                    # Log de erro com informação da conta usada
                    log_envio = LogEnvioEmail(
                        projeto_id=projeto.id,
                        relatorio_id=relatorio.id,
                        usuario_id=usuario_id,
                        destinatarios=json.dumps([email_dest]),
                        cc=json.dumps(cc_fallback),
                        bcc=json.dumps(destinatarios_data.get('bcc', [])),
                        assunto=assunto,
                        status='falhou',
                        erro_detalhes=f"Erro: {str(e)} | Tentativa via: {email_remetente} ({'Conta pessoal' if user_config else 'Conta sistema'})"
                    )
                    logs_envio.append(log_envio)
            
            # Salvar todos os logs em nova transação
            try:
                for log in logs_envio:
                    db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar logs de envio: {str(log_error)}")
            
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
            # Fazer rollback de qualquer transação pendente
            try:
                db.session.rollback()
            except:
                pass
            
            # Log geral de erro em nova transação
            try:
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
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar log de erro: {str(log_error)}")
                log_envio = None
            
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

    def enviar_notificacao_rejeicao(self, relatorio, motivo_rejeicao, aprovador, usuario_id):
        """
        Enviar notificação por e-mail ao autor sobre rejeição do relatório
        
        Args:
            relatorio: Objeto Relatorio rejeitado
            motivo_rejeicao: String com o motivo da rejeição
            aprovador: Objeto User que aprovou/rejeitou
            usuario_id: ID do usuário que está enviando (aprovador)
        """
        try:
            # Buscar configuração específica do usuário primeiro
            user_config = self.get_user_email_config(usuario_id)
            
            # Se não houver configuração do usuário, usar configuração do sistema
            system_config = None
            if not user_config:
                system_config = self.get_configuracao_ativa()
                if not system_config:
                    raise Exception("Nenhuma configuração de e-mail encontrada (nem do usuário nem do sistema)")
            
            # Configurar SMTP (prioridade: usuário > sistema)
            self.configure_smtp(system_config, user_config)
            
            # Determinar qual configuração está sendo usada para logging
            email_remetente = user_config.email_address if user_config else system_config.email_remetente
            
            # Dados do relatório e projeto
            projeto = relatorio.projeto
            autor = relatorio.autor
            data_rejeicao = datetime.now().strftime('%d/%m/%Y às %H:%M')
            
            # Assunto personalizado para rejeição
            assunto = f"Relatório {relatorio.numero} Rejeitado - {projeto.nome}"
            
            # Corpo do e-mail personalizado para rejeição
            corpo = f"""
            <p>Olá {autor.nome_completo},</p>
            
            <p>Seu relatório <strong>{relatorio.numero}</strong> do projeto <strong>{projeto.nome}</strong> foi rejeitado em {data_rejeicao}.</p>
            
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 15px; margin: 15px 0;">
                <h4 style="color: #721c24; margin-top: 0;">Motivo da Rejeição:</h4>
                <p style="color: #721c24; margin-bottom: 0;">{motivo_rejeicao}</p>
            </div>
            
            <p>Por favor, faça as correções solicitadas e reenvie o relatório para aprovação.</p>
            
            <p><strong>Próximos passos:</strong></p>
            <ol>
                <li>Acesse o sistema e abra o relatório rejeitado</li>
                <li>Clique em "Editar e Corrigir"</li>
                <li>Faça as correções solicitadas</li>
                <li>Reenvie para aprovação</li>
            </ol>
            
            <p>Rejeitado por: <strong>{aprovador.nome_completo}</strong></p>
            
            <p>Em caso de dúvidas, entre em contato conosco.</p>
            
            <p>Atenciosamente,<br>
            Equipe ELP Consultoria</p>
            """
            
            # Preparar e-mail
            from flask_mail import Message
            msg = Message(
                subject=assunto,
                recipients=[autor.email],
                html=corpo,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            # Enviar e-mail
            self.mail.send(msg)
            
            # Log do envio em nova transação
            from models import LogEnvioEmail
            import json
            try:
                log = LogEnvioEmail(
                    projeto_id=relatorio.projeto_id,
                    relatorio_id=relatorio.id,
                    usuario_id=usuario_id,
                    destinatarios=json.dumps([autor.email]),
                    cc=json.dumps([]),
                    bcc=json.dumps([]),
                    assunto=assunto,
                    status='enviado',
                    data_envio=datetime.utcnow()
                )
                
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar log de notificação de rejeição: {str(log_error)}")
            
            current_app.logger.info(f"Notificação de rejeição enviada para {autor.email} - Relatório {relatorio.numero}")
            return {'success': True, 'message': f'Notificação de rejeição enviada para {autor.nome_completo}'}
            
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de rejeição: {str(e)}")
            
            # Fazer rollback de transação pendente
            try:
                db.session.rollback()
            except:
                pass
            
            # Log do erro em nova transação
            try:
                from models import LogEnvioEmail
                import json
                log = LogEnvioEmail(
                    projeto_id=relatorio.projeto_id,
                    relatorio_id=relatorio.id,
                    usuario_id=usuario_id,
                    destinatarios=json.dumps([autor.email]),
                    cc=json.dumps([]),
                    bcc=json.dumps([]),
                    assunto=f"Relatório {relatorio.numero} Rejeitado - {projeto.nome}",
                    status='falhou',
                    erro_detalhes=str(e),
                    data_envio=datetime.utcnow()
                )
                
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar log de erro: {str(log_error)}")
                
            return {'success': False, 'error': str(e)}

    def send_report_approval_email(self, relatorio_id):
        """
        Enviar e-mail de aprovação para todos os envolvidos no relatório
        Conforme especificação: autor, responsável, funcionários e acompanhantes
        
        Args:
            relatorio_id: ID do relatório aprovado
        
        Returns:
            dict: {'success': bool, 'enviados': int, 'falhas': int, 'message': str}
        """
        try:
            # Importar modelos necessários
            from models import Relatorio, Projeto, User, FuncionarioProjeto
            
            # Buscar relatório
            relatorio = Relatorio.query.get(relatorio_id)
            if not relatorio:
                current_app.logger.error(f"❌ Relatório {relatorio_id} não encontrado")
                return {'success': False, 'error': 'Relatório não encontrado'}
            
            projeto = relatorio.projeto
            if not projeto:
                current_app.logger.error(f"❌ Projeto não encontrado para relatório {relatorio_id}")
                return {'success': False, 'error': 'Projeto não encontrado'}
            
            # Configuração SMTP segura via variáveis de ambiente
            SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
            SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
            SMTP_USER = os.environ.get('SMTP_USER', os.environ.get('MAIL_USERNAME', ''))
            SMTP_PASS = os.environ.get('SMTP_PASS', os.environ.get('MAIL_PASSWORD', ''))
            
            if not SMTP_USER or not SMTP_PASS:
                current_app.logger.error("❌ Credenciais SMTP não configuradas")
                return {'success': False, 'error': 'Configuração de e-mail não disponível'}
            
            # Coletar todos os destinatários sem duplicação
            destinatarios = set()
            
            # 1. Autor do relatório
            if relatorio.autor and relatorio.autor.email:
                destinatarios.add(relatorio.autor.email)
                current_app.logger.info(f"📧 Adicionando autor: {relatorio.autor.email}")
            
            # 2. Responsável pela obra (via projeto)
            if projeto.responsavel_id:
                responsavel = db.session.get(User, projeto.responsavel_id)
                if responsavel and responsavel.email:
                    destinatarios.add(responsavel.email)
                    current_app.logger.info(f"📧 Adicionando responsável: {responsavel.email}")
            
            # 3. Funcionários da obra
            funcionarios = FuncionarioProjeto.query.filter_by(
                projeto_id=projeto.id,
                ativo=True
            ).all()
            
            for func in funcionarios:
                # Funcionários podem ter user_id (usuários do sistema) ou apenas dados cadastrais
                if func.user_id:
                    user = db.session.get(User, func.user_id)
                    if user and user.email:
                        destinatarios.add(user.email)
                        current_app.logger.info(f"📧 Adicionando funcionário (user): {user.email}")
                # Também verificar se o funcionário tem e-mail cadastrado diretamente no modelo
                # Nota: O modelo FuncionarioProjeto atual não tem campo email, mas mantemos para futura compatibilidade
                elif hasattr(func, 'email') and func.email:
                    destinatarios.add(func.email)
                    current_app.logger.info(f"📧 Adicionando funcionário (cadastral): {func.email}")
            
            # 4. Acompanhantes da visita (stored in JSONB field)
            if relatorio.acompanhantes:
                try:
                    # acompanhantes é um campo JSONB que pode conter lista de objetos
                    acompanhantes_list = relatorio.acompanhantes if isinstance(relatorio.acompanhantes, list) else []
                    for acomp in acompanhantes_list:
                        if isinstance(acomp, dict) and acomp.get('email'):
                            destinatarios.add(acomp['email'])
                            current_app.logger.info(f"📧 Adicionando acompanhante: {acomp['email']}")
                except Exception as e:
                    current_app.logger.warning(f"⚠️ Erro ao processar acompanhantes: {e}")
            
            if not destinatarios:
                current_app.logger.warning(f"⚠️ Nenhum destinatário encontrado para relatório {relatorio.numero}")
                return {'success': False, 'error': 'Nenhum destinatário encontrado'}
            
            current_app.logger.info(f"📬 Total de destinatários únicos: {len(destinatarios)}")
            
            # Gerar PDF do relatório
            from pdf_generator_weasy import gerar_pdf_relatorio_weasy
            pdf_path = gerar_pdf_relatorio_weasy(relatorio_id)
            
            if not pdf_path or not os.path.exists(pdf_path):
                current_app.logger.error(f"❌ PDF não encontrado: {pdf_path}")
                return {'success': False, 'error': 'PDF do relatório não disponível'}
            
            current_app.logger.info(f"📄 PDF gerado: {pdf_path}")
            
            # Preparar e-mail
            from email.message import EmailMessage
            import smtplib
            
            assunto = f"RELATORIO-{relatorio.numero}"
            email_responsavel = relatorio.autor.email if relatorio.autor else SMTP_USER
            
            # Contadores de envio
            enviados = 0
            falhas = 0
            
            # Enviar para cada destinatário
            for email_dest in destinatarios:
                try:
                    msg = EmailMessage()
                    msg["From"] = SMTP_USER
                    msg["To"] = email_dest
                    msg["Subject"] = assunto
                    
                    # Corpo do e-mail (texto simples)
                    corpo_texto = f"{email_dest}, este é o relatório da obra \"{projeto.nome}\".\nQualquer dúvida, entre em contato com {email_responsavel}."
                    msg.set_content(corpo_texto)
                    
                    # Corpo HTML
                    corpo_html = f"""
                    <html>
                      <body>
                        <p><strong>{email_dest}</strong>, este é o relatório da obra <b>{projeto.nome}</b>.</p>
                        <p>Qualquer dúvida, entre em contato com <a href="mailto:{email_responsavel}">{email_responsavel}</a>.</p>
                      </body>
                    </html>
                    """
                    msg.add_alternative(corpo_html, subtype='html')
                    
                    # Anexar PDF
                    with open(pdf_path, "rb") as f:
                        pdf_data = f.read()
                        msg.add_attachment(
                            pdf_data,
                            maintype="application",
                            subtype="pdf",
                            filename=f"RELATORIO-{relatorio.numero}.pdf"
                        )
                    
                    # Enviar e-mail
                    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
                        smtp.starttls()
                        smtp.login(SMTP_USER, SMTP_PASS)
                        smtp.send_message(msg)
                    
                    enviados += 1
                    current_app.logger.info(f"✅ E-mail enviado para {email_dest}")
                    
                except Exception as e:
                    falhas += 1
                    current_app.logger.error(f"❌ Erro ao enviar e-mail para {email_dest}: {str(e)}")
            
            # Limpar arquivo PDF temporário
            try:
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    current_app.logger.info(f"🗑️ PDF temporário removido: {pdf_path}")
            except Exception as e:
                current_app.logger.warning(f"⚠️ Erro ao remover PDF temporário: {e}")
            
            # Resultado final
            current_app.logger.info(f"📊 Envio concluído: {enviados} enviados, {falhas} falhas")
            
            return {
                'success': enviados > 0,
                'enviados': enviados,
                'falhas': falhas,
                'total': len(destinatarios),
                'message': f'{enviados} e-mail(s) enviado(s) com sucesso'
            }
            
        except Exception as e:
            current_app.logger.exception(f"❌ Erro crítico ao enviar e-mails de aprovação: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'enviados': 0,
                'falhas': 0
            }
    
    def enviar_notificacao_enviado_para_aprovacao(self, relatorio, aprovador, autor, usuario_id):
        """
        Enviar notificação por e-mail ao aprovador quando relatório é enviado para aprovação
        
        Args:
            relatorio: Objeto Relatorio enviado para aprovação
            aprovador: Objeto User que deve aprovar
            autor: Objeto User que enviou o relatório
            usuario_id: ID do usuário que está enviando (autor)
        """
        try:
            user_config = self.get_user_email_config(usuario_id)
            
            system_config = None
            if not user_config:
                system_config = self.get_configuracao_ativa()
                if not system_config:
                    raise Exception("Nenhuma configuração de e-mail encontrada (nem do usuário nem do sistema)")
            
            self.configure_smtp(system_config, user_config)
            
            email_remetente = user_config.email_address if user_config else system_config.email_remetente
            
            projeto = relatorio.projeto
            data_envio = datetime.now().strftime('%d/%m/%Y às %H:%M')
            
            # Gerar link direto para o relatório
            link_relatorio = f"{current_app.config.get('BASE_URL', '')}/reports/{relatorio.id}/review"
            
            assunto = f"Relatório {relatorio.numero} enviado para aprovação"
            
            corpo = f"""
            <p>Olá {aprovador.nome_completo},</p>
            
            <p>O relatório <strong>{relatorio.numero}</strong> referente à obra <strong>{projeto.nome}</strong> foi enviado para aprovação por <strong>{autor.nome_completo}</strong> em {data_envio}.</p>
            
            <p>Clique abaixo para acessar o relatório:</p>
            <p><a href="{link_relatorio}" style="display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Visualizar e Aprovar Relatório</a></p>
            
            <p>Ou copie o link: <a href="{link_relatorio}">{link_relatorio}</a></p>
            
            <p>Atenciosamente,<br>
            Sistema ELP Consultoria</p>
            """
            
            from flask_mail import Message
            msg = Message(
                subject=assunto,
                recipients=[aprovador.email],
                html=corpo,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            self.mail.send(msg)
            
            # Log do envio em nova transação
            from models import LogEnvioEmail
            import json
            try:
                log = LogEnvioEmail(
                    projeto_id=relatorio.projeto_id,
                    relatorio_id=relatorio.id,
                    usuario_id=usuario_id,
                    destinatarios=json.dumps([aprovador.email]),
                    cc=json.dumps([]),
                    bcc=json.dumps([]),
                    assunto=assunto,
                    status='enviado',
                    data_envio=datetime.utcnow()
                )
                
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar log de notificação: {str(log_error)}")
            
            current_app.logger.info(f"Notificação de envio para aprovação enviada para {aprovador.email} - Relatório {relatorio.numero}")
            return {'success': True, 'message': f'Notificação enviada para {aprovador.nome_completo}'}
            
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de envio para aprovação: {str(e)}")
            
            # Fazer rollback de transação pendente
            try:
                db.session.rollback()
            except:
                pass
            
            # Log do erro em nova transação
            try:
                from models import LogEnvioEmail
                import json
                log = LogEnvioEmail(
                    projeto_id=relatorio.projeto_id,
                    relatorio_id=relatorio.id,
                    usuario_id=usuario_id,
                    destinatarios=json.dumps([aprovador.email]),
                    cc=json.dumps([]),
                    bcc=json.dumps([]),
                    assunto=f"Relatório {relatorio.numero} enviado para aprovação",
                    status='falhou',
                    erro_detalhes=str(e),
                    data_envio=datetime.utcnow()
                )
                
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar log de erro: {str(log_error)}")
                
            return {'success': False, 'error': str(e)}

    def enviar_notificacao_aprovacao(self, relatorio, autor, aprovador, usuario_id):
        """
        Enviar notificação por e-mail ao autor quando relatório é aprovado
        
        Args:
            relatorio: Objeto Relatorio aprovado
            autor: Objeto User que criou o relatório
            aprovador: Objeto User que aprovou
            usuario_id: ID do usuário que está enviando (aprovador)
        """
        try:
            user_config = self.get_user_email_config(usuario_id)
            
            system_config = None
            if not user_config:
                system_config = self.get_configuracao_ativa()
                if not system_config:
                    raise Exception("Nenhuma configuração de e-mail encontrada (nem do usuário nem do sistema)")
            
            self.configure_smtp(system_config, user_config)
            
            email_remetente = user_config.email_address if user_config else system_config.email_remetente
            
            projeto = relatorio.projeto
            data_aprovacao = datetime.now().strftime('%d/%m/%Y às %H:%M')
            
            # Gerar link direto para o relatório
            link_relatorio = f"{current_app.config.get('BASE_URL', '')}/reports/{relatorio.id}/review"
            
            assunto = f"Relatório {relatorio.numero} aprovado"
            
            corpo = f"""
            <p>Olá {autor.nome_completo},</p>
            
            <p>O relatório <strong>{relatorio.numero}</strong> referente à obra <strong>{projeto.nome}</strong> foi aprovado por <strong>{aprovador.nome_completo}</strong> em {data_aprovacao}.</p>
            
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; padding: 15px; margin: 15px 0;">
                <h4 style="color: #155724; margin-top: 0;">✓ Relatório Aprovado</h4>
                <p style="color: #155724; margin-bottom: 0;">O relatório foi aprovado e está pronto para ser enviado aos clientes.</p>
            </div>
            
            <p>Clique abaixo para acessar o relatório:</p>
            <p><a href="{link_relatorio}" style="display: inline-block; background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Visualizar Relatório</a></p>
            
            <p>Ou copie o link: <a href="{link_relatorio}">{link_relatorio}</a></p>
            
            <p>Atenciosamente,<br>
            Sistema ELP Consultoria</p>
            """
            
            from flask_mail import Message
            msg = Message(
                subject=assunto,
                recipients=[autor.email],
                html=corpo,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            self.mail.send(msg)
            
            # Log do envio em nova transação
            from models import LogEnvioEmail
            import json
            try:
                log = LogEnvioEmail(
                    projeto_id=relatorio.projeto_id,
                    relatorio_id=relatorio.id,
                    usuario_id=usuario_id,
                    destinatarios=json.dumps([autor.email]),
                    cc=json.dumps([]),
                    bcc=json.dumps([]),
                    assunto=assunto,
                    status='enviado',
                    data_envio=datetime.utcnow()
                )
                
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar log de aprovação: {str(log_error)}")
            
            current_app.logger.info(f"Notificação de aprovação enviada para {autor.email} - Relatório {relatorio.numero}")
            return {'success': True, 'message': f'Notificação enviada para {autor.nome_completo}'}
            
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de aprovação: {str(e)}")
            
            # Fazer rollback de transação pendente
            try:
                db.session.rollback()
            except:
                pass
            
            # Log do erro em nova transação
            try:
                from models import LogEnvioEmail
                import json
                log = LogEnvioEmail(
                    projeto_id=relatorio.projeto_id,
                    relatorio_id=relatorio.id,
                    usuario_id=usuario_id,
                    destinatarios=json.dumps([autor.email]),
                    cc=json.dumps([]),
                    bcc=json.dumps([]),
                    assunto=f"Relatório {relatorio.numero} aprovado",
                    status='falhou',
                    erro_detalhes=str(e),
                    data_envio=datetime.utcnow()
                )
                
                db.session.add(log)
                db.session.commit()
            except Exception as log_error:
                db.session.rollback()
                current_app.logger.error(f"⚠️ Erro ao salvar log de erro: {str(log_error)}")
                
            return {'success': False, 'error': str(e)}

# Instância global do serviço
email_service = EmailService()