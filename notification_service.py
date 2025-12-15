import os
import logging
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, messaging
from flask import current_app
# Import models inside functions to avoid circular imports
# from models import Notificacao, User, Projeto, Relatorio, FuncionarioProjeto
from app import db

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.firebase_initialized = False
        self.init_firebase()
    
    def init_firebase(self):
        try:
            if not firebase_admin._apps:
                firebase_credentials = os.environ.get('FIREBASE_CREDENTIALS_JSON')
                
                if firebase_credentials:
                    import json
                    cred_dict = json.loads(firebase_credentials)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    self.firebase_initialized = True
                    logger.info("✅ Firebase Admin SDK inicializado com sucesso")
                else:
                    # Firebase opcional - não logar warning
                    logger.debug("ℹ️ Firebase não configurado (modo opcional)")
                    self.firebase_initialized = False
            else:
                self.firebase_initialized = True
                logger.info("✅ Firebase Admin SDK já estava inicializado")
        except Exception as e:
            logger.debug(f"ℹ️ Firebase não disponível: {e}")
            self.firebase_initialized = False
    
    def criar_notificacao(self, user_id, tipo, titulo, mensagem, link_destino=None, enviar_push=True):
        """
        Cria uma notificação genérica no sistema
        
        Args:
            user_id: ID do usuário destinatário
            tipo: Tipo da notificação (obra_criada, relatorio_pendente, relatorio_reprovado)
            titulo: Título da notificação
            mensagem: Mensagem da notificação
            link_destino: URL de destino ao clicar na notificação
            enviar_push: Se deve enviar push notification
        """
        try:
            from models import Notificacao, User
            
            notificacao = Notificacao(
                user_id=user_id,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                link_destino=link_destino,
                status='nova'
            )
            
            db.session.add(notificacao)
            db.session.flush()
            
            if enviar_push:
                usuario_destino = User.query.get(user_id)
                if usuario_destino and usuario_destino.fcm_token:
                    self.enviar_push_notification(
                        token=usuario_destino.fcm_token,
                        titulo=titulo,
                        corpo=mensagem,
                        link=link_destino,
                        tipo=tipo
                    )
                else:
                    logger.info(f"📱 Usuário {user_id} não tem FCM token configurado")
            
            db.session.commit()
            logger.info(f"✅ Notificação criada: {titulo} para usuário {user_id}")
            
            return {
                'success': True,
                'notificacao_id': notificacao.id
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao criar notificação: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def criar_notificacao_obra_criada(self, projeto_id):
        """
        Cria notificações para todos os responsáveis de uma obra recém-criada
        
        Args:
            projeto_id: ID do projeto/obra criado
        """
        try:
            from models import Projeto, FuncionarioProjeto
            
            projeto = Projeto.query.get(projeto_id)
            if not projeto:
                logger.error(f"❌ Projeto {projeto_id} não encontrado")
                return {'success': False, 'error': 'Projeto não encontrado'}
            
            # Obter todos os responsáveis pela obra
            responsaveis_ids = set()
            
            # Adicionar responsável principal apenas se existir e for válido
            if projeto.responsavel_id is not None:
                responsaveis_ids.add(projeto.responsavel_id)
            
            # Adicionar funcionários responsáveis do projeto
            funcionarios = FuncionarioProjeto.query.filter_by(
                projeto_id=projeto_id,
                ativo=True
            ).all()
            
            for func in funcionarios:
                if func.user_id is not None:
                    responsaveis_ids.add(func.user_id)
            
            # Filtrar IDs inválidos (None, 0, negativos)
            responsaveis_ids = {uid for uid in responsaveis_ids if uid and uid > 0}
            
            # Verificar se há responsáveis válidos
            if not responsaveis_ids:
                logger.warning(f"⚠️ Nenhum responsável válido encontrado para projeto {projeto_id}")
                return {'success': True, 'count': 0, 'message': 'Nenhum responsável para notificar'}
            
            # Criar notificação para cada responsável
            notificacoes_criadas = 0
            for user_id in responsaveis_ids:
                resultado = self.criar_notificacao(
                    user_id=user_id,
                    tipo='obra_criada',
                    titulo='Nova obra criada',
                    mensagem=f'A obra "{projeto.nome}" foi criada e você foi designado como responsável.',
                    link_destino=f'/projects/{projeto_id}'
                )
                
                if resultado['success']:
                    notificacoes_criadas += 1
            
            logger.info(f"✅ {notificacoes_criadas} notificações de obra criada enviadas")
            return {'success': True, 'count': notificacoes_criadas}
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar notificações de obra criada: {e}")
            return {'success': False, 'error': str(e)}
    
    def criar_notificacao_relatorio_pendente(self, relatorio_id):
        """
        Cria notificação para o aprovador de um relatório pendente
        Busca aprovador específico do projeto ou aprovador global
        
        Args:
            relatorio_id: ID do relatório pendente
        """
        try:
            from models import Relatorio, Projeto, AprovadorPadrao
            
            relatorio = Relatorio.query.get(relatorio_id)
            if not relatorio:
                logger.error(f"❌ Relatório {relatorio_id} não encontrado")
                return {'success': False, 'error': 'Relatório não encontrado'}
            
            # Buscar aprovador específico do projeto ou aprovador global
            aprovador_id = None
            
            # 1. Tentar buscar aprovador específico do projeto
            if relatorio.projeto_id:
                aprovador_projeto = AprovadorPadrao.query.filter_by(
                    projeto_id=relatorio.projeto_id,
                    ativo=True
                ).order_by(AprovadorPadrao.prioridade).first()
                
                if aprovador_projeto:
                    aprovador_id = aprovador_projeto.aprovador_id
                    logger.info(f"✅ Aprovador específico encontrado para projeto {relatorio.projeto_id}: user {aprovador_id}")
            
            # 2. Se não encontrou aprovador específico, buscar aprovador global
            if not aprovador_id:
                aprovador_global = AprovadorPadrao.query.filter_by(
                    is_global=True,
                    ativo=True
                ).order_by(AprovadorPadrao.prioridade).first()
                
                if aprovador_global:
                    aprovador_id = aprovador_global.aprovador_id
                    logger.info(f"✅ Aprovador global encontrado: user {aprovador_id}")
            
            # 3. Fallback: usar aprovador_id do relatório se existir
            if not aprovador_id and relatorio.aprovador_id:
                aprovador_id = relatorio.aprovador_id
                logger.info(f"✅ Usando aprovador_id do relatório: user {aprovador_id}")
            
            # Se não encontrou nenhum aprovador, retornar erro
            if not aprovador_id:
                logger.warning(f"⚠️ Relatório {relatorio_id} não tem aprovador designado (nem específico, nem global)")
                return {'success': False, 'error': 'Relatório sem aprovador designado'}
            
            # Buscar informações do projeto para mensagem mais completa
            projeto = Projeto.query.get(relatorio.projeto_id) if relatorio.projeto_id else None
            projeto_nome = projeto.nome if projeto else "Sem projeto"
            
            resultado = self.criar_notificacao(
                user_id=aprovador_id,
                tipo='relatorio_pendente',
                titulo='Você tem um relatório com aprovação pendente',
                mensagem=f'O relatório "{relatorio.titulo or relatorio.numero}" da obra "{projeto_nome}" está aguardando sua aprovação.',
                link_destino=f'/reports/{relatorio_id}/review'
            )
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar notificação de relatório pendente: {e}")
            return {'success': False, 'error': str(e)}
    
    def criar_notificacao_relatorio_reprovado(self, relatorio_id):
        """
        Cria notificação para o autor de um relatório reprovado
        
        Args:
            relatorio_id: ID do relatório reprovado
        """
        try:
            from models import Relatorio, Projeto
            
            relatorio = Relatorio.query.get(relatorio_id)
            if not relatorio:
                logger.error(f"❌ Relatório {relatorio_id} não encontrado")
                return {'success': False, 'error': 'Relatório não encontrado'}
            
            projeto = Projeto.query.get(relatorio.projeto_id) if relatorio.projeto_id else None
            projeto_nome = projeto.nome if projeto else "Sem projeto"
            numero_rel = relatorio.numero or "S/N"
            
            resultado = self.criar_notificacao(
                user_id=relatorio.autor_id,
                tipo='relatorio_reprovado',
                titulo='Relatório reprovado',
                mensagem=f'O relatório nº {numero_rel} da obra "{projeto_nome}" foi reprovado. Verifique as observações e corrija antes de reenviar.',
                link_destino=f'/reports/{relatorio_id}/edit'
            )
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar notificação de relatório reprovado: {e}")
            return {'success': False, 'error': str(e)}
    
    def enviar_push_notification(self, token, titulo, corpo, link=None, tipo=None):
        if not self.firebase_initialized:
            # Firebase opcional - retornar silenciosamente
            return False
        
        try:
            message_data = {
                'tipo': tipo or 'geral',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if link:
                message_data['link'] = link
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=corpo
                ),
                data=message_data,
                webpush=messaging.WebpushConfig(
                    fcm_options=messaging.WebpushFCMOptions(
                        link=link
                    ) if link else None,
                    notification=messaging.WebpushNotification(
                        title=titulo,
                        body=corpo,
                        icon='/static/icons/icon-192x192.png',
                        badge='/static/icons/icon-72x72.png'
                    )
                ),
                token=token
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Push notification enviada com sucesso: {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar push notification: {e}")
            return False
    
    def marcar_como_lida(self, notificacao_id, user_id):
        """
        Marca uma notificação como lida
        
        Args:
            notificacao_id: ID da notificação
            user_id: ID do usuário (para validação de permissão)
        """
        try:
            from models import Notificacao
            
            notificacao = Notificacao.query.filter_by(
                id=notificacao_id,
                user_id=user_id
            ).first()
            
            if not notificacao:
                return {'success': False, 'error': 'Notificação não encontrada'}
            
            notificacao.marcar_como_lida()
            db.session.commit()
            
            return {'success': True}
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao marcar notificação como lida: {e}")
            return {'success': False, 'error': str(e)}
    
    def marcar_todas_como_lidas(self, user_id):
        """
        Marca todas as notificações de um usuário como lidas
        
        Args:
            user_id: ID do usuário
        """
        try:
            from models import Notificacao
            
            notificacoes = Notificacao.query.filter_by(
                user_id=user_id,
                status='nova'
            ).all()
            
            count = 0
            for notificacao in notificacoes:
                notificacao.marcar_como_lida()
                count += 1
            
            db.session.commit()
            logger.info(f"✅ {count} notificações marcadas como lidas para usuário {user_id}")
            
            return {'success': True, 'count': count}
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao marcar todas como lidas: {e}")
            return {'success': False, 'error': str(e)}
    
    def listar_notificacoes(self, user_id, apenas_nao_lidas=False, limit=50):
        """
        Lista as notificações de um usuário
        
        Args:
            user_id: ID do usuário
            apenas_nao_lidas: Se deve retornar apenas notificações não lidas
            limit: Número máximo de notificações a retornar
        """
        try:
            from models import Notificacao
            
            query = Notificacao.query.filter_by(user_id=user_id)
            
            if apenas_nao_lidas:
                query = query.filter_by(status='nova')
            
            notificacoes = query.order_by(Notificacao.created_at.desc()).limit(limit).all()
            
            return {
                'success': True,
                'notificacoes': [n.to_dict() for n in notificacoes],
                'total': len(notificacoes)
            }
        
        except Exception as e:
            logger.error(f"❌ Erro ao listar notificações: {e}")
            return {'success': False, 'error': str(e)}
    
    def criar_notificacao_relatorio_aprovado(self, relatorio_id, aprovador_id):
        """
        Cria notificação para o autor quando relatório é aprovado
        
        Args:
            relatorio_id: ID do relatório aprovado
            aprovador_id: ID do aprovador que aprovou
        """
        try:
            from models import Relatorio, User, Projeto
            
            relatorio = Relatorio.query.get(relatorio_id)
            if not relatorio:
                logger.error(f"❌ Relatório {relatorio_id} não encontrado")
                return {'success': False, 'error': 'Relatório não encontrado'}
            
            # Notificar o autor do relatório
            aprovador = User.query.get(aprovador_id)
            aprovador_nome = aprovador.nome_completo if aprovador else "Aprovador"
            
            projeto = Projeto.query.get(relatorio.projeto_id) if relatorio.projeto_id else None
            projeto_nome = projeto.nome if projeto else "Sem projeto"
            
            resultado = self.criar_notificacao(
                user_id=relatorio.autor_id,
                tipo='relatorio_aprovado',
                titulo='Relatório aprovado',
                mensagem=f'Seu relatório "{relatorio.titulo or relatorio.numero}" da obra "{projeto_nome}" foi aprovado por {aprovador_nome}.',
                link_destino=f'/reports/{relatorio_id}'
            )
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar notificação de relatório aprovado: {e}")
            return {'success': False, 'error': str(e)}
    
    def criar_notificacao_relatorio_criado(self, relatorio_id):
        """
        Cria notificação para participantes quando um novo relatório é criado
        
        Args:
            relatorio_id: ID do relatório criado
        """
        try:
            from models import Relatorio, Projeto, FuncionarioProjeto, AprovadorPadrao
            
            relatorio = Relatorio.query.get(relatorio_id)
            if not relatorio:
                logger.error(f"❌ Relatório {relatorio_id} não encontrado")
                return {'success': False, 'error': 'Relatório não encontrado'}
            
            projeto = Projeto.query.get(relatorio.projeto_id) if relatorio.projeto_id else None
            projeto_nome = projeto.nome if projeto else "Sem projeto"
            
            # Coletar IDs de usuários a notificar (excluindo o autor)
            usuarios_a_notificar = set()
            
            # 1. Responsável do projeto
            if projeto and projeto.responsavel_id and projeto.responsavel_id != relatorio.autor_id:
                usuarios_a_notificar.add(projeto.responsavel_id)
            
            # 2. Funcionários do projeto
            if relatorio.projeto_id:
                funcionarios = FuncionarioProjeto.query.filter_by(
                    projeto_id=relatorio.projeto_id,
                    ativo=True
                ).all()
                
                for func in funcionarios:
                    if func.user_id and func.user_id != relatorio.autor_id:
                        usuarios_a_notificar.add(func.user_id)
            
            # Criar notificações
            notificacoes_criadas = 0
            for user_id in usuarios_a_notificar:
                resultado = self.criar_notificacao(
                    user_id=user_id,
                    tipo='relatorio_criado',
                    titulo='Novo relatório criado',
                    mensagem=f'Um novo relatório "{relatorio.titulo or relatorio.numero}" foi criado para a obra "{projeto_nome}".',
                    link_destino=f'/reports/{relatorio_id}'
                )
                
                if resultado['success']:
                    notificacoes_criadas += 1
            
            logger.info(f"✅ {notificacoes_criadas} notificações de relatório criado enviadas")
            return {'success': True, 'count': notificacoes_criadas}
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar notificações de relatório criado: {e}")
            return {'success': False, 'error': str(e)}
    
    def criar_notificacao_relatorio_editado(self, relatorio_id, editor_id):
        """
        Cria notificação quando relatório é editado (se estiver aguardando aprovação)
        
        Args:
            relatorio_id: ID do relatório editado
            editor_id: ID do usuário que editou
        """
        try:
            from models import Relatorio, Projeto, AprovadorPadrao, User
            
            relatorio = Relatorio.query.get(relatorio_id)
            if not relatorio:
                logger.error(f"❌ Relatório {relatorio_id} não encontrado")
                return {'success': False, 'error': 'Relatório não encontrado'}
            
            # Só notificar se o relatório está aguardando aprovação
            if relatorio.status != 'Aguardando Aprovação':
                logger.debug(f"ℹ️ Relatório {relatorio_id} não está aguardando aprovação - notificação não criada")
                return {'success': True, 'message': 'Relatório não está aguardando aprovação'}
            
            # Buscar aprovador
            aprovador_id = None
            
            if relatorio.projeto_id:
                aprovador_projeto = AprovadorPadrao.query.filter_by(
                    projeto_id=relatorio.projeto_id,
                    ativo=True
                ).order_by(AprovadorPadrao.prioridade).first()
                
                if aprovador_projeto:
                    aprovador_id = aprovador_projeto.aprovador_id
            
            if not aprovador_id:
                aprovador_global = AprovadorPadrao.query.filter_by(
                    is_global=True,
                    ativo=True
                ).order_by(AprovadorPadrao.prioridade).first()
                
                if aprovador_global:
                    aprovador_id = aprovador_global.aprovador_id
            
            if not aprovador_id:
                logger.warning(f"⚠️ Nenhum aprovador encontrado para relatório {relatorio_id}")
                return {'success': False, 'error': 'Nenhum aprovador encontrado'}
            
            # Não notificar se o editor é o próprio aprovador
            if editor_id == aprovador_id:
                logger.debug(f"ℹ️ Editor é o aprovador - notificação não criada")
                return {'success': True, 'message': 'Editor é o aprovador'}
            
            projeto = Projeto.query.get(relatorio.projeto_id) if relatorio.projeto_id else None
            projeto_nome = projeto.nome if projeto else "Sem projeto"
            
            editor = User.query.get(editor_id)
            editor_nome = editor.nome_completo if editor else "Um usuário"
            
            resultado = self.criar_notificacao(
                user_id=aprovador_id,
                tipo='relatorio_editado',
                titulo='Relatório pendente foi editado',
                mensagem=f'{editor_nome} editou o relatório "{relatorio.titulo or relatorio.numero}" da obra "{projeto_nome}" que está aguardando sua aprovação.',
                link_destino=f'/reports/{relatorio_id}/review'
            )
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar notificação de relatório editado: {e}")
            return {'success': False, 'error': str(e)}
    
    def limpar_notificacoes_expiradas(self):
        """
        Remove notificações que expiraram (mais de 24 horas)
        """
        try:
            from models import Notificacao
            
            agora = datetime.utcnow()
            
            # Buscar notificações expiradas
            notificacoes_expiradas = Notificacao.query.filter(
                Notificacao.expires_at < agora
            ).all()
            
            count = len(notificacoes_expiradas)
            
            if count > 0:
                for notificacao in notificacoes_expiradas:
                    db.session.delete(notificacao)
                
                db.session.commit()
                logger.info(f"🧹 {count} notificações expiradas removidas")
            else:
                logger.debug("ℹ️ Nenhuma notificação expirada encontrada")
            
            return {'success': True, 'removed_count': count}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao limpar notificações expiradas: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_icone_tipo(self, tipo):
        icones = {
            'obra_criada': '🏗️',
            'relatorio_pendente': '📄',
            'relatorio_aprovado': '✅',
            'relatorio_reprovado': '❌',
            'relatorio_criado': '📝',
            'relatorio_editado': '✏️',
            'aprovado': '✅',
            'rejeitado': '⚠️',
            'enviado_para_aprovacao': '📤'
        }
        return icones.get(tipo, '🔔')

notification_service = NotificationService()
