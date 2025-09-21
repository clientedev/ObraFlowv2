
#!/usr/bin/env python3
"""
Script para recuperar imagens perdidas dos attached_assets
"""

import os
import shutil
from app import app, db
from models import FotoRelatorio, FotoRelatorioExpress

def recuperar_imagens_perdidas():
    """Recupera imagens perdidas dos attached_assets"""
    with app.app_context():
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        attached_assets_folder = 'attached_assets'
        
        print(f"🔍 Buscando imagens perdidas...")
        print(f"📁 Upload folder: {upload_folder}")
        print(f"📁 Attached assets: {attached_assets_folder}")
        
        # Criar pasta uploads se não existir
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            print(f"✅ Pasta {upload_folder} criada")
        
        recuperadas = 0
        nao_encontradas = 0
        
        # Processar fotos de relatórios normais
        print("\n📋 Processando relatórios normais...")
        fotos_normais = FotoRelatorio.query.all()
        
        for foto in fotos_normais:
            filename = foto.filename
            upload_path = os.path.join(upload_folder, filename)
            
            if not os.path.exists(upload_path):
                attached_path = os.path.join(attached_assets_folder, filename)
                
                if os.path.exists(attached_path):
                    try:
                        shutil.copy2(attached_path, upload_path)
                        print(f"✅ Recuperada: {filename} (relatório {foto.relatorio_id})")
                        recuperadas += 1
                    except Exception as e:
                        print(f"❌ Erro ao copiar {filename}: {str(e)}")
                        nao_encontradas += 1
                else:
                    print(f"❌ Não encontrada: {filename} (relatório {foto.relatorio_id})")
                    nao_encontradas += 1
        
        # Processar fotos de relatórios express
        print("\n🚀 Processando relatórios express...")
        fotos_express = FotoRelatorioExpress.query.all()
        
        for foto in fotos_express:
            filename = foto.filename
            upload_path = os.path.join(upload_folder, filename)
            
            if not os.path.exists(upload_path):
                attached_path = os.path.join(attached_assets_folder, filename)
                
                if os.path.exists(attached_path):
                    try:
                        shutil.copy2(attached_path, upload_path)
                        print(f"✅ Recuperada: {filename} (express {foto.relatorio_express_id})")
                        recuperadas += 1
                    except Exception as e:
                        print(f"❌ Erro ao copiar {filename}: {str(e)}")
                        nao_encontradas += 1
                else:
                    print(f"❌ Não encontrada: {filename} (express {foto.relatorio_express_id})")
                    nao_encontradas += 1
        
        print(f"\n📊 RESULTADO:")
        print(f"✅ Imagens recuperadas: {recuperadas}")
        print(f"❌ Imagens não encontradas: {nao_encontradas}")
        
        return recuperadas, nao_encontradas

if __name__ == "__main__":
    recuperadas, nao_encontradas = recuperar_imagens_perdidas()
    
    if recuperadas > 0:
        print(f"\n🎉 Sucesso! {recuperadas} imagens foram recuperadas!")
    
    if nao_encontradas > 0:
        print(f"\n⚠️ Atenção: {nao_encontradas} imagens permanecem perdidas.")
        print("💡 Verifique se os arquivos existem em 'attached_assets' ou se foram deletados permanentemente.")
