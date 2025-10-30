import os
import logging
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, messaging
from flask import current_app
from models import Notificacao, User
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
                    logger.warning("⚠️ Firebase não configurado (FIREBASE_CREDENTIALS_JSON não encontrado)")
            else:
                self.firebase_initialized = True
                logger.info("✅ Firebase Admin SDK já estava inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Firebase: {e}")
            self.firebase_initialized = False
    
    def criar_notificacao(self, usuario_destino_id, usuario_origem_id, titulo, mensagem, tipo, 
                         relatorio_id=None, link_destino=None, enviar_push=True):
        try:
            notificacao = Notificacao(
                usuario_destino_id=usuario_destino_id,
                usuario_origem_id=usuario_origem_id,
                titulo=titulo,
                mensagem=mensagem,
                tipo=tipo,
                relatorio_id=relatorio_id,
                link_destino=link_destino,
                status='nao_lida'
            )
            
            db.session.add(notificacao)
            db.session.flush()
            
            if enviar_push:
                usuario_destino = User.query.get(usuario_destino_id)
                if usuario_destino and usuario_destino.fcm_token:
                    push_sucesso = self.enviar_push_notification(
                        token=usuario_destino.fcm_token,
                        titulo=titulo,
                        corpo=mensagem,
                        link=link_destino,
                        tipo=tipo
                    )
                    
                    notificacao.push_enviado = True
                    notificacao.push_sucesso = push_sucesso
                else:
                    logger.info(f"📱 Usuário {usuario_destino_id} não tem FCM token configurado")
            
            db.session.commit()
            logger.info(f"✅ Notificação criada: {titulo} para usuário {usuario_destino_id}")
            
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
    
    def enviar_push_notification(self, token, titulo, corpo, link=None, tipo=None):
        if not self.firebase_initialized:
            logger.warning("⚠️ Firebase não inicializado - push notification não enviada")
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
    
    def limpar_notificacoes_expiradas(self):
        try:
            now = datetime.utcnow()
            notificacoes_expiradas = Notificacao.query.filter(
                Notificacao.expires_at < now
            ).all()
            
            count = len(notificacoes_expiradas)
            
            for notificacao in notificacoes_expiradas:
                db.session.delete(notificacao)
            
            db.session.commit()
            logger.info(f"🧹 {count} notificações expiradas removidas")
            
            return {
                'success': True,
                'removed_count': count
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao limpar notificações expiradas: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def marcar_como_lida(self, notificacao_id, usuario_id):
        try:
            notificacao = Notificacao.query.filter_by(
                id=notificacao_id,
                usuario_destino_id=usuario_id
            ).first()
            
            if not notificacao:
                return {'success': False, 'error': 'Notificação não encontrada'}
            
            notificacao.status = 'lida'
            notificacao.lida_em = datetime.utcnow()
            db.session.commit()
            
            return {'success': True}
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao marcar notificação como lida: {e}")
            return {'success': False, 'error': str(e)}
    
    def marcar_todas_como_lidas(self, usuario_id):
        try:
            notificacoes = Notificacao.query.filter_by(
                usuario_destino_id=usuario_id,
                status='nao_lida'
            ).all()
            
            count = 0
            for notificacao in notificacoes:
                notificacao.status = 'lida'
                notificacao.lida_em = datetime.utcnow()
                count += 1
            
            db.session.commit()
            logger.info(f"✅ {count} notificações marcadas como lidas para usuário {usuario_id}")
            
            return {'success': True, 'count': count}
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao marcar todas como lidas: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_icone_tipo(self, tipo):
        icones = {
            'obra_criada': '🏗️',
            'relatorio_pendente': '📄',
            'aprovado': '✅',
            'rejeitado': '⚠️',
            'enviado_para_aprovacao': '📤'
        }
        return icones.get(tipo, '🔔')

notification_service = NotificationService()
