#!/usr/bin/env python3
"""
Teste do gerador de PDF WeasyPrint
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_weasy_pdf_generation():
    """Testar geração de PDF com WeasyPrint"""
    try:
        from pdf_generator_weasy import WeasyPrintReportGenerator
        
        print("✓ Importação do gerador WeasyPrint bem-sucedida")
        
        # Criar gerador
        generator = WeasyPrintReportGenerator()
        print("✓ Gerador WeasyPrint criado")
        
        # Dados de teste
        class MockUser:
            def __init__(self, nome):
                self.nome_completo = nome
        
        class MockProjeto:
            def __init__(self):
                self.nome = "Artesano Oscar Porto"
                self.endereco = "Rua Coronel Oscar Porto 507 - Paraíso"
                self.responsavel = MockUser("R. Yazbek")
        
        class MockRelatorio:
            def __init__(self):
                self.numero = "45"
                self.conteudo = "Piscina - Cheia executada, necessário utilizar tela metálica."
                self.data_relatorio = datetime(2025, 3, 12, 14, 38)
                self.projeto = MockProjeto()
                self.autor = MockUser("Eng. Mateus Almeida")
        
        class MockFoto:
            def __init__(self, ordem, desc):
                self.ordem = ordem
                self.descricao = desc
                self.filename = "test_image.jpg"  # Arquivo que não existe, mas será tratado
        
        # Criar dados de teste
        relatorio = MockRelatorio()
        fotos = [
            MockFoto(1, "Piscina - Cheia executada, necessário utilizar tela metálica."),
            MockFoto(2, "Piscina - Chapisco colante deve ser misturado fora")
        ]
        
        print("✓ Dados de teste preparados")
        
        # Gerar PDF
        output_path = "test_weasy_relatorio.pdf"
        result = generator.generate_report_pdf(relatorio, fotos, output_path)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✓ PDF gerado com sucesso: {output_path} ({file_size} bytes)")
            return True
        else:
            print("✗ Arquivo PDF não foi criado")
            return False
            
    except ImportError as e:
        print(f"✗ Erro de importação: {e}")
        print("WeasyPrint pode não estar instalado corretamente")
        return False
    except Exception as e:
        print(f"✗ Erro ao gerar PDF: {e}")
        return False

if __name__ == "__main__":
    print("Testando geração de PDF com WeasyPrint...")
    success = test_weasy_pdf_generation()
    if success:
        print("\n🎉 Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falhou")
    exit(0 if success else 1)