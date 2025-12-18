"""
Serviço de envio de e-mail via yagmail para relatórios aprovados.
Usa conta Gmail fixa: relatorioselpconsultoria@gmail.com
Envia e-mails para os envolvidos quando um relatório é aprovado.
"""
import os
import json
import yagmail
from datetime import datetime
from flask import current_app


class ReportApprovalEmailService:
    """Serviço de envio de e-mails via yagmail"""
    
    def __init__(self):
        self.from_email = "relatorioselpconsultoria@gmail.com"
        self.from_password = "ipbs dkwc osyn vixg"
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
        Retorna lista de emails únicos com logs detalhados.
        
        Destinatários:
        - Pessoa que criou o relatório (autor)
        - Aprovador global
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
            
            # 3. Acompanhantes da visita vinculados ao relatório
            if relatorio.acompanhantes:
                current_app.logger.info(f"🔍 Processando acompanhantes: {type(relatorio.acompanhantes)}")
                acompanhantes_list = []
                
                # Converter para lista se necessário
                if isinstance(relatorio.acompanhantes, list):
                    acompanhantes_list = relatorio.acompanhantes
                elif isinstance(relatorio.acompanhantes, str):
                    try:
                        acompanhantes_list = json.loads(relatorio.acompanhantes)
                        if not isinstance(acompanhantes_list, list):
                            acompanhantes_list = []
                    except json.JSONDecodeError:
                        current_app.logger.warning(f"⚠️ Erro ao fazer parse de acompanhantes JSON: {relatorio.acompanhantes}")
                        acompanhantes_list = []
                elif isinstance(relatorio.acompanhantes, dict):
                    acompanhantes_list = []
                
                current_app.logger.info(f"📋 Total de acompanhantes para processar: {len(acompanhantes_list)}")
                
                for idx, acomp in enumerate(acompanhantes_list):
                    try:
                        email = None
                        nome = "Desconhecido"
                        user_id = None
                        
                        if isinstance(acomp, dict):
                            # Extrair informações do acompanhante
                            email = (acomp.get('email', '') or '').strip()
                            nome = (acomp.get('nome', '') or '').strip() or 'Desconhecido'
                            user_id = acomp.get('id') or acomp.get('user_id')
                            
                            current_app.logger.info(f"🔍 [ACOMPANHANTE {idx+1}] nome='{nome}' id={user_id} email_salvo='{email}'")
                            
                            # 1. SE JÁ TEM EMAIL SALVO, USAR DIRETO (PRIORIDADE!)
                            if email:
                                current_app.logger.info(f"✅ Email já salvo: {email}")
                            
                            # 2. Se tem ID, buscar por ID
                            elif user_id:
                                try:
                                    from models import User
                                    user = User.query.filter_by(id=user_id).first()
                                    if user and user.email:
                                        email = user.email
                                        nome = user.nome_completo or user.username
                                        current_app.logger.info(f"✅ Email encontrado por ID {user_id}: {email}")
                                except Exception as e:
                                    current_app.logger.warning(f"⚠️ Erro ao buscar User por ID {user_id}: {e}")
                            
                            # 3. Se tem ID tipo 'ec_123' ou 'ec_133', é um email_config_id direto
                            if not email and user_id and isinstance(user_id, str) and user_id.startswith('ec_'):
                                try:
                                    from models import UserEmailConfig
                                    ec_id = int(user_id.replace('ec_', ''))
                                    email_config = UserEmailConfig.query.filter_by(id=ec_id).first()
                                    
                                    if email_config and email_config.email_address:
                                        email = email_config.email_address
                                        current_app.logger.info(f"✅ Email encontrado em user_email_config (ID={ec_id}): {email}")
                                except Exception as e:
                                    current_app.logger.warning(f"⚠️ Erro ao buscar email_config por ID {user_id}: {e}")
                            
                            # 4. Se nome é válido, buscar na user_email_config por nome
                            if not email and nome != 'Desconhecido':
                                try:
                                    from models import UserEmailConfig
                                    # Buscar por nome_funcionario (nome do funcionário responsável)
                                    email_config = UserEmailConfig.query.filter(
                                        UserEmailConfig.nome_funcionario.ilike(f'%{nome}%')
                                    ).first()
                                    
                                    if email_config and email_config.email_address:
                                        email = email_config.email_address
                                        current_app.logger.info(f"✅ Email encontrado em user_email_config por nome: {email}")
                                except Exception as e:
                                    current_app.logger.warning(f"⚠️ Erro ao buscar em user_email_config por nome: {e}")
                            
                            # 5. Fallback: buscar na tabela User por nome
                            if not email and nome != 'Desconhecido':
                                try:
                                    from models import User
                                    user = User.query.filter_by(nome_completo=nome).first()
                                    if not user:
                                        user = User.query.filter(
                                            User.nome_completo.ilike(f'%{nome}%')
                                        ).first()
                                    
                                    if user and user.email:
                                        email = user.email
                                        current_app.logger.info(f"✅ Email encontrado em User por nome: {email}")
                                except Exception as e:
                                    current_app.logger.warning(f"⚠️ Erro ao buscar em User por nome: {e}")
                        
                        # Adicionar email se encontrou
                        if email:
                            recipients.add(email)
                            current_app.logger.info(f"✉️ [ACOMPANHANTE {idx+1}] {nome} ({email})")
                        else:
                            current_app.logger.warning(f"⚠️ [ACOMPANHANTE {idx+1}] '{nome}' - SEM EMAIL ENCONTRADO")
                    
                    except Exception as e:
                        current_app.logger.warning(f"⚠️ Erro ao processar acompanhante {idx}: {e}")
            
            else:
                current_app.logger.info(f"ℹ️ Nenhum acompanhante registrado para este relatório")
            
            current_app.logger.info(f"📊 RESUMO: Total de {len(recipients)} destinatário(s) coletado(s)")
            for email in recipients:
                current_app.logger.info(f"   - {email}")
        
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao coletar destinatários: {e}", exc_info=True)
        
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
            
            # Obter nome da obra
            if hasattr(relatorio, 'projeto') and relatorio.projeto:
                obra_nome = relatorio.projeto.nome
            elif hasattr(relatorio, 'obra_nome'):
                obra_nome = relatorio.obra_nome or "Obra"
            else:
                obra_nome = "Obra"
            
            assunto = f"Relatório aprovado – Obra {obra_nome}"
            
            current_app.logger.info(f"📧 Iniciando envio de {len(recipients)} e-mail(s) para relatório {relatorio.numero}")
            current_app.logger.info(f"📧 Obra: {obra_nome}")
            current_app.logger.info(f"📧 PDF: {pdf_path}")
            
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
            erros = []
            
            # Enviar e-mail individual para cada destinatário
            for recipient_email in recipients:
                try:
                    # Obter nome do destinatário
                    destinatario_nome = recipient_email.split('@')[0]
                    
                    # Tentar encontrar nome completo do usuário
                    try:
                        from models import User
                        user = User.query.filter_by(email=recipient_email).first()
                        if user:
                            destinatario_nome = user.nome_completo or user.username
                    except:
                        pass
                    
                    # Corpo do e-mail
                    corpo = self._format_email_body(destinatario_nome, obra_nome, relatorio.data_aprovacao)
                    
                    current_app.logger.info(f"📤 Enviando email para {recipient_email}...")
                    
                    # Enviar via yagmail
                    yag.send(
                        to=recipient_email,
                        subject=assunto,
                        contents=corpo,
                        attachments=pdf_path
                    )
                    
                    enviados += 1
                    current_app.logger.info(f"✅ E-mail {enviados}/{len(recipients)} enviado: {recipient_email}")
                
                except Exception as e:
                    erro_msg = f"Erro ao enviar para {recipient_email}: {str(e)}"
                    erros.append(erro_msg)
                    current_app.logger.error(f"❌ {erro_msg}")
            
            if enviados > 0:
                current_app.logger.info(f"✅ SUCESSO: {enviados}/{len(recipients)} e-mail(s) enviado(s)")
                return {
                    'success': True,
                    'enviados': enviados,
                    'total': len(recipients),
                    'error': None
                }
            else:
                erro_final = "Falha ao enviar e-mails para todos os destinatários: " + "; ".join(erros)
                current_app.logger.error(f"❌ {erro_final}")
                return {
                    'success': False,
                    'enviados': 0,
                    'total': len(recipients),
                    'error': erro_final
                }
        
        except Exception as e:
            current_app.logger.error(f"💥 Erro geral ao enviar e-mails: {e}", exc_info=True)
            return {
                'success': False,
                'enviados': 0,
                'error': str(e)
            }
