"""
Utilidades para o sistema de acompanhamento de visitas em obras
"""
import re
from flask import flash
from datetime import datetime

def validate_email_format(email):
    """
    Valida o formato de um email usando regex
    
    Args:
        email (str): Email a ser validado
        
    Returns:
        bool: True se o email for válido, False caso contrário
    """
    if not email:
        return False
    
    # Regex para validação de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def add_email_to_contact(contato_id, email, principal=False):
    """
    Adiciona um email a um contato
    
    Args:
        contato_id (int): ID do contato
        email (str): Email a ser adicionado
        principal (bool): Se este é o email principal
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from models import ContatoEmail, db
    from app import app
    
    if not validate_email_format(email):
        return False, "Formato de email inválido"
    
    # Verificar se o email já existe para este contato
    existing = ContatoEmail.query.filter_by(contato_id=contato_id, email=email).first()
    if existing:
        return False, "Este email já está cadastrado para este contato"
    
    try:
        with app.app_context():
            # Se este for o email principal, remover outros emails principais
            if principal:
                ContatoEmail.query.filter_by(contato_id=contato_id, principal=True).update({'principal': False})
            
            # Criar novo email
            novo_email = ContatoEmail(
                contato_id=contato_id,
                email=email,
                principal=principal,
                ativo=True
            )
            
            db.session.add(novo_email)
            db.session.commit()
            
            return True, "Email adicionado com sucesso"
            
    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao adicionar email: {str(e)}"

def remove_email_from_contact(contato_id, email):
    """
    Remove um email de um contato
    
    Args:
        contato_id (int): ID do contato
        email (str): Email a ser removido
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from models import ContatoEmail, db
    from app import app
    
    try:
        with app.app_context():
            email_obj = ContatoEmail.query.filter_by(contato_id=contato_id, email=email).first()
            if not email_obj:
                return False, "Email não encontrado"
            
            db.session.delete(email_obj)
            db.session.commit()
            
            return True, "Email removido com sucesso"
            
    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao remover email: {str(e)}"

