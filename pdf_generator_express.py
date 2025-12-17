"""
Gerador de PDF para Relatórios Express usando WeasyPrint
Este módulo fornece funções para gerar PDFs de Relatórios Express,
adaptando-os para funcionar com o mesmo gerador dos relatórios comuns.
"""

import os
import json
import logging
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

def gerar_numero_relatorio_express():
    """
    Gera um número único para relatório express no formato EXP-YYYY-NNNN
    """
    from app import db
    from models import RelatorioExpress
    
    ano_atual = datetime.now().year
    
    ultimo_relatorio = RelatorioExpress.query.filter(
        RelatorioExpress.numero.like(f'EXP-{ano_atual}-%')
    ).order_by(RelatorioExpress.id.desc()).first()
    
    if ultimo_relatorio:
        try:
            ultimo_numero = int(ultimo_relatorio.numero.split('-')[-1])
            novo_numero = ultimo_numero + 1
        except (ValueError, IndexError):
            novo_numero = 1
    else:
        novo_numero = 1
    
    return f"EXP-{ano_atual}-{novo_numero:04d}"


def gerar_pdf_relatorio_express(relatorio_ou_id, output_path=None, salvar_arquivo=True):
    """
    Gera PDF do Relatório Express usando WeasyPrint.
    
    Args:
        relatorio_ou_id: Objeto RelatorioExpress ou ID do relatório
        output_path: Caminho para salvar o arquivo (opcional)
        salvar_arquivo: Se True, salva em arquivo; se False, retorna BytesIO
        
    Returns:
        dict com 'success' e 'path'/'data' ou 'error'
        ou BytesIO se salvar_arquivo=False
    """
    from app import db
    from models import RelatorioExpress, FotoRelatorioExpress
    
    try:
        if isinstance(relatorio_ou_id, int):
            relatorio_express = RelatorioExpress.query.get(relatorio_ou_id)
            if not relatorio_express:
                if salvar_arquivo:
                    return {'success': False, 'error': f'Relatório Express {relatorio_ou_id} não encontrado'}
                else:
                    raise Exception(f'Relatório Express {relatorio_ou_id} não encontrado')
        else:
            relatorio_express = relatorio_ou_id
        
        fotos = FotoRelatorioExpress.query.filter_by(
            relatorio_express_id=relatorio_express.id
        ).order_by(FotoRelatorioExpress.ordem).all()
        
        class VirtualProject:
            """Projeto virtual com dados da obra express"""
            def __init__(self, obra_nome, obra_endereco, obra_construtora, obra_responsavel):
                self.nome = obra_nome or 'Obra Express'
                self.endereco = obra_endereco or ''
                self.construtora = obra_construtora or ''
                self.cliente = obra_construtora or ''
                self.responsavel = obra_responsavel or ''
        
        class VirtualAuthor:
            """Autor virtual quando não há autor real"""
            def __init__(self, nome='Não informado'):
                self.nome_completo = nome
        
        class ExpressReportAdapter:
            """Adaptador para fazer RelatorioExpress funcionar com WeasyPrintReportGenerator"""
            def __init__(self, express_report):
                self.id = express_report.id
                self.numero = express_report.numero
                self.titulo = express_report.titulo
                self.conteudo = express_report.conteudo or ''
                self.data_relatorio = express_report.data_relatorio
                self.data_aprovacao = express_report.data_aprovacao
                self.status = express_report.status
                self.observacoes_finais = express_report.observacoes_finais
                
                acomp = express_report.acompanhantes
                if isinstance(acomp, str):
                    try:
                        self.acompanhantes = json.loads(acomp)
                    except:
                        self.acompanhantes = []
                else:
                    self.acompanhantes = acomp or []
                
                self.checklist_data = express_report.checklist_data
                
                if express_report.autor:
                    self.autor = express_report.autor
                else:
                    self.autor = VirtualAuthor('Não informado')
                
                self.aprovador = express_report.aprovador
                
                self.projeto = VirtualProject(
                    express_report.obra_nome,
                    express_report.obra_endereco,
                    express_report.obra_construtora,
                    express_report.obra_responsavel
                )
        
        relatorio_adaptado = ExpressReportAdapter(relatorio_express)
        
        from pdf_generator_weasy import WeasyPrintReportGenerator
        generator = WeasyPrintReportGenerator()
        
        if salvar_arquivo:
            if output_path:
                pdf_path = output_path
            else:
                upload_folder = 'uploads'
                os.makedirs(upload_folder, exist_ok=True)
                pdf_filename = f"relatorio_express_{relatorio_express.numero.replace('/', '_')}.pdf"
                pdf_path = os.path.join(upload_folder, pdf_filename)
            
            generator.generate_report_pdf(relatorio_adaptado, fotos, pdf_path)
            
            logger.info(f"✅ PDF Express gerado: {pdf_path}")
            return {'success': True, 'path': pdf_path}
        else:
            pdf_bytes = generator.generate_report_pdf(relatorio_adaptado, fotos)
            pdf_io = BytesIO(pdf_bytes)
            pdf_io.seek(0)
            return pdf_io
            
    except Exception as e:
        logger.error(f"❌ Erro ao gerar PDF Express: {e}", exc_info=True)
        if salvar_arquivo:
            return {'success': False, 'error': str(e)}
        else:
            raise


def gerar_pdf_relatorio_comum(relatorio_id, output_path=None):
    """
    Gera PDF do Relatório Comum usando WeasyPrint.
    
    Args:
        relatorio_id: ID do relatório
        output_path: Caminho para salvar o arquivo (opcional)
        
    Returns:
        dict com 'success' e 'path' ou 'error'
    """
    from app import db
    from models import Relatorio, FotoRelatorio
    
    try:
        relatorio = Relatorio.query.get(relatorio_id)
        if not relatorio:
            return {'success': False, 'error': f'Relatório {relatorio_id} não encontrado'}
        
        fotos = FotoRelatorio.query.filter_by(
            relatorio_id=relatorio_id
        ).order_by(FotoRelatorio.ordem).all()
        
        from pdf_generator_weasy import WeasyPrintReportGenerator
        generator = WeasyPrintReportGenerator()
        
        if output_path:
            pdf_path = output_path
        else:
            upload_folder = 'uploads'
            os.makedirs(upload_folder, exist_ok=True)
            pdf_filename = f"relatorio_{relatorio.numero.replace('/', '_')}.pdf"
            pdf_path = os.path.join(upload_folder, pdf_filename)
        
        generator.generate_report_pdf(relatorio, fotos, pdf_path)
        
        logger.info(f"✅ PDF gerado: {pdf_path}")
        return {'success': True, 'path': pdf_path}
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar PDF: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
