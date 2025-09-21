#!/usr/bin/env python3
"""Script para testar login e acesso à imagens"""

import requests
import sys
import os

def test_authenticated_image_access():
    session = requests.Session()
    
    # URL base
    base_url = "http://localhost:5000"
    
    # 1. Obter o formulário de login para pegar o CSRF token
    print("🔐 Fazendo login...")
    login_page = session.get(f"{base_url}/login")
    
    if login_page.status_code != 200:
        print(f"❌ Erro ao acessar página de login: {login_page.status_code}")
        return False
    
    # Buscar CSRF token no HTML (método simples)
    csrf_token = ""
    for line in login_page.text.split('\n'):
        if 'csrf_token' in line and 'value=' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break
    
    if not csrf_token:
        print("❌ CSRF token não encontrado")
        return False
    
    print(f"✅ CSRF token obtido: {csrf_token[:20]}...")
    
    # 2. Fazer login
    login_data = {
        'username': 'admin',
        'password': 'admin',
        'csrf_token': csrf_token
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=True)
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(f"Response: {login_response.text[:500]}")
        return False
    
    # Verificar se foi redirecionado para dashboard (indica sucesso)
    if 'dashboard' in login_response.url.lower() or 'login' not in login_response.url.lower():
        print("✅ Login realizado com sucesso!")
    else:
        print("❌ Login falhou - ainda na página de login")
        return False
    
    # 3. Testar acesso à imagem autenticada
    print("🖼️ Testando acesso à imagem com usuário autenticado...")
    image_url = f"{base_url}/uploads/0c02fd661f9e42cfbb33f6da6fda1294_WhatsApp_Image_2025-08-12_at_16.47.17.jpeg"
    
    image_response = session.head(image_url)
    print(f"Status da imagem: {image_response.status_code}")
    print(f"Content-Type: {image_response.headers.get('Content-Type', 'N/A')}")
    print(f"Content-Length: {image_response.headers.get('Content-Length', 'N/A')}")
    
    if image_response.status_code == 200:
        content_type = image_response.headers.get('Content-Type', '')
        if 'image' in content_type:
            print("✅ Imagem acessível com usuário autenticado!")
            return True
        else:
            print("⚠️ Resposta OK mas não é uma imagem real (placeholder)")
            return False
    else:
        print(f"❌ Erro ao acessar imagem: {image_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_authenticated_image_access()
    sys.exit(0 if success else 1)