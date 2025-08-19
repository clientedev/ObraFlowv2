#!/usr/bin/env python3
"""
Script para testar e aplicar as correções do sistema
"""

import requests
import json

def test_gps_api():
    """Testa a API de GPS para endereços formatados"""
    url = "http://localhost:5000/get_location"
    data = {
        "latitude": -23.5505,
        "longitude": -46.6333
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"GPS API Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"GPS Response: {result}")
            return result.get('endereco', 'ERRO')
        else:
            print(f"GPS Error: {response.text}")
            return None
    except Exception as e:
        print(f"GPS Exception: {e}")
        return None

def test_nearby_projects():
    """Testa a API de projetos próximos"""
    url = "http://localhost:5000/api/projects/nearby"
    data = {
        "lat": -23.5505,
        "lon": -46.6333
    }
    
    try:
        # Need to simulate authenticated request
        response = requests.post(url, json=data, timeout=10)
        print(f"Nearby API Status: {response.status_code}")
        print(f"Nearby Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Nearby Exception: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTANDO CORREÇÕES ===")
    
    print("\n1. Testando GPS para endereços formatados:")
    endereco = test_gps_api()
    if endereco and "Lat:" not in endereco:
        print("✓ GPS retorna endereço formatado")
    else:
        print("✗ GPS ainda retorna coordenadas")
    
    print("\n2. Testando API de projetos próximos:")
    if test_nearby_projects():
        print("✓ API de projetos próximos funcionando")
    else:
        print("✗ API de projetos próximos com erro")
    
    print("\n=== TESTE CONCLUÍDO ===")