"""
Script para debugar o backup de fotos
Verificar quantos relatórios aprovados existem e se as fotos existem no disco
"""
import os
import sys

# Configurar o ambiente
os.environ['DATABASE_URL'] = 'postgresql://postgres:KgyYkEmMztCNMSPHVbOpWLTiKZFXYwpB@switchback.proxy.rlwy.net:17107/railway'

from app import app, db
from models import Relatorio, FotoRelatorio, RelatorioExpress, FotoRelatorioExpress, Projeto
from sqlalchemy import func

with app.app_context():
    print("=" * 80)
    print("VERIFICAÇÃO DO BANCO DE DADOS - BACKUP DE FOTOS")
    print("=" * 80)
    
    # 1. Verificar relatórios aprovados (case-insensitive)
    print("\n📊 RELATÓRIOS COMUNS:")
    relatorios_aprovados = Relatorio.query.filter(
        func.lower(Relatorio.status).in_(['aprovado', 'finalizado', 'aprovado final'])
    ).all()
    
    print(f"   Total de relatórios aprovados: {len(relatorios_aprovados)}")
    
    if relatorios_aprovados:
        print(f"\n   Primeiros 5 relatórios:")
        for rel in relatorios_aprovados[:5]:
            projeto_nome = rel.projeto.nome if rel.projeto else 'Sem Projeto'
            print(f"   - ID: {rel.id}, Número: {rel.numero}, Status: {rel.status}, Projeto: {projeto_nome}")
    
    # 2. Verificar relatórios express aprovados
    print("\n⚡ RELATÓRIOS EXPRESS:")
    express_aprovados = RelatorioExpress.query.filter(
        func.lower(RelatorioExpress.status).in_(['aprovado', 'finalizado', 'aprovado final'])
    ).all()
    
    print(f"   Total de relatórios express aprovados: {len(express_aprovados)}")
    
    if express_aprovados:
        print(f"\n   Primeiros 5 relatórios express:")
        for exp in express_aprovados[:5]:
            print(f"   - ID: {exp.id}, Número: {exp.numero}, Status: {exp.status}, Obra: {exp.obra_nome}")
    
    # 3. Verificar TODAS as fotos no banco
    print("\n📷 FOTOS NO BANCO DE DADOS:")
    
    # Fotos de relatórios comuns
    total_fotos_relatorio = FotoRelatorio.query.count()
    print(f"   Total de fotos de relatórios comuns: {total_fotos_relatorio}")
    
    # Fotos de relatórios express
    total_fotos_express = FotoRelatorioExpress.query.count()
    print(f"   Total de fotos de relatórios express: {total_fotos_express}")
    
    print(f"\n   TOTAL GERAL DE FOTOS: {total_fotos_relatorio + total_fotos_express}")
    
    # 4. Verificar fotos de relatórios APROVADOS
    print("\n📷 FOTOS DE RELATÓRIOS APROVADOS:")
    
    fotos_aprovados = 0
    for rel in relatorios_aprovados:
        fotos = FotoRelatorio.query.filter_by(relatorio_id=rel.id).all()
        fotos_aprovados += len(fotos)
    
    print(f"   Fotos em relatórios comuns aprovados: {fotos_aprovados}")
    
    fotos_express_aprovados = 0
    for exp in express_aprovados:
        fotos = FotoRelatorioExpress.query.filter_by(relatorio_express_id=exp.id).all()
        fotos_express_aprovados += len(fotos)
    
    print(f"   Fotos em relatórios express aprovados: {fotos_express_aprovados}")
    print(f"\n   TOTAL DE FOTOS A FAZER BACKUP: {fotos_aprovados + fotos_express_aprovados}")
    
    # 5. Verificar se os arquivos físicos existem
    print("\n📁 VERIFICAÇÃO DE ARQUIVOS FÍSICOS:")
    
    upload_folder = app.config['UPLOAD_FOLDER']
    print(f"   Pasta de uploads configurada: {upload_folder}")
    print(f"   Caminho absoluto: {os.path.abspath(upload_folder)}")
    print(f"   Pasta existe? {os.path.exists(upload_folder)}")
    
    if os.path.exists(upload_folder):
        arquivos_na_pasta = os.listdir(upload_folder)
        print(f"   Total de arquivos na pasta uploads: {len(arquivos_na_pasta)}")
        
        # Verificar algumas fotos de relatórios aprovados
        print("\n   Verificando primeiras 10 fotos de relatórios aprovados:")
        fotos_verificadas = 0
        fotos_encontradas = 0
        fotos_nao_encontradas = 0
        
        for rel in relatorios_aprovados[:3]:  # Primeiros 3 relatórios
            fotos = FotoRelatorio.query.filter_by(relatorio_id=rel.id).limit(5).all()
            for foto in fotos:
                fotos_verificadas += 1
                
                # Tentar diferentes caminhos
                local_filename = foto.filename or foto.filename_original or foto.filename_anotada
                
                if local_filename:
                    file_path = os.path.join(upload_folder, local_filename)
                    file_path_basename = os.path.join(upload_folder, os.path.basename(local_filename))
                    
                    exists = os.path.exists(file_path) or os.path.exists(file_path_basename)
                    
                    if exists:
                        fotos_encontradas += 1
                        print(f"   ✅ Foto ID {foto.id}: {local_filename[:50]}")
                    else:
                        fotos_nao_encontradas += 1
                        print(f"   ❌ Foto ID {foto.id}: {local_filename[:50]} - NÃO ENCONTRADA")
                else:
                    fotos_nao_encontradas += 1
                    print(f"   ⚠️  Foto ID {foto.id}: SEM FILENAME no banco")
                
                if fotos_verificadas >= 10:
                    break
            
            if fotos_verificadas >= 10:
                break
        
        print(f"\n   Resumo da verificação:")
        print(f"   - Fotos verificadas: {fotos_verificadas}")
        print(f"   - Fotos encontradas no disco: {fotos_encontradas}")
        print(f"   - Fotos NÃO encontradas: {fotos_nao_encontradas}")
        
        if fotos_nao_encontradas > 0:
            print(f"\n   ⚠️  PROBLEMA: {fotos_nao_encontradas} de {fotos_verificadas} fotos não existem no disco!")
            print(f"   Isso explica por que o backup falha.")
    
    print("\n" + "=" * 80)
    print("FIM DA VERIFICAÇÃO")
    print("=" * 80)
