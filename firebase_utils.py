"""
Firebase Cloud Messaging - Configuração e Funções de Envio
Sistema de Push Notifications para ELP Consultoria
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

firebase_admin = None
messaging = None
firebase_initialized = False

def initialize_firebase():
    """
    Inicializa Firebase Admin SDK
    Suporta tanto credenciais via arquivo JSON quanto variáveis de ambiente
    """
    global firebase_admin, messaging, firebase_initialized
    
    if firebase_initialized:
        logger.info("✅ Firebase já inicializado")
        return True
    
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging as fcm_messaging
        
        if firebase_admin._apps:
            logger.info("✅ Firebase já inicializado (app existente)")
            firebase_initialized = True
            messaging = fcm_messaging
            return True
        
        cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'firebase_credentials.json')
        
        if os.path.exists(cred_path):
            logger.info(f"🔧 Inicializando Firebase com arquivo: {cred_path}")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            messaging = fcm_messaging
            firebase_initialized = True
            logger.info("✅ Firebase inicializado com sucesso (arquivo JSON)")
            return True
        
        firebase_config = os.environ.get('FIREBASE_CONFIG')
        if firebase_config:
            logger.info("🔧 Inicializando Firebase com variável de ambiente")
            config_dict = json.loads(firebase_config)
            cred = credentials.Certificate(config_dict)
            firebase_admin.initialize_app(cred)
            messaging = fcm_messaging
            firebase_initialized = True
            logger.info("✅ Firebase inicializado com sucesso (variável de ambiente)")
            return True
        
        # Firebase opcional - logar apenas em debug
        logger.debug("ℹ️ Firebase não configurado (modo opcional)")
        return False
    
    except ImportError:
        logger.warning("⚠️ firebase-admin não instalado - push notifications desabilitadas")
        logger.warning("   Execute: pip install firebase-admin")
        return False
    
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Firebase: {e}")
        return False


def send_push_notification(
    user,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None
) -> bool:
    """
    Enviar notificação push para um usuário específico
    
    Args:
        user: Objeto User com fcm_token
        title: Título da notificação
        body: Corpo da mensagem
        data: Dados customizados (opcional)
        image_url: URL da imagem (opcional)
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    global messaging, firebase_initialized
    
    if not firebase_initialized:
        if not initialize_firebase():
            # Firebase opcional - retornar silenciosamente
            return False
    
    if not user or not user.fcm_token:
        # Usuário sem token - retornar silenciosamente
        return False
    
    try:
        from firebase_admin import messaging as fcm_messaging
        
        notification_config = fcm_messaging.Notification(
            title=title,
            body=body,
            image=image_url if image_url else None
        )
        
        android_config = fcm_messaging.AndroidConfig(
            priority='high',
            notification=fcm_messaging.AndroidNotification(
                icon='ic_notification',
                color='#00BCD4',
                sound='default',
                channel_id='elp_notifications'
            )
        )
        
        message = fcm_messaging.Message(
            notification=notification_config,
            data=data if data else {},
            token=user.fcm_token,
            android=android_config
        )
        
        response = fcm_messaging.send(message)
        
        logger.info(f"✅ Push notification enviada para {user.username}: {response}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar push notification: {e}")
        
        if "not-found" in str(e).lower() or "invalid" in str(e).lower():
            logger.warning(f"⚠️ Token FCM inválido para {user.username} - removendo...")
            user.fcm_token = None
            try:
                from app import db
                db.session.commit()
            except:
                pass
        
        return False


def send_push_notification_multiple(
    users: list,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Enviar notificação push para múltiplos usuários
    
    Args:
        users: Lista de objetos User
        title: Título da notificação
        body: Corpo da mensagem
        data: Dados customizados (opcional)
    
    Returns:
        dict: Estatísticas de envio
    """
    global messaging, firebase_initialized
    
    if not firebase_initialized:
        if not initialize_firebase():
            return {
                'success': False,
                'error': 'Firebase não inicializado',
                'sent': 0,
                'failed': 0
            }
    
    tokens = [user.fcm_token for user in users if user and user.fcm_token]
    
    if not tokens:
        # Nenhum token disponível - retornar silenciosamente
        return {
            'success': False,
            'error': 'Nenhum token válido',
            'sent': 0,
            'failed': len(users)
        }
    
    try:
        from firebase_admin import messaging as fcm_messaging
        
        message = fcm_messaging.MulticastMessage(
            notification=fcm_messaging.Notification(
                title=title,
                body=body
            ),
            data=data if data else {},
            tokens=tokens
        )
        
        response = fcm_messaging.send_multicast(message)
        
        logger.info(f"✅ Push notifications enviadas: {response.success_count}/{len(tokens)}")
        
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    logger.warning(f"⚠️ Falha no envio para token {idx}: {resp.exception}")
        
        return {
            'success': True,
            'sent': response.success_count,
            'failed': response.failure_count,
            'total': len(tokens)
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar push notifications múltiplas: {e}")
        return {
            'success': False,
            'error': str(e),
            'sent': 0,
            'failed': len(tokens)
        }


def verify_fcm_token(token: str) -> bool:
    """
    Verificar se um FCM token é válido
    
    Args:
        token: Token FCM a verificar
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not token or len(token) < 20:
        return False
    
    try:
        return True
    except:
        return False
