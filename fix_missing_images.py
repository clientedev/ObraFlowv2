
#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir imagens perdidas
"""

import os
import sys
from app import app, db
from models import FotoRelatorio, FotoRelatorioExpress
import shutil
from datetime import datetime

def find_missing_images():
    """Encontrar imagens registradas no banco mas ausentes no filesystem"""
    with app.app_context():
        missing_images = []
        
        # Verificar FotoRelatorio
        fotos_relatorio = FotoRelatorio.query.all()
        for foto in fotos_relatorio:
            if not check_file_exists(foto.filename):
                missing_images.append({
                    'type': 'relatorio',
                    'id': foto.id,
                    'filename': foto.filename,
                    'relatorio_id': foto.relatorio_id,
                    'legenda': foto.legenda
                })
        
        # Verificar FotoRelatorioExpress  
        fotos_express = FotoRelatorioExpress.query.all()
        for foto in fotos_express:
            if not check_file_exists(foto.filename):
                missing_images.append({
                    'type': 'express',
                    'id': foto.id,
                    'filename': foto.filename,
                    'relatorio_express_id': foto.relatorio_express_id,
                    'legenda': foto.legenda
                })
        
        return missing_images

def check_file_exists(filename):
    """Verificar se arquivo existe em qualquer diretório"""
    search_dirs = ['uploads', 'attached_assets', 'static/uploads', 'static/img']
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                if filename in files:
                    return True
    return False

def find_similar_files(target_filename):
    """Encontrar arquivos similares ao arquivo alvo"""
    base_pattern = target_filename[:30]
    similar_files = []
    
    search_dirs = ['uploads', 'attached_assets', 'static/uploads', 'static/img']
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if (base_pattern in file and 
                        file.lower().endswith(('.jpg', '.jpeg', '.png')) and
                        file != target_filename):
                        similar_files.append({
                            'file': file,
                            'path': os.path.join(root, file),
                            'similarity': len(set(target_filename) & set(file)) / len(set(target_filename) | set(file))
                        })
    
    return sorted(similar_files, key=lambda x: x['similarity'], reverse=True)

def fix_specific_image():
    """Corrigir especificamente a imagem problemática"""
    target_filename = "017050397c414b519d1df38fd32e78c8_1758143134942281964204884259198.jpg"
    
    print(f"🔍 Buscando por: {target_filename}")
    
    # Verificar se existe
    if check_file_exists(target_filename):
        print(f"✅ Arquivo já existe!")
        return True
    
    # Buscar similares
    similar_files = find_similar_files(target_filename)
    
    if similar_files:
        print(f"🎯 Encontrados {len(similar_files)} arquivos similares:")
        for i, similar in enumerate(similar_files[:5]):
            print(f"   {i+1}. {similar['file']} (similaridade: {similar['similarity']:.2f})")
        
        # Usar o mais similar
        best_match = similar_files[0]
        if best_match['similarity'] > 0.8:
            print(f"🔧 Copiando {best_match['file']} para {target_filename}")
            
            # Copiar arquivo para uploads
            uploads_dir = 'uploads'
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            
            target_path = os.path.join(uploads_dir, target_filename)
            shutil.copy2(best_match['path'], target_path)
            
            print(f"✅ Arquivo copiado com sucesso!")
            return True
    
    print(f"❌ Não foi possível corrigir automaticamente")
    return False

if __name__ == "__main__":
    print("🚀 Diagnóstico de Imagens Perdidas")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--fix-specific':
        fix_specific_image()
    else:
        missing = find_missing_images()
        print(f"📊 Encontradas {len(missing)} imagens perdidas")
        
        for img in missing[:10]:  # Mostrar apenas as primeiras 10
            print(f"   📄 {img['filename']} ({img['type']})")
        
        if len(missing) > 10:
            print(f"   ... e mais {len(missing) - 10} imagens")
        
        print(f"\n💡 Para corrigir a imagem específica, execute:")
        print(f"   python fix_missing_images.py --fix-specific")
