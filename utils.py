import requests
import json

def get_address_from_coordinates(latitude, longitude):
    """Convert GPS coordinates to readable address using OpenStreetMap Nominatim API"""
    try:
        if not latitude or not longitude:
            return None
            
        # Use OpenStreetMap Nominatim API (free, no API key required)
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': float(latitude),
            'lon': float(longitude),
            'addressdetails': 1,
            'language': 'pt-BR'
        }
        
        headers = {
            'User-Agent': 'ConstructionSiteReporting/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'display_name' in data:
                # Extract key address components
                address_parts = []
                
                if 'address' in data:
                    addr = data['address']
                    
                    # Street number and name
                    street_parts = []
                    if 'house_number' in addr:
                        street_parts.append(addr['house_number'])
                    if 'road' in addr:
                        street_parts.append(addr['road'])
                    elif 'pedestrian' in addr:
                        street_parts.append(addr['pedestrian'])
                    
                    if street_parts:
                        address_parts.append(' '.join(street_parts))
                    
                    # Neighborhood
                    if 'neighbourhood' in addr:
                        address_parts.append(addr['neighbourhood'])
                    elif 'suburb' in addr:
                        address_parts.append(addr['suburb'])
                    
                    # City
                    if 'city' in addr:
                        address_parts.append(addr['city'])
                    elif 'town' in addr:
                        address_parts.append(addr['town'])
                    elif 'municipality' in addr:
                        address_parts.append(addr['municipality'])
                    
                    # State
                    if 'state' in addr:
                        address_parts.append(addr['state'])
                    
                    # Country
                    if 'country' in addr:
                        address_parts.append(addr['country'])
                
                if address_parts:
                    return ', '.join(address_parts)
                else:
                    return data['display_name']
        
        return None
        
    except Exception as e:
        print(f"Error converting coordinates to address: {e}")
        return None

def format_coordinates_display(latitude, longitude):
    """Format coordinates for display with address lookup"""
    try:
        if not latitude or not longitude:
            return "Localização não capturada"
        
        # Try to get readable address
        address = get_address_from_coordinates(latitude, longitude)
        
        if address:
            return f"{address}\n(Coordenadas: {latitude}, {longitude})"
        else:
            return f"Latitude: {latitude}, Longitude: {longitude}"
            
    except Exception as e:
        print(f"Error formatting coordinates: {e}")
        return f"Latitude: {latitude}, Longitude: {longitude}"

# Utility functions for number generation
def generate_project_number():
    """Generate sequential project number"""
    from models import Projeto
    from app import db
    
    try:
        last_project = Projeto.query.order_by(Projeto.id.desc()).first()
        if last_project:
            # Extract number from existing format like "PROJ-0001"
            if last_project.numero and 'PROJ-' in last_project.numero:
                try:
                    last_num = int(last_project.numero.split('-')[1])
                    return f"PROJ-{last_num + 1:04d}"
                except:
                    pass
        
        # Default start
        return "PROJ-0001"
    except:
        return "PROJ-0001"

def generate_report_number():
    """Generate sequential report number"""
    from models import Relatorio
    from app import db
    
    try:
        last_report = Relatorio.query.order_by(Relatorio.id.desc()).first()
        if last_report:
            # Extract number from existing format like "REL-0001"
            if last_report.numero and 'REL-' in last_report.numero:
                try:
                    last_num = int(last_report.numero.split('-')[1])
                    return f"REL-{last_num + 1:04d}"
                except:
                    pass
        
        # Default start
        return "REL-0001"
    except:
        return "REL-0001"

def generate_visit_number():
    """Generate sequential visit number"""
    from models import Visita
    from app import db
    
    try:
        last_visit = Visita.query.order_by(Visita.id.desc()).first()
        if last_visit:
            # Extract number from existing format like "VIS-0001"
            if last_visit.numero and 'VIS-' in last_visit.numero:
                try:
                    last_num = int(last_visit.numero.split('-')[1])
                    return f"VIS-{last_num + 1:04d}"
                except:
                    pass
        
        # Default start
        return "VIS-0001"
    except:
        return "VIS-0001"

def send_report_email(report, email, name):
    """Send report via email"""
    from flask import current_app
    from flask_mail import Message, Mail
    
    try:
        mail = Mail(current_app)
        
        msg = Message(
            subject=f'Relatório {report.numero} - {report.projeto.nome if report.projeto else "Projeto"}',
            recipients=[email],
            body=f"""
Olá {name},

Segue em anexo o relatório {report.numero}.

Projeto: {report.projeto.nome if report.projeto else "Não informado"}
Data: {report.data_relatorio.strftime('%d/%m/%Y') if report.data_relatorio else "Não informada"}

Atenciosamente,
Sistema de Relatórios
"""
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def calculate_reimbursement_total(reembolso):
    """Calculate total reimbursement amount"""
    try:
        total = 0
        
        # Kilometragem
        if reembolso.quilometragem and reembolso.valor_km:
            total += reembolso.quilometragem * reembolso.valor_km
        
        # Other expenses
        if reembolso.alimentacao:
            total += reembolso.alimentacao
        if reembolso.hospedagem:
            total += reembolso.hospedagem
        if reembolso.outros_gastos:
            total += reembolso.outros_gastos
        
        return total
    except:
        return 0