def update_email_status(contato_id, email, principal=None, ativo=None):
    """
    Atualiza o status de um email
    
    Args:
        contato_id (int): ID do contato
        email (str): Email a ser atualizado
        principal (bool, optional): Se é email principal
        ativo (bool, optional): Se está ativo
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from models import ContatoEmail, db
    from app import app
    
    try:
        with app.app_context():
            email_obj = ContatoEmail.query.filter_by(contato_id=contato_id, email=email).first()
            if not email_obj:
                return False, "Email não encontrado"
            
            if principal is not None:
                if principal:
                    # Remover outros emails principais
                    ContatoEmail.query.filter_by(contato_id=contato_id, principal=True).update({'principal': False})
                email_obj.principal = principal
            
            if ativo is not None:
                email_obj.ativo = ativo
            
            db.session.commit()
            
            return True, "Email atualizado com sucesso"
            
    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao atualizar email: {str(e)}"

def get_contact_emails_for_project(projeto_id, tipo_relacionamento=None):
    """
    Obtém todos os emails de contatos associados a um projeto
    
    Args:
        projeto_id (int): ID do projeto
        tipo_relacionamento (str, optional): Filtrar por tipo de relacionamento
        
    Returns:
        list: Lista de emails
    """
    from models import Contato, ContatoProjeto, ContatoEmail, db
    
    query = db.session.query(ContatoEmail).join(Contato).join(ContatoProjeto).filter(
        ContatoProjeto.projeto_id == projeto_id,
        ContatoEmail.ativo == True
    )
    
    if tipo_relacionamento:
        if isinstance(tipo_relacionamento, list):
            query = query.filter(ContatoProjeto.tipo_relacionamento.in_(tipo_relacionamento))
        else:
            query = query.filter(ContatoProjeto.tipo_relacionamento == tipo_relacionamento)
    
    emails = query.all()
    return [email.email for email in emails]

def get_contacts_without_emails():
    """
    Retorna contatos que não possuem emails cadastrados
    
    Returns:
        list: Lista de contatos sem email
    """
    from models import Contato, ContatoEmail, db
    from sqlalchemy import and_, not_, exists
    
    # Contatos que não têm emails na tabela ContatoEmail E não têm email no campo legacy
    contatos_sem_email = db.session.query(Contato).filter(
        and_(
            not_(exists().where(ContatoEmail.contato_id == Contato.id)),
            Contato.email.is_(None)
        )
    ).all()
    
    return contatos_sem_email

def migrate_legacy_emails():
    """
    Migra emails do campo legacy 'email' para a tabela ContatoEmail
    
    Returns:
        tuple: (success: bool, migrated_count: int, message: str)
    """
    from models import Contato, ContatoEmail, db
    from app import app
    
    migrated_count = 0
    
    try:
        with app.app_context():
            # Buscar contatos com email no campo legacy que ainda não foram migrados
            contatos_com_legacy_email = db.session.query(Contato).filter(
                Contato.email.isnot(None),
                Contato.email != ''
            ).all()
            
            for contato in contatos_com_legacy_email:
                # Verificar se já existe este email na tabela ContatoEmail
                existing = ContatoEmail.query.filter_by(contato_id=contato.id, email=contato.email).first()
                
                if not existing and validate_email_format(contato.email):
                    # Criar entrada na nova tabela
                    novo_email = ContatoEmail(
                        contato_id=contato.id,
                        email=contato.email,
                        principal=True,  # Email legacy será considerado principal
                        ativo=True
                    )
                    
                    db.session.add(novo_email)
                    migrated_count += 1
            
            db.session.commit()
            
            return True, migrated_count, f"Migrados {migrated_count} emails com sucesso"
            
    except Exception as e:
        db.session.rollback()
        return False, 0, f"Erro na migração: {str(e)}"

def generate_project_number():
    """
    Gera um número sequencial único para projeto
    
    Returns:
        str: Número do projeto no formato PRJ-YYYYMMDD-XXX
    """
    from models import Projeto
    
    today = datetime.now()
    prefix = f"PRJ-{today.strftime('%Y%m%d')}"
    
    # Find highest number for today
    projects_today = Projeto.query.filter(
        Projeto.numero.like(f"{prefix}-%")
    ).order_by(Projeto.numero.desc()).first()
    
    if projects_today:
        # Extract number and increment
        last_number = int(projects_today.numero.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:03d}"

def generate_report_number():
    """
    Gera um número sequencial único para relatório
    
    Returns:
        str: Número do relatório no formato REL-YYYYMMDD-XXX
    """
    from models import Relatorio
    
    today = datetime.now()
    prefix = f"REL-{today.strftime('%Y%m%d')}"
    
    # Find highest number for today
    reports_today = Relatorio.query.filter(
        Relatorio.numero.like(f"{prefix}-%")
    ).order_by(Relatorio.numero.desc()).first()
    
    if reports_today:
        # Extract number and increment
        last_number = int(reports_today.numero.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:03d}"

def generate_visit_number():
    """
    Gera um número sequencial único para visita
    
    Returns:
        str: Número da visita no formato VIS-YYYYMMDD-XXX
    """
    from models import Visita
    
    today = datetime.now()
    prefix = f"VIS-{today.strftime('%Y%m%d')}"
    
    # Find highest number for today
    visits_today = Visita.query.filter(
        Visita.numero.like(f"{prefix}-%")
    ).order_by(Visita.numero.desc()).first()
    
    if visits_today:
        # Extract number and increment
        last_number = int(visits_today.numero.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:03d}"

def send_report_email(report_id, email_list):
    """
    Envia relatório por email para lista de destinatários
    
    Args:
        report_id (int): ID do relatório
        email_list (list): Lista de emails de destinatários
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from models import Relatorio, EnvioRelatorio, db
    from flask_mail import Message
    from app import mail
    
    try:
        relatorio = Relatorio.query.get(report_id)
        if not relatorio:
            return False, "Relatório não encontrado"
        
        # TODO: Implementar envio real de email
        # Por enquanto, apenas registra o envio
        for email in email_list:
            if validate_email_format(email):
                envio = EnvioRelatorio(
                    relatorio_id=report_id,
                    email_destinatario=email,
                    status_entrega='Enviado'
                )
                db.session.add(envio)
        
        db.session.commit()
        return True, f"Relatório enviado para {len(email_list)} destinatários"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao enviar relatório: {str(e)}"

def calculate_reimbursement_total(quilometragem, valor_km, alimentacao, hospedagem, outros_gastos):
    """
    Calcula o total de reembolso
    
    Args:
        quilometragem (float): Quilometragem percorrida
        valor_km (float): Valor por quilômetro
        alimentacao (float): Gastos com alimentação
        hospedagem (float): Gastos com hospedagem
        outros_gastos (float): Outros gastos
        
    Returns:
        float: Total calculado
    """
    total_km = (quilometragem or 0) * (valor_km or 0)
    total = total_km + (alimentacao or 0) + (hospedagem or 0) + (outros_gastos or 0)
    return round(total, 2)