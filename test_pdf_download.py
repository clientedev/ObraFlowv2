"""
Criar um PDF de exemplo para download direto
"""

import sys
sys.path.append('.')
import os

from app import app
from pdf_generator_fitz import ArtesanoPDFGeneratorFitz

# Mock simples para demonstração
class MockRelatorio:
    def __init__(self):
        self.id = 1
        self.numero = "REL-0123"
        self.data_relatorio = None
        self.conteudo = "Estrutura em excelente estado. Revestimento necessita de reparos pontuais na fachada norte."
        
        # Mock autor
        self.autor = type('MockUser', (), {
            'nome_completo': 'Eng. João Silva'
        })()
        
        # Mock projeto
        self.projeto = type('MockProjeto', (), {
            'nome': 'Edifício Residencial Torres del Mar',
            'endereco': 'Av. Atlântica, 1200 - Copacabana - RJ',
            'responsavel': type('MockUser', (), {
                'nome_completo': 'Construtora ABC Ltda'
            })()
        })()

def create_sample_pdf():
    """Criar PDF de exemplo"""
    try:
        print("Gerando PDF de exemplo...")
        
        # Criar mock
        relatorio = MockRelatorio()
        fotos = []  # Sem fotos para este exemplo
        
        # Gerar PDF
        generator = ArtesanoPDFGeneratorFitz()
        output_file = "static/relatorio_exemplo_fitz.pdf"
        
        result = generator.generate_report_pdf(relatorio, fotos, output_file)
        
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"✓ PDF de exemplo criado: {output_file} ({size} bytes)")
            print(f"✓ Disponível em: /static/relatorio_exemplo_fitz.pdf")
            return True
        else:
            print("❌ Erro ao criar PDF")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    with app.app_context():
        success = create_sample_pdf()
        sys.exit(0 if success else 1)