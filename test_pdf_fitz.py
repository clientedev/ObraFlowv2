"""
Teste do novo gerador de PDF usando PyMuPDF
"""

import os
import sys
sys.path.append('.')

from pdf_generator_fitz import ArtesanoPDFGeneratorFitz

# Mock data para teste
class MockRelatorio:
    def __init__(self):
        self.id = 1
        self.numero = "REL-0045"
        self.data_relatorio = None
        self.conteudo = "Piscina - Cheia executada, necessário utilizar tela metálica."
        
        # Mock autor
        self.autor = type('MockUser', (), {
            'nome_completo': 'Eng. Mateus Almeida'
        })()
        
        # Mock projeto
        self.projeto = type('MockProjeto', (), {
            'nome': 'Artesano Oscar Porto',
            'endereco': 'Rua Coronel Oscar Porto 507 - Paraíso',
            'responsavel': type('MockUser', (), {
                'nome_completo': 'R. Yazbek'
            })()
        })()

class MockFoto:
    def __init__(self, filename, descricao, ordem):
        self.filename = filename
        self.descricao = descricao
        self.ordem = ordem

def test_pdf_generation():
    """Testar geração do PDF"""
    try:
        print("🧪 Iniciando teste do gerador PyMuPDF...")
        
        # Verificar se template existe
        template_path = "templates/pdf_template_artesano.pdf"
        if not os.path.exists(template_path):
            print(f"❌ Template não encontrado: {template_path}")
            return False
            
        print("✓ Template encontrado")
        
        # Criar mock do relatório
        relatorio = MockRelatorio()
        print(f"✓ Relatório mock criado: {relatorio.numero}")
        
        # Criar mock das fotos (usando as fotos existentes se disponíveis)
        fotos = []
        upload_folder = 'uploads'
        if os.path.exists(upload_folder):
            foto_files = [f for f in os.listdir(upload_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            for i, foto_file in enumerate(foto_files[:2]):  # Máximo 2 fotos para teste
                fotos.append(MockFoto(foto_file, f"Foto {i+1} - Teste", i+1))
        
        print(f"✓ {len(fotos)} foto(s) preparada(s)")
        
        # Criar gerador
        generator = ArtesanoPDFGeneratorFitz()
        print("✓ Gerador PyMuPDF criado")
        
        # Gerar PDF
        output_path = "test_relatorio_fitz.pdf"
        result = generator.generate_report_pdf(relatorio, fotos, output_path)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✓ PDF gerado com sucesso: {output_path} ({file_size} bytes)")
            return True
        else:
            print("❌ Arquivo PDF não foi criado")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante teste: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    sys.exit(0 if success else 1)