
#!/usr/bin/env python3
"""
Script de diagnóstico para verificar imagens específicas
Executa verificações detalhadas do sistema de imagens
"""

import os
import sys
from app import app, db

def verificar_imagem_especifica(filename):
    """Verificar uma imagem específica em detalhes"""
    print(f"\n🔍 DIAGNÓSTICO DETALHADO: {filename}")
    print("=" * 60)
    
    # Verificar pastas
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    attached_assets = 'attached_assets'
    
    paths_to_check = [
        os.path.join(upload_folder, filename),
        os.path.join(attached_assets, filename),
        os.path.join('static', 'uploads', filename),
        os.path.join('static', 'img', filename)
    ]
    
    print(f"📁 Pasta uploads configurada: {upload_folder}")
    print(f"📂 Verificando {len(paths_to_check)} localizações:\n")
    
    found_files = []
    
    for path in paths_to_check:
        exists = os.path.exists(path)
        status = "✅ EXISTE" if exists else "❌ NÃO EXISTE"
        print(f"   {status}: {path}")
        
        if exists:
            size = os.path.getsize(path)
            print(f"      📊 Tamanho: {size:,} bytes")
            found_files.append((path, size))
    
    print(f"\n📋 RESUMO:")
    print(f"   🔍 Arquivo procurado: {filename}")
    print(f"   ✅ Encontrado em: {len(found_files)} localizações")
    
    if found_files:
        print(f"   📍 Localizações encontradas:")
        for path, size in found_files:
            print(f"      - {path} ({size:,} bytes)")
        
        # Verificar se há diferenças de tamanho
        sizes = set(size for _, size in found_files)
        if len(sizes) > 1:
            print(f"   ⚠️ ATENÇÃO: Arquivos com tamanhos diferentes encontrados!")
        else:
            print(f"   ✅ Todos os arquivos têm o mesmo tamanho")
    else:
        print(f"   ❌ Arquivo não encontrado em nenhuma localização")
    
    return found_files

def listar_imagens_uploads():
    """Listar todas as imagens na pasta uploads"""
    print(f"\n📂 LISTAGEM DA PASTA UPLOADS:")
    print("=" * 60)
    
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    
    if not os.path.exists(upload_folder):
        print(f"❌ Pasta uploads não existe: {upload_folder}")
        return []
    
    arquivos = []
    for filename in os.listdir(upload_folder):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            filepath = os.path.join(upload_folder, filename)
            size = os.path.getsize(filepath)
            arquivos.append((filename, size))
    
    arquivos.sort()
    
    print(f"📊 Total de imagens: {len(arquivos)}")
    print(f"📁 Pasta: {upload_folder}\n")
    
    for filename, size in arquivos[:20]:  # Primeiros 20
        print(f"   📄 {filename} ({size:,} bytes)")
    
    if len(arquivos) > 20:
        print(f"   ... e mais {len(arquivos) - 20} arquivos")
    
    return arquivos

def verificar_banco_dados():
    """Verificar registros de imagens no banco"""
    print(f"\n🗃️ VERIFICAÇÃO DO BANCO DE DADOS:")
    print("=" * 60)
    
    try:
        with app.app_context():
            from models import FotoRelatorio, FotoRelatorioExpress
            
            # Fotos de relatórios normais
            fotos_normais = FotoRelatorio.query.count()
            print(f"📋 Fotos de relatórios normais: {fotos_normais}")
            
            # Fotos de relatórios express
            fotos_express = FotoRelatorioExpress.query.count()
            print(f"📋 Fotos de relatórios express: {fotos_express}")
            
            print(f"📊 Total de fotos no banco: {fotos_normais + fotos_express}")
            
            # Verificar algumas fotos específicas
            print(f"\n🔍 Últimas 10 fotos cadastradas:")
            ultimas_fotos = FotoRelatorio.query.order_by(FotoRelatorio.created_at.desc()).limit(10).all()
            
            for foto in ultimas_fotos:
                print(f"   📷 {foto.filename} (Relatório {foto.relatorio_id})")
                
    except Exception as e:
        print(f"❌ Erro ao acessar banco: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        verificar_imagem_especifica(filename)
    else:
        print("🔍 DIAGNÓSTICO COMPLETO DO SISTEMA DE IMAGENS")
        print("=" * 80)
        
        # Verificar configurações
        print(f"📁 UPLOAD_FOLDER configurado: {app.config.get('UPLOAD_FOLDER', 'uploads')}")
        
        # Listar imagens
        listar_imagens_uploads()
        
        # Verificar banco
        verificar_banco_dados()
        
        print(f"\n💡 Para verificar uma imagem específica:")
        print(f"   python diagnostic_image_check.py nome_do_arquivo.jpg")
