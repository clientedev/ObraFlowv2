"""
Script para verificar como as fotos são armazenadas no banco
e onde os arquivos realmente estão
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:KgyYkEmMztCNMSPHVbOpWLTiKZFXYwpB@switchback.proxy.rlwy.net:17107/railway'

from app import app, db
from models import FotoRelatorio, FotoRelatorioExpress

with app.app_context():
    print("\n🔍 INVESTIGAÇÃO DE CAMINHOS DE FOTOS")
    print("=" * 80)
    
    # Pegar 10 fotos de amostra
    fotos_sample = FotoRelatorio.query.limit(10).all()
    
    print(f"\n📷 Primeiras 10 fotos de FotoRelatorio:")
    print("-" * 80)
    
    for foto in fotos_sample:
        filename = foto.filename or foto.filename_original or foto.filename_anotada
        
        if filename:
            # Testar vários caminhos possíveis
            paths_to_check = [
                f"uploads/{filename}",
                f"uploads/{os.path.basename(filename)}",
                filename,  # Caminho absoluto?
                f"static/{filename}",
                f"static/uploads/{filename}",
            ]
            
            found = False
            found_path = None
            
            for path in paths_to_check:
                if os.path.exists(path):
                    found = True
                    found_path = path
                    break
            
            status = "✅ ENCONTRADA" if found else "❌ NÃO ENCONTRADA"
            print(f"\nFoto ID {foto.id}:")
            print(f"  Filename no banco: {filename[:80]}")
            print(f"  Status: {status}")
            if found:
                print(f"  Caminho real: {found_path}")
                print(f"  Tamanho: {os.path.getsize(found_path)} bytes")
    
    # Verificar fotos express também
    print("\n" + "=" * 80)
    print(f"\n⚡ Primeiras 10 fotos de FotoRelatorioExpress:")
    print("-" * 80)
    
    fotos_express_sample = FotoRelatorioExpress.query.limit(10).all()
    
    for foto in fotos_express_sample:
        filename = foto.filename or foto.filename_original or foto.filename_anotada
        
        if filename:
            paths_to_check = [
                f"uploads/{filename}",
                f"uploads/{os.path.basename(filename)}",
                filename,
                f"static/{filename}",
                f"static/uploads/{filename}",
            ]
            
            found = False
            found_path = None
            
            for path in paths_to_check:
                if os.path.exists(path):
                    found = True
                    found_path = path
                    break
            
            status = "✅ ENCONTRADA" if found else "❌ NÃO ENCONTRADA"
            print(f"\nFoto ID {foto.id}:")
            print(f"  Filename no banco: {filename[:80]}")
            print(f"  Status: {status}")
            if found:
                print(f"  Caminho real: {found_path}")
                print(f"  Tamanho: {os.path.getsize(found_path)} bytes")
    
    print("\n" + "=" * 80)
