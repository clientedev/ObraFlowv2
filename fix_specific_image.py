
<line_number>1</line_number>
#!/usr/bin/env python3
"""
Script para buscar especificamente a imagem que está dando erro
"""

import os
import re

def find_specific_image():
    """Busca pela imagem específica que está dando erro"""
    
    # Padrão da imagem baseado no erro
    target_pattern = "017050397c414b519d1df38fd32e78c8"
    
    print(f"🔍 Buscando por imagem com padrão: {target_pattern}")
    
    # Diretórios para buscar
    search_dirs = [
        'uploads',
        'attached_assets', 
        'static',
        '.'  # Diretório atual
    ]
    
    found_files = []
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            print(f"📁 Buscando em: {search_dir}")
            
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    # Buscar por padrão no nome do arquivo
                    if target_pattern in file:
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)
                        print(f"✅ ENCONTRADO: {full_path}")
                    
                    # Buscar por arquivos com timestamp similar
                    elif "1758143" in file or "_1758" in file:
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)
                        print(f"🔍 SIMILAR: {full_path}")
    
    if not found_files:
        print("❌ Arquivo não encontrado. Listando todos os arquivos de imagem recentes...")
        
        # Listar todas as imagens recentes
        for search_dir in ['uploads', 'attached_assets']:
            if os.path.exists(search_dir):
                print(f"\n📁 Imagens em {search_dir}:")
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            full_path = os.path.join(root, file)
                            # Mostrar apenas arquivos recentes (com timestamp alto)
                            if "1758" in file:
                                print(f"   📄 {file}")
    
    return found_files

def check_uploads_vs_attached():
    """Compara arquivos entre uploads e attached_assets"""
    print("\n🔄 Comparando uploads vs attached_assets...")
    
    uploads_files = set()
    attached_files = set()
    
    # Listar uploads
    if os.path.exists('uploads'):
        for file in os.listdir('uploads'):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                uploads_files.add(file)
    
    # Listar attached_assets recursivamente
    if os.path.exists('attached_assets'):
        for root, dirs, files in os.walk('attached_assets'):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    attached_files.add(file)
    
    # Arquivos apenas em attached_assets
    only_in_attached = attached_files - uploads_files
    
    if only_in_attached:
        print(f"📋 {len(only_in_attached)} imagens apenas em attached_assets:")
        for file in sorted(only_in_attached):
            if "1758" in file:  # Mostrar apenas arquivos recentes
                print(f"   📄 {file}")

if __name__ == "__main__":
    print("🚀 Busca Específica de Imagem Perdida")
    print("=" * 40)
    
    found = find_specific_image()
    check_uploads_vs_attached()
    
    if found:
        print(f"\n✅ {len(found)} arquivo(s) encontrado(s)!")
    else:
        print(f"\n❌ Arquivo específico não encontrado.")
        print("💡 Execute o recovery_script.py para busca completa")
