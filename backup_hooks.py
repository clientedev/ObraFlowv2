"""
Hooks para backup automático
Implementa triggers para backup quando relatórios são finalizados
"""

import logging
from google_drive_service import drive_service
from flask import current_app, session

logger = logging.getLogger(__name__)

def trigger_auto_backup(project_id: int, report_type: str = 'relatorio', report_id: int = None):
    """
    Dispara backup automático quando um relatório é finalizado
    
    Args:
        project_id: ID do projeto
        report_type: Tipo do relatório ('relatorio' ou 'relatorio_express')
        report_id: ID do relatório criado (opcional)
    """
    try:
        # Verificar se o Google Drive está configurado e autenticado
        if not drive_service.is_authenticated():
            logger.warning(f"Backup automático não executado para projeto {project_id}: Google Drive não configurado")
            return False
        
        logger.info(f"Iniciando backup automático para projeto {project_id} após criação de {report_type}")
        
        # Executar backup do projeto
        result = drive_service.backup_project_files(project_id)
        
        if result['success']:
            uploaded_count = len(result.get('uploaded_files', []))
            error_count = len(result.get('errors', []))
            
            logger.info(f"Backup automático concluído para projeto {project_id}: "
                       f"{uploaded_count} arquivos enviados, {error_count} erros")
            
            return True
        else:
            logger.error(f"Erro no backup automático do projeto {project_id}: {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        logger.error(f"Erro inesperado no backup automático do projeto {project_id}: {e}")
        return False

def backup_single_report(report_id: int, report_type: str = 'relatorio'):
    """
    Faz backup de um relatório específico
    
    Args:
        report_id: ID do relatório
        report_type: Tipo do relatório ('relatorio' ou 'relatorio_express')
    """
    try:
        if not drive_service.is_authenticated():
            logger.warning(f"Backup de relatório {report_id} não executado: Google Drive não configurado")
            return False
        
        from models import Projeto, Relatorio, RelatorioExpress
        
        # Buscar o relatório e projeto
        if report_type == 'relatorio_express':
            relatorio = RelatorioExpress.query.get(report_id)
        else:
            relatorio = Relatorio.query.get(report_id)
            
        if not relatorio:
            logger.error(f"Relatório {report_id} não encontrado")
            return False
        
        projeto = Projeto.query.get(relatorio.projeto_id)
        if not projeto:
            logger.error(f"Projeto do relatório {report_id} não encontrado")
            return False
        
        # Criar pasta do projeto se não existir
        project_folder_id = drive_service.create_project_folder(projeto.nome, projeto.numero)
        if not project_folder_id:
            logger.error(f"Erro ao criar pasta do projeto {projeto.id}")
            return False
        
        # Fazer backup do relatório específico
        try:
            if report_type == 'relatorio_express':
                from pdf_generator_express import gerar_pdf_relatorio_express
                pdf_content = gerar_pdf_relatorio_express(report_id)
                filename = f"RelatorioExpress_{report_id}_{relatorio.created_at.strftime('%Y%m%d_%H%M%S')}.pdf"
            else:
                from pdf_generator_weasy import gerar_pdf_weasy
                pdf_content = gerar_pdf_weasy(report_id)
                filename = f"Relatorio_{report_id}_{relatorio.created_at.strftime('%Y%m%d_%H%M%S')}.pdf"
            
            if pdf_content:
                file_id = drive_service.upload_from_bytes(pdf_content, filename, project_folder_id)
                
                if file_id:
                    logger.info(f"Backup individual do relatório {report_id} concluído: {filename}")
                    return True
                else:
                    logger.error(f"Erro no upload do relatório {report_id}")
                    return False
            else:
                logger.error(f"Erro na geração de PDF do relatório {report_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao processar relatório {report_id}: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Erro no backup individual do relatório {report_id}: {e}")
        return False

def get_backup_status_for_project(project_id: int) -> dict:
    """Retorna status do backup para um projeto específico"""
    try:
        from models import Projeto
        
        projeto = Projeto.query.get(project_id)
        if not projeto:
            return {'error': 'Projeto não encontrado'}
        
        return {
            'project_id': project_id,
            'project_name': projeto.nome,
            'project_number': projeto.numero,
            'drive_configured': drive_service.get_backup_status()['is_configured'],
            'drive_authenticated': drive_service.is_authenticated(),
            'can_backup': drive_service.is_authenticated()
        }
        
    except Exception as e:
        return {'error': str(e)}