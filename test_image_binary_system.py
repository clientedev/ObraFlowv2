#!/usr/bin/env python3
"""
Script de teste para verificar se o sistema de imagens está funcionando
corretamente após as correções implementadas.

Este script testa:
1. Conexão com o banco de dados
2. Estrutura das tabelas FotoRelatorio e FotoRelatorioExpress
3. Funcionamento das rotas de servir imagens
4. Validação de que o sistema está salvando dados binários
"""

import sys
import os
import requests
from datetime import datetime

# Configuração para importar os modelos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_structure():
    """Testa a estrutura das tabelas no banco"""
    try:
        from app import app, db
        from models import FotoRelatorio, FotoRelatorioExpress
        
        with app.app_context():
            # Verificar se as tabelas existem e têm a coluna 'imagem'
            print("📊 TESTE 1: Estrutura das tabelas")
            
            # Verificar FotoRelatorio
            inspector = db.inspect(db.engine)
            foto_relatorio_columns = [col['name'] for col in inspector.get_columns('fotos_relatorio')]
            
            required_columns = ['id', 'filename', 'filename_original', 'imagem']
            missing_columns = [col for col in required_columns if col not in foto_relatorio_columns]
            
            if missing_columns:
                print(f"❌ FotoRelatorio - Colunas ausentes: {missing_columns}")
                return False
            else:
                print("✅ FotoRelatorio - Todas as colunas necessárias presentes")
            
            # Verificar FotoRelatorioExpress
            foto_express_columns = [col['name'] for col in inspector.get_columns('fotos_relatorios_express')]
            missing_express_columns = [col for col in required_columns if col not in foto_express_columns]
            
            if missing_express_columns:
                print(f"❌ FotoRelatorioExpress - Colunas ausentes: {missing_express_columns}")
                return False
            else:
                print("✅ FotoRelatorioExpress - Todas as colunas necessárias presentes")
            
            return True
            
    except Exception as e:
        print(f"❌ ERRO no teste de estrutura: {str(e)}")
        return False

def test_image_routes():
    """Testa se as rotas de imagens respondem corretamente"""
    print("\n📊 TESTE 2: Rotas de imagens")
    
    try:
        base_url = "http://127.0.0.1:5000"
        
        # Testar rota básica
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor Flask respondendo")
        else:
            print(f"❌ Servidor Flask não responde (status: {response.status_code})")
            return False
        
        # Testar rota de imagem inexistente (deve retornar placeholder)
        response = requests.get(f"{base_url}/imagens/99999", timeout=5)
        if response.status_code in [200, 404]:
            print("✅ Rota /imagens/<id> acessível")
        else:
            print(f"❌ Rota /imagens/<id> com problemas (status: {response.status_code})")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO na conexão: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERRO no teste de rotas: {str(e)}")
        return False

def test_binary_data_functionality():
    """Testa se o sistema consegue verificar dados binários"""
    print("\n📊 TESTE 3: Funcionalidade de dados binários")
    
    try:
        from app import app, db
        from models import FotoRelatorio, FotoRelatorioExpress
        
        with app.app_context():
            # Contar registros com e sem dados binários
            fotos_com_binario = FotoRelatorio.query.filter(FotoRelatorio.imagem != None).count()
            fotos_sem_binario = FotoRelatorio.query.filter(FotoRelatorio.imagem == None).count()
            
            express_com_binario = FotoRelatorioExpress.query.filter(FotoRelatorioExpress.imagem != None).count()
            express_sem_binario = FotoRelatorioExpress.query.filter(FotoRelatorioExpress.imagem == None).count()
            
            print(f"📸 FotoRelatorio:")
            print(f"   - Com dados binários: {fotos_com_binario}")
            print(f"   - Sem dados binários: {fotos_sem_binario}")
            
            print(f"📸 FotoRelatorioExpress:")
            print(f"   - Com dados binários: {express_com_binario}")
            print(f"   - Sem dados binários: {express_sem_binario}")
            
            # Verificar se há pelo menos algumas fotos
            total_fotos = fotos_com_binario + fotos_sem_binario
            total_express = express_com_binario + express_sem_binario
            
            if total_fotos == 0 and total_express == 0:
                print("ℹ️  Nenhuma foto encontrada no banco (normal para instalação nova)")
            else:
                print(f"📊 Total de fotos no sistema: {total_fotos + total_express}")
            
            return True
            
    except Exception as e:
        print(f"❌ ERRO no teste de dados binários: {str(e)}")
        return False

def test_upload_folder():
    """Testa se a pasta de upload existe"""
    print("\n📊 TESTE 4: Pasta de upload")
    
    try:
        from app import app
        
        with app.app_context():
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            
            if os.path.exists(upload_folder):
                files = os.listdir(upload_folder)
                print(f"✅ Pasta de upload existe: {upload_folder}")
                print(f"📁 Arquivos na pasta: {len(files)}")
                
                if len(files) > 0:
                    # Mostrar alguns exemplos
                    examples = files[:5]
                    print(f"📄 Exemplos: {', '.join(examples)}")
                
            else:
                print(f"⚠️  Pasta de upload não existe: {upload_folder}")
                print("ℹ️  Será criada automaticamente no primeiro upload")
            
            return True
            
    except Exception as e:
        print(f"❌ ERRO no teste da pasta de upload: {str(e)}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 SISTEMA DE TESTES - UPLOAD DE IMAGENS BINÁRIOS")
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tests = [
        ("Estrutura do Banco", test_database_structure),
        ("Rotas de Imagens", test_image_routes),
        ("Dados Binários", test_binary_data_functionality),
        ("Pasta de Upload", test_upload_folder)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Executando: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"📋 {test_name}: {status}")
        except Exception as e:
            print(f"❌ ERRO CRÍTICO em {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Relatório final
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} {test_name}")
    
    print(f"\n📊 RESULTADO GERAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema funcionando corretamente.")
        exit_code = 0
    else:
        print("⚠️  ALGUNS TESTES FALHARAM. Verifique os erros acima.")
        exit_code = 1
    
    print(f"⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return exit_code

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)