"""
Tarefas Agendadas - Sistema de Limpeza Automática
Usa APScheduler para executar tarefas periódicas
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def limpar_notificacoes_expiradas_task():
    """Tarefa periódica para limpar notificações expiradas (>24h)"""
    try:
        with scheduler.app.app_context():
            from notification_service import notification_service
            
            resultado = notification_service.limpar_notificacoes_expiradas()
            
            if resultado['success']:
                count = resultado.get('removed_count', 0)
                if count > 0:
                    logger.info(f"🧹 [SCHEDULER] {count} notificações expiradas removidas")
                else:
                    logger.debug("🧹 [SCHEDULER] Nenhuma notificação expirada encontrada")
            else:
                logger.error(f"❌ [SCHEDULER] Erro ao limpar notificações: {resultado.get('error')}")
                
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erro na tarefa de limpeza: {e}")

def init_scheduler(app):
    """Inicializar scheduler com as tarefas agendadas"""
    try:
        # Armazenar referência do app para uso nas tarefas
        scheduler.app = app
        
        # Tarefa 1: Limpar notificações expiradas a cada 6 horas
        scheduler.add_job(
            func=limpar_notificacoes_expiradas_task,
            trigger=IntervalTrigger(hours=6),
            id='limpar_notificacoes_expiradas',
            name='Limpar notificações expiradas (>24h)',
            replace_existing=True
        )
        
        # Tarefa 2: Limpeza diária às 3h da manhã (horário de baixo uso)
        scheduler.add_job(
            func=limpar_notificacoes_expiradas_task,
            trigger=CronTrigger(hour=3, minute=0),
            id='limpeza_diaria_3am',
            name='Limpeza diária às 3h',
            replace_existing=True
        )
        
        # Iniciar scheduler
        scheduler.start()
        
        logger.info("✅ Scheduler iniciado com sucesso")
        logger.info("📅 Tarefas agendadas:")
        logger.info("   - Limpeza de notificações a cada 6 horas")
        logger.info("   - Limpeza diária às 3h da manhã")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar scheduler: {e}")
        return None

def shutdown_scheduler():
    """Desligar scheduler de forma segura"""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("🛑 Scheduler desligado")
    except Exception as e:
        logger.error(f"❌ Erro ao desligar scheduler: {e}")
