#!/usr/bin/env python3
"""
Script para testar a geração de PDF
"""

import sys
import os
sys.path.append('.')

from pdf_generator_artesano import ArtesanoPDFGenerator
from models import Relatorio, FotoRelatorio
from app import app, db

def test_pdf_generation():
    """Testar geração de PDF"""
    with app.app_context():
        # Buscar um relatório existente
        relatorio = Relatorio.query.first()
        if not relatorio:
            print("❌ Nenhum relatório encontrado para teste")
            return False
        
        print(f"✓ Relatório encontrado: {relatorio.numero}")
        
        # Buscar fotos do relatório
        fotos = FotoRelatorio.query.filter_by(relatorio_id=relatorio.id).all()
        print(f"✓ {len(fotos)} foto(s) encontrada(s)")
        
        try:
            # Criar gerador
            generator = ArtesanoPDFGenerator()
            print("✓ Gerador de PDF criado")
            
            # Gerar PDF
            output_path = "test_relatorio.pdf"
            result = generator.generate_report_pdf(relatorio, fotos, output_path)
            
            if result and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✓ PDF gerado com sucesso: {output_path} ({file_size} bytes)")
                return True
            else:
                print("❌ PDF não foi gerado")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_pdf_generation()
    sys.exit(0 if success else 1)