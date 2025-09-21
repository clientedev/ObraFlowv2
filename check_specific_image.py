
#!/usr/bin/env python3
"""
Script para verificar uma imagem específica que está causando problema
"""

import os
from app import app, db
from models import FotoRelatorio, FotoRelatorioExpress

def check_specific_image():
    target_filename = "017050397c414b519d1df38fd32e78c8_1758143134942281964204884259198.jpg"
    
    with app.app_context():
        print(f"🔍 VERIFICANDO: {target_filename}")
        print("=" * 80)
        
        # Verificar no banco
        foto_relatorio = FotoRelatorio.query.filter_by(filename=target_filename).first()
        foto_express = FotoRelatorioExpress.query.filter_by(filename=target_filename).first()
        
        if foto_relatorio:
            print(f"📋 ENCONTRADA NO BANCO (Relatório {foto_relatorio.relatorio_id})")
            print(f"   Legenda: {foto_relatorio.legenda}")
            print(f"   Ordem: {foto_relatorio.ordem}")
        
        if foto_express:
            print(f"📋 ENCONTRADA NO BANCO (Express {foto_express.relatorio_express_id})")
            print(f"   Legenda: {foto_express.legenda}")
        
        if not foto_relatorio and not foto_express:
            print("❌ NÃO ENCONTRADA NO BANCO")
            return
        
        # Verificar no filesystem
        upload_path = os.path.join('uploads', target_filename)
        attached_path = os.path.join('attached_assets', target_filename)
        
        print(f"\n📁 VERIFICANDO FILESYSTEM:")
        print(f"   uploads/{target_filename}: {'✅ EXISTE' if os.path.exists(upload_path) else '❌ NÃO EXISTE'}")
        print(f"   attached_assets/{target_filename}: {'✅ EXISTE' if os.path.exists(attached_path) else '❌ NÃO EXISTE'}")
        
        # Se existe em attached_assets mas não em uploads, copiar
        if os.path.exists(attached_path) and not os.path.exists(upload_path):
            try:
                import shutil
                if not os.path.exists('uploads'):
                    os.makedirs('uploads')
                shutil.copy2(attached_path, upload_path)
                print(f"✅ COPIADA DE attached_assets PARA uploads")
            except Exception as e:
                print(f"❌ ERRO AO COPIAR: {e}")

if __name__ == "__main__":
    check_specific_image()
