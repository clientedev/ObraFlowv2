#!/usr/bin/env python3
"""
Test script to verify Express Report photo upload functionality end-to-end.
This script simulates a user uploading photos to an express report.
"""

import requests
import base64
import json
from io import BytesIO
from PIL import Image

# Configuration
BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
EXPRESS_NEW_URL = f"{BASE_URL}/express/novo"

# Test credentials (using admin account)
USERNAME = "admin"
PASSWORD = "elp1212"

def create_test_image(text="TEST PHOTO", size=(800, 600)):
    """Create a simple test image with text"""
    img = Image.new('RGB', size, color='lightblue')
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_bytes = buffer.read()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}", img_bytes

def test_photo_upload():
    """Test the complete photo upload flow"""
    
    print("=" * 80)
    print("🧪 TESTE DE UPLOAD DE FOTOS - EXPRESS REPORT")
    print("=" * 80)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Login
    print("\n1️⃣ Fazendo login...")
    login_data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    
    response = session.post(LOGIN_URL, data=login_data, allow_redirects=False)
    
    if response.status_code not in [200, 302]:
        print(f"❌ ERRO no login: {response.status_code}")
        return False
    
    print("✅ Login bem-sucedido")
    
    # Step 2: Get the form page to extract CSRF token
    print("\n2️⃣ Acessando formulário de novo relatório...")
    response = session.get(EXPRESS_NEW_URL)
    
    if response.status_code != 200:
        print(f"❌ ERRO ao acessar formulário: {response.status_code}")
        return False
    
    # Extract CSRF token from the page
    html_content = response.text
    csrf_token = None
    
    # Simple extraction (you may need to adjust this)
    if 'csrf_token' in html_content:
        import re
        match = re.search(r'name="csrf_token".*?value="([^"]+)"', html_content)
        if match:
            csrf_token = match.group(1)
    
    print(f"✅ Formulário acessado (CSRF token: {'encontrado' if csrf_token else 'não encontrado'})")
    
    # Step 3: Create test photos
    print("\n3️⃣ Criando fotos de teste...")
    
    photo1_base64, photo1_bytes = create_test_image("FOTO TESTE 1")
    photo2_base64, photo2_bytes = create_test_image("FOTO TESTE 2")
    
    foto_configuracoes = [
        {
            "data": photo1_base64,
            "legenda": "Foto de teste automatizada 1",
            "categoria": "Teste",
            "local": "",
            "originalName": "test_photo_1.png"
        },
        {
            "data": photo2_base64,
            "legenda": "Foto de teste automatizada 2", 
            "categoria": "Teste",
            "local": "",
            "originalName": "test_photo_2.png"
        }
    ]
    
    print(f"✅ 2 fotos de teste criadas (tamanho: {len(photo1_bytes)} bytes cada)")
    
    # Step 4: Submit the form
    print("\n4️⃣ Submetendo relatório com fotos...")
    
    form_data = {
        'csrf_token': csrf_token,
        'obra': '1',  # Assuming obra ID 1 exists
        'data_visita': '2025-11-21',
        'tipo': 'Visita Técnica',
        'observacoes_gerais': 'Relatório de teste automatizado para verificar upload de fotos',
        'foto_configuracoes': json.dumps(foto_configuracoes),
        'checklist_completo': '[]'
    }
    
    response = session.post(EXPRESS_NEW_URL, data=form_data, allow_redirects=False)
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Formulário enviado com sucesso (redirecionamento)")
        redirect_url = response.headers.get('Location', '')
        print(f"   Redirecionando para: {redirect_url}")
        
        # Step 5: Verify in database
        print("\n5️⃣ Verificando no banco de dados...")
        
        # Import database connection
        import sys
        sys.path.insert(0, '.')
        from app import app
        from models import db, RelatorioExpress, FotoRelatorioExpress
        
        with app.app_context():
            # Get the most recent express report
            latest_report = RelatorioExpress.query.order_by(RelatorioExpress.id.desc()).first()
            
            if latest_report:
                print(f"✅ Relatório encontrado: ID={latest_report.id}")
                
                # Check for photos
                photos = FotoRelatorioExpress.query.filter_by(
                    relatorio_express_id=latest_report.id
                ).all()
                
                print(f"✅ Fotos encontradas: {len(photos)}")
                
                if len(photos) > 0:
                    for i, photo in enumerate(photos, 1):
                        print(f"\n   Foto {i}:")
                        print(f"   - ID: {photo.id}")
                        print(f"   - Filename: {photo.filename}")
                        print(f"   - Legenda: {photo.legenda}")
                        print(f"   - Categoria: {photo.tipo_servico}")
                        print(f"   - Tamanho: {len(photo.imagem) if photo.imagem else 0} bytes")
                        print(f"   - Hash: {photo.imagem_hash}")
                    
                    print("\n" + "=" * 80)
                    print("✅✅✅ TESTE BEM-SUCEDIDO! FOTOS FORAM SALVAS NO BANCO! ✅✅✅")
                    print("=" * 80)
                    return True
                else:
                    print("\n" + "=" * 80)
                    print("❌❌❌ TESTE FALHOU! NENHUMA FOTO FOI SALVA! ❌❌❌")
                    print("=" * 80)
                    return False
            else:
                print("❌ Nenhum relatório encontrado")
                return False
                
    elif response.status_code == 200:
        print("⚠️ Formulário retornou 200 (possível erro de validação)")
        print("Resposta:")
        print(response.text[:500])
        return False
    else:
        print(f"❌ ERRO ao enviar formulário: {response.status_code}")
        return False

if __name__ == "__main__":
    try:
        success = test_photo_upload()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
