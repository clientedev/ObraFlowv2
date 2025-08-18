import os
import uuid
from datetime import datetime, timedelta
from flask import current_app, render_template
from flask_mail import Message
from werkzeug.utils import secure_filename as werkzeug_secure_filename
from app import mail, db
from models import Projeto, Relatorio

def secure_filename(filename):
    """Secure filename wrapper"""
    return werkzeug_secure_filename(filename)

def generate_project_number():
    """Generate sequential project number"""
    last_project = Projeto.query.order_by(Projeto.id.desc()).first()
    if last_project:
        last_number = int(last_project.numero.split('-')[-1])
        return f"PROJ-{last_number + 1:04d}"
    else:
        return "PROJ-0001"

def generate_report_number():
    """Generate sequential report number"""
    current_year = datetime.now().year
    last_report = Relatorio.query.filter(
        Relatorio.numero.like(f"REL-{current_year}-%")
    ).order_by(Relatorio.id.desc()).first()
    
    if last_report:
        last_number = int(last_report.numero.split('-')[-1])
        return f"REL-{current_year}-{last_number + 1:04d}"
    else:
        return f"REL-{current_year}-0001"

def generate_visit_number():
    """Generate sequential visit number"""
    from models import Visita
    last_visit = Visita.query.order_by(Visita.id.desc()).first()
    if last_visit and last_visit.numero:
        try:
            last_number = int(last_visit.numero.split('-')[-1])
            return f"VIS-{last_number + 1:04d}"
        except:
            pass
    return "VIS-0001"

def send_report_email(relatorio, email_destinatario, nome_destinatario=None):
    """Send report via email"""
    try:
        subject = f"Relatório de Obra - {relatorio.numero} - {relatorio.titulo}"
        
        # Prepare content with line breaks
        conteudo_html = relatorio.conteudo.replace('\n', '<br>') if relatorio.conteudo else 'Sem conteúdo adicional.'
        
        # Prepare visit info if available
        visit_info_html = ""
        visit_info_text = ""
        if relatorio.visita:
            date_format = "%d/%m/%Y às %H:%M"
            visit_date = relatorio.visita.data_realizada.strftime(date_format)
            visit_info_html = f'<p><strong>Visita relacionada:</strong> Visita realizada em {visit_date}</p>'
            visit_info_text = f'Visita relacionada: Visita realizada em {visit_date}'
        
        # Prepare approver info if available
        approver_html = f'<li><strong>Aprovador:</strong> {relatorio.aprovador_nome}</li>' if relatorio.aprovador_nome else ''
        approver_text = f'Aprovador: {relatorio.aprovador_nome}' if relatorio.aprovador_nome else ''
        
        html_body = f"""
        <html>
        <body>
            <h2>Relatório de Acompanhamento de Obra</h2>
            
            <p><strong>Caro(a) {nome_destinatario or 'Cliente'},</strong></p>
            
            <p>Segue em anexo o relatório de acompanhamento da obra:</p>
            
            <ul>
                <li><strong>Número do Relatório:</strong> {relatorio.numero}</li>
                <li><strong>Título:</strong> {relatorio.titulo}</li>
                <li><strong>Projeto:</strong> {relatorio.projeto.nome}</li>
                <li><strong>Data:</strong> {relatorio.data_relatorio.strftime('%d/%m/%Y')}</li>
                <li><strong>Autor:</strong> {relatorio.autor.nome_completo}</li>
                {approver_html}
            </ul>
            
            <h3>Conteúdo:</h3>
            <div style="border: 1px solid #ddd; padding: 15px; background-color: #f9f9f9;">
                {conteudo_html}
            </div>
            
            {visit_info_html}
            
            <hr>
            <p><small>Este é um email automático do Sistema de Acompanhamento de Visitas em Obras.</small></p>
        </body>
        </html>
        """
        
        text_body = f"""
        Relatório de Acompanhamento de Obra
        
        Caro(a) {nome_destinatario or 'Cliente'},
        
        Segue relatório de acompanhamento da obra:
        
        Número do Relatório: {relatorio.numero}
        Título: {relatorio.titulo}
        Projeto: {relatorio.projeto.nome}
        Data: {relatorio.data_relatorio.strftime('%d/%m/%Y')}
        Autor: {relatorio.autor.nome_completo}
        {approver_text}
        
        Conteúdo:
        {relatorio.conteudo or 'Sem conteúdo adicional.'}
        
        {visit_info_text}
        
        ---
        Este é um email automático do Sistema de Acompanhamento de Visitas em Obras.
        """
        
        msg = Message(
            subject=subject,
            recipients=[email_destinatario],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        raise e

def calculate_reimbursement_total(data):
    """Calculate total reimbursement amount from data dict"""
    total = 0
    quilometragem = data.get('quilometragem', 0) or 0
    valor_km = data.get('valor_km', 0) or 0
    total += quilometragem * valor_km
    total += data.get('alimentacao', 0) or 0
    total += data.get('hospedagem', 0) or 0
    total += data.get('outros_gastos', 0) or 0
    return round(total, 2)

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def format_currency(value):
    """Format currency for Brazilian Real"""
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def format_date_br(date_obj):
    """Format date in Brazilian format"""
    if date_obj is None:
        return ""
    return date_obj.strftime('%d/%m/%Y')

def format_datetime_br(datetime_obj):
    """Format datetime in Brazilian format"""
    if datetime_obj is None:
        return ""
    return datetime_obj.strftime('%d/%m/%Y às %H:%M')

# Template filters
def register_template_filters(app):
    """Register custom template filters"""
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['date_br'] = format_date_br
    app.jinja_env.filters['datetime_br'] = format_datetime_br

# Initialize default data on first run
def init_app_data():
    """Initialize application with default data"""
    from models import init_default_data
    init_default_data()
