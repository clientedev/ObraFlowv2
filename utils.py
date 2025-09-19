import requests
import re
import json

def get_address_from_coordinates(latitude, longitude):
    """Convert GPS coordinates to readable address using OpenStreetMap Nominatim API"""
    import time
    
    try:
        if not latitude or not longitude:
            return None
        
        # Railway-compatible headers
        headers = {
            'User-Agent': 'ELP-ConstructionTracker/1.0 (elp.contato@gmail.com)',
            'Accept': 'application/json',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
        }
        
        # Rate limiting
        time.sleep(1.2)
        
        # Use OpenStreetMap Nominatim API (free, no API key required)
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': float(latitude),
            'lon': float(longitude),
            'addressdetails': 1,
            'language': 'pt-BR'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
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
            
            elif response.status_code == 429:
                print(f"⚠️  REVERSE GEOCODING: Rate limited")
            elif response.status_code == 403:
                print(f"❌ REVERSE GEOCODING: Blocked by Nominatim")
            else:
                print(f"⚠️  REVERSE GEOCODING: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⚠️  REVERSE GEOCODING: Timeout")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  REVERSE GEOCODING: Connection error")
        
        return None
        
    except Exception as e:
        print(f"❌ REVERSE GEOCODING: Erro: {e}")
        return None

def normalize_address(address):
    """Normalize address by expanding common abbreviations"""
    if not address or not isinstance(address, str):
        return address
    
    # Dictionary of common Brazilian address abbreviations
    rules = {
        # Street types
        r'\bR\s+': 'Rua ',
        r'\bR\.': 'Rua',
        r'\bAv\s+': 'Avenida ',
        r'\bAv\.': 'Avenida',
        r'\bPç\s+': 'Praça ',
        r'\bPça\s+': 'Praça ',
        r'\bPç\.': 'Praça',
        r'\bPça\.': 'Praça',
        r'\bRod\.': 'Rodovia',
        r'\bEstr\.': 'Estrada',
        r'\bAl\.': 'Alameda',
        r'\bTv\.': 'Travessa',
        r'\bVl\.': 'Vila',
        r'\bJd\.': 'Jardim',
        r'\bPq\.': 'Parque',
        r'\bCj\.': 'Conjunto',
        r'\bRes\.': 'Residencial',
        r'\bBl\.': 'Bloco',
        r'\bQt\.': 'Quadra',
        r'\bLt\.': 'Lote',
    }
    
    normalized = address.strip()
    original = normalized
    
    # Apply normalization rules
    for pattern, replacement in rules.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Log transformation if there was a change
    if original != normalized:
        print(f"📍 ENDEREÇO NORMALIZADO: '{original}' → '{normalized}'")
    
    return normalized


def get_coordinates_from_address(address):
    """Convert address to GPS coordinates using OpenStreetMap Nominatim API"""
    import time
    import os
    
    try:
        if not address or not address.strip():
            return None, None
        
        # Railway-compatible headers and rate limiting
        headers = {
            'User-Agent': 'ELP-ConstructionTracker/1.0 (elp.contato@gmail.com)',
            'Accept': 'application/json',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
        }
        
        # Rate limiting: Nominatim requires 1 second between requests
        time.sleep(1.2)
        
        # Use OpenStreetMap Nominatim API for forward geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': normalize_address(address),
            'format': 'json',
            'addressdetails': 1,
            'language': 'pt-BR',
            'countrycodes': 'br',  # Limit to Brazil for better accuracy
            'limit': 1,
            'dedupe': 1  # Remove duplicates
        }
        
        # Retry logic for Railway deployment
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=15  # Increased timeout for Railway
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data and len(data) > 0:
                        result = data[0]
                        latitude = float(result['lat'])
                        longitude = float(result['lon'])
                        
                        print(f"✅ GEOCODING: {normalize_address(address)} → {latitude}, {longitude}")
                        return latitude, longitude
                        
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    print(f"⚠️  GEOCODING: Rate limited, waiting...")
                    time.sleep(5)
                    continue
                    
                elif response.status_code == 403:
                    # Forbidden - likely blocked
                    print(f"❌ GEOCODING: Blocked by Nominatim (403)")
                    break
                    
                else:
                    print(f"⚠️  GEOCODING: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"⚠️  GEOCODING: Timeout, tentativa {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            except requests.exceptions.ConnectionError:
                print(f"⚠️  GEOCODING: Connection error, tentativa {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except Exception as e:
                print(f"❌ GEOCODING: Erro inesperado: {e}")
                break
        
        print(f"❌ GEOCODING: Falhou para '{address}' após {max_retries} tentativas")
        return None, None
        
    except Exception as e:
        print(f"❌ GEOCODING: Erro crítico: {e}")
        return None, None

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
        # Buscar todos os relatórios com números no formato REL-XXXX
        relatorios = Relatorio.query.filter(Relatorio.numero.like('REL-%')).all()
        
        max_num = 0
        for relatorio in relatorios:
            if relatorio.numero and 'REL-' in relatorio.numero:
                try:
                    num = int(relatorio.numero.split('-')[1])
                    if num > max_num:
                        max_num = num
                except:
                    continue
        
        # Retornar próximo número disponível
        return f"REL-{max_num + 1:04d}"
        
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