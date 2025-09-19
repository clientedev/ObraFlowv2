"""
Per-project Report Numbering System
Implements sequential numbering within each project while maintaining backward compatibility
"""
import logging
from app import db

def generate_project_report_number(project_id):
    """
    Generate sequential report number for a specific project
    Returns the next available number (1, 2, 3...) for the given project
    """
    try:
        from models import Relatorio
        
        # Find the highest numero_relatorio for this project
        ultimo_numero = db.session.query(
            db.func.max(Relatorio.numero_relatorio)
        ).filter_by(projeto_id=project_id).scalar()
        
        # Return next available number (start at 1 if no reports exist)
        proximo_numero = (ultimo_numero or 0) + 1
        logging.info(f"Generated project report number {proximo_numero} for project {project_id}")
        return proximo_numero
        
    except Exception as e:
        logging.error(f"Error generating project report number: {e}")
        return 1

def get_display_report_number(relatorio):
    """
    Get the display number for a report (with fallback for legacy reports)
    Returns: tuple (display_number, is_legacy)
    """
    try:
        if relatorio.numero_relatorio is not None:
            # New per-project numbering
            return str(relatorio.numero_relatorio), False
        else:
            # Legacy global numbering - extract from numero field
            if relatorio.numero:
                return relatorio.numero, True
            else:
                return "N/A", True
    except Exception as e:
        logging.error(f"Error getting display number for report {relatorio.id}: {e}")
        return "N/A", True

def get_formatted_report_title(relatorio):
    """
    Generate formatted report title with project-specific numbering
    """
    try:
        display_number, is_legacy = get_display_report_number(relatorio)
        
        if is_legacy:
            return f"Relatório {display_number} - {relatorio.titulo}"
        else:
            # New format: Project name + sequential number
            project_name = relatorio.projeto.nome if relatorio.projeto else "Projeto"
            return f"{project_name} - Relatório {display_number}"
            
    except Exception as e:
        logging.error(f"Error formatting report title: {e}")
        return relatorio.titulo if relatorio.titulo else "Relatório"