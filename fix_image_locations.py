
#!/usr/bin/env python3
"""
Script para corrigir localização das imagens e sincronizar com o banco
"""

import os
import shutil
import logging
from app import app, db
from models import FotoRelatorio, FotoRelatorioExpress

logging.basicConfig(level=logging.INFO)

def fix_image_locations():
    """Migrar e corrigir localização das imagens"""
    
    with app.app_context():
        print("🔧 Iniciando correção de localização de imagens...")
        
        # Diretórios
        uploads_dir = app.config.get('UPLOAD_FOLDER', 'uploads')
        attached_assets_dir = 'attached_assets'
        
        # Garantir que uploads existe
        os.makedirs(uploads_dir, exist_ok=True)
        
        stats = {
            'migradas': 0,
            'ja_existem': 0,
            'nao_encontradas': 0,
            'erros': 0
        }
        
        # Buscar todas as fotos do banco
        fotos_normais = FotoRelatorio.query.all()
        fotos_express = FotoRelatorioExpress.query.all()
        
        todas_fotos = []
        for foto in fotos_normais:
            todas_fotos.append(('normal', foto.filename, foto.relatorio_id))
        
        for foto in fotos_express:
            todas_fotos.append(('express', foto.filename, foto.relatorio_express_id))
        
        print(f"📊 Total de fotos no banco: {len(todas_fotos)}")
        
        # Processar cada foto
        for tipo, filename, relatorio_id in todas_fotos:
            try:
                uploads_path = os.path.join(uploads_dir, filename)
                attached_path = os.path.join(attached_assets_dir, filename)
                
                # Se já existe em uploads, pular
                if os.path.exists(uploads_path):
                    stats['ja_existem'] += 1
                    continue
                
                # Se existe em attached_assets, migrar
                if os.path.exists(attached_path):
                    shutil.copy2(attached_path, uploads_path)
                    stats['migradas'] += 1
                    print(f"📤 MIGRADA: {filename} ({tipo} #{relatorio_id})")
                else:
                    # Buscar recursivamente em attached_assets
                    encontrada = False
                    if os.path.exists(attached_assets_dir):
                        for root, dirs, files in os.walk(attached_assets_dir):
                            if filename in files:
                                source_path = os.path.join(root, filename)
                                shutil.copy2(source_path, uploads_path)
                                stats['migradas'] += 1
                                print(f"📤 MIGRADA DE SUBDIR: {filename} ({root})")
                                encontrada = True
                                break
                    
                    if not encontrada:
                        stats['nao_encontradas'] += 1
                        print(f"❌ NÃO ENCONTRADA: {filename} ({tipo} #{relatorio_id})")
                        
            except Exception as e:
                stats['erros'] += 1
                print(f"💥 ERRO: {filename} - {str(e)}")
        
        print("\n📊 RELATÓRIO FINAL:")
        print(f"   📤 Migradas: {stats['migradas']}")
        print(f"   ✅ Já existiam: {stats['ja_existem']}")
        print(f"   ❌ Não encontradas: {stats['nao_encontradas']}")
        print(f"   💥 Erros: {stats['erros']}")
        
        # Verificar diretório uploads
        uploads_count = 0
        if os.path.exists(uploads_dir):
            for file in os.listdir(uploads_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    uploads_count += 1
        
        print(f"\n📁 Arquivos em uploads/: {uploads_count}")
        
        return stats

if __name__ == '__main__':
    stats = fix_image_locations()
    print(f"\n🎉 Concluído! {stats['migradas']} imagens migradas.")
