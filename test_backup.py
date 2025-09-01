#!/usr/bin/env python3
"""
Script de teste para verificar o sistema de backup Google Drive
"""

import sys
import os
sys.path.append('.')

from app import app, db
from models import Projeto, Relatorio, RelatorioExpress
from google_drive_service import drive_service
from backup_hooks import trigger_auto_backup

def test_drive_connection():
    """Testa a conexão com Google Drive"""
    print("=== TESTE DE CONEXÃO GOOGLE DRIVE ===")
    
    status = drive_service.get_backup_status()
    print(f"Status do backup: {status}")
    
    if status['is_configured']:
        print("✓ Google Drive configurado")
    else:
        print("✗ Google Drive NÃO configurado")
        return False
    
    if drive_service.is_authenticated():
        print("✓ Google Drive autenticado")
    else:
        print("✗ Google Drive NÃO autenticado")
        return False
    
    return True

def test_project_backup(project_id=None):
    """Testa backup de um projeto específico"""
    print("\n=== TESTE DE BACKUP DE PROJETO ===")
    
    with app.app_context():
        if project_id:
            projeto = Projeto.query.get(project_id)
        else:
            projeto = Projeto.query.first()
        
        if not projeto:
            print("✗ Nenhum projeto encontrado para teste")
            return False
        
        print(f"Testando backup do projeto: {projeto.numero} - {projeto.nome}")
        
        # Contar arquivos existentes
        relatorios = Relatorio.query.filter_by(projeto_id=projeto.id).count()
        relatorios_express = RelatorioExpress.query.filter_by(projeto_id=projeto.id).count()
        
        print(f"Projeto tem {relatorios} relatórios normais e {relatorios_express} relatórios express")
        
        # Executar backup
        result = drive_service.backup_project_files(projeto.id)
        
        if result['success']:
            uploaded_count = len(result.get('uploaded_files', []))
            error_count = len(result.get('errors', []))
            
            print(f"✓ Backup realizado: {uploaded_count} arquivos enviados")
            
            if error_count > 0:
                print(f"⚠ {error_count} erros durante o backup:")
                for error in result.get('errors', []):
                    print(f"  - {error}")
            
            print("Arquivos enviados:")
            for file_info in result.get('uploaded_files', []):
                print(f"  - {file_info['type']}: {file_info['filename']}")
            
            return True
        else:
            print(f"✗ Erro no backup: {result.get('error', 'Erro desconhecido')}")
            return False

def test_create_project_folder():
    """Testa criação de pasta de projeto"""
    print("\n=== TESTE DE CRIAÇÃO DE PASTA ===")
    
    test_project_name = "Teste Backup System"
    test_project_number = "TESTE-001"
    
    try:
        folder_id = drive_service.create_project_folder(test_project_name, test_project_number)
        
        if folder_id:
            print(f"✓ Pasta criada com sucesso: {test_project_number} - {test_project_name}")
            print(f"  ID da pasta: {folder_id}")
            return True
        else:
            print("✗ Erro ao criar pasta")
            return False
            
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("SISTEMA DE TESTE - BACKUP GOOGLE DRIVE")
    print("=" * 50)
    
    # Teste 1: Conexão
    connection_ok = test_drive_connection()
    
    if not connection_ok:
        print("\n❌ FALHA: Google Drive não está configurado ou autenticado")
        print("\nPara configurar:")
        print("1. Acesse /backup/config na aplicação")
        print("2. Clique em 'Autorizar Google Drive'")
        print("3. Complete o processo de autenticação")
        return
    
    # Teste 2: Criação de pasta
    folder_ok = test_create_project_folder()
    
    # Teste 3: Backup de projeto
    backup_ok = test_project_backup()
    
    # Resumo
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES:")
    print(f"Conexão Google Drive: {'✓' if connection_ok else '✗'}")
    print(f"Criação de pasta: {'✓' if folder_ok else '✗'}")
    print(f"Backup de projeto: {'✓' if backup_ok else '✗'}")
    
    if connection_ok and folder_ok and backup_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema de backup funcionando.")
    else:
        print("\n⚠ ALGUNS TESTES FALHARAM. Verifique a configuração.")

if __name__ == '__main__':
    main()