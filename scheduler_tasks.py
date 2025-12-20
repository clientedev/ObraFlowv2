"""
Tarefas Agendadas - Sistema de Limpeza Automática
Usa APScheduler para executar tarefas periódicas
"""

import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app import db

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

def processar_fila_email_task():
    """Tarefa periódica para processar fila de envio de emails com delay"""
    try:
        with scheduler.app.app_context():
            from models import EmailQueue, RelatorioExpress, Relatorio
            from email_service_unified import get_email_service
            import os
            
            # Buscar emails pendentes
            emails_pendentes = EmailQueue.query.filter_by(status='pending').all()
            
            if not emails_pendentes:
                logger.debug("📬 [SCHEDULER] Nenhum email pendente na fila")
                return
            
            logger.info(f"📬 [SCHEDULER] Processando {len(emails_pendentes)} email(s) da fila...")
            email_service = get_email_service()
            
            for fila in emails_pendentes:
                try:
                    # Obter relatório
                    if fila.relatorio_type == 'express':
                        relatorio = RelatorioExpress.query.get(fila.relatorio_express_id)
                    else:
                        relatorio = Relatorio.query.get(fila.relatorio_id)
                    
                    if not relatorio:
                        fila.status = 'erro'
                        fila.erro_mensagem = 'Relatório não encontrado'
                        logger.warning(f"⚠️ [SCHEDULER] Relatório não encontrado para fila {fila.id}")
                        db.session.commit()
                        continue
                    
                    # Verificar se PDF existe
                    if fila.pdf_path and os.path.exists(fila.pdf_path):
                        # Enviar email
                        resultado = email_service.send_approval_email(relatorio, fila.pdf_path)
                        
                        if resultado.get('enviados', 0) > 0:
                            fila.status = 'enviado'
                            fila.processado_at = datetime.utcnow()
                            logger.info(f"✅ [SCHEDULER] Email enviado para {resultado.get('enviados')} destinatário(s) - Fila {fila.id}")
                        else:
                            fila.tentativas += 1
                            if fila.tentativas >= 5:
                                fila.status = 'erro'
                                fila.erro_mensagem = 'Nenhum destinatário válido encontrado'
                                logger.error(f"❌ [SCHEDULER] Nenhum destinatário válido - Fila {fila.id}")
                            else:
                                logger.warning(f"⚠️ [SCHEDULER] Sem destinatários válidos - Tentativa {fila.tentativas}/5 - Fila {fila.id}")
                    else:
                        fila.tentativas += 1
                        if fila.tentativas >= 5:
                            fila.status = 'erro'
                            fila.erro_mensagem = f'PDF não encontrado: {fila.pdf_path}'
                            logger.error(f"❌ [SCHEDULER] PDF não encontrado - Fila {fila.id}")
                        else:
                            logger.warning(f"⚠️ [SCHEDULER] PDF ainda não gerado - Tentativa {fila.tentativas}/5 - Fila {fila.id}")
                    
                    db.session.commit()
                    
                except Exception as e:
                    fila.status = 'erro'
                    fila.erro_mensagem = str(e)
                    fila.tentativas += 1
                    logger.error(f"❌ [SCHEDULER] Erro ao processar fila {fila.id}: {e}")
                    db.session.commit()
                    
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Erro na tarefa de processamento de fila: {e}")


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
        
        # Tarefa 3: Processar fila de emails a cada 2 minutos
        scheduler.add_job(
            func=processar_fila_email_task,
            trigger=IntervalTrigger(seconds=120),
            id='processar_fila_email',
            name='Processar fila de emails (delay system)',
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
