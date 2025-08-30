"""
Teste da rota de PDF usando contexto Flask
"""

import sys
sys.path.append('.')

from app import app, db
from models import Relatorio, FotoRelatorio

def test_pdf_route():
    """Testar a rota de PDF dentro do contexto Flask"""
    with app.app_context():
        # Buscar um relatório existente
        relatorio = Relatorio.query.first()
        if not relatorio:
            print("❌ Nenhum relatório encontrado no banco de dados")
            return False
        
        print(f"✓ Relatório encontrado: {relatorio.numero}")
        
        # Buscar fotos do relatório
        fotos = FotoRelatorio.query.filter_by(relatorio_id=relatorio.id).order_by(FotoRelatorio.ordem).all()
        print(f"✓ {len(fotos)} foto(s) encontrada(s)")
        
        try:
            from pdf_generator_fitz import ArtesanoPDFGeneratorFitz
            generator = ArtesanoPDFGeneratorFitz()
            
            # Testar geração do PDF
            output_path = "test_relatorio_route.pdf"
            result = generator.generate_report_pdf(relatorio, fotos, output_path)
            
            if result and result == output_path:
                print(f"✓ PDF gerado com sucesso: {output_path}")
                import os
                size = os.path.getsize(output_path)
                print(f"✓ Tamanho do arquivo: {size} bytes")
                return True
            else:
                print("❌ Falha na geração do PDF")
                return False
                
        except Exception as e:
            print(f"❌ Erro na geração: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_pdf_route()
    sys.exit(0 if success else 1)