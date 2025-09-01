"""
Gerador de PDF para Relatórios Express
Replicação exata do template WeasyPrint padrão com dados da empresa no topo
"""

from pdf_generator_weasy import WeasyPrintReportGenerator
from models import RelatorioExpress, FotoRelatorioExpress
import os
import json
from datetime import datetime
import base64

class ExpressReportGenerator(WeasyPrintReportGenerator):
    """
    Gerador de PDF para Relatórios Express
    Herda do WeasyPrintReportGenerator e adapta apenas os dados da empresa
    """
    
    def generate_express_report_pdf(self, relatorio_express, fotos_list, output_path):
        """
        Gera PDF do relatório express usando o mesmo template do WeasyPrint
        mas com dados da empresa ao invés de projeto
        """
        
        try:
            # Preparar dados no mesmo formato do relatório padrão
            report_data = self._prepare_express_data(relatorio_express, fotos_list)
            
            # Usar o mesmo template HTML com dados adaptados
            html_content = self._render_template('weasy_template.html', report_data)
            
            # Gerar PDF usando WeasyPrint
            result = self._generate_pdf_from_html(html_content, output_path)
            
            if result.get('success'):
                print(f"✓ PDF do Relatório Express gerado: {output_path}")
                return {
                    'success': True,
                    'file_path': output_path,
                    'size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
                }
            else:
                return {'success': False, 'error': result.get('error', 'Erro desconhecido')}
                
        except Exception as e:
            error_msg = f"Erro ao gerar PDF Express: {str(e)}"
            print(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _prepare_express_data(self, relatorio_express, fotos_list):
        """
        Prepara dados do relatório express no formato esperado pelo template
        Adaptação: dados da empresa ao invés de projeto
        """
        
        # Dados da empresa (substitui dados do projeto)
        empresa_data = {
            'nome': relatorio_express.empresa_nome,
            'endereco': relatorio_express.empresa_endereco or 'Não informado',
            'telefone': relatorio_express.empresa_telefone or 'Não informado',
            'email': relatorio_express.empresa_email or 'Não informado',
            'responsavel': relatorio_express.empresa_responsavel or 'Não informado'
        }
        
        # Dados do relatório (idênticos ao padrão)
        relatorio_data = {
            'numero': relatorio_express.numero,
            'data_visita': relatorio_express.data_visita.strftime('%d/%m/%Y') if relatorio_express.data_visita else '',
            'periodo_inicio': relatorio_express.periodo_inicio.strftime('%H:%M') if relatorio_express.periodo_inicio else '',
            'periodo_fim': relatorio_express.periodo_fim.strftime('%H:%M') if relatorio_express.periodo_fim else '',
            'condicoes_climaticas': relatorio_express.condicoes_climaticas or '',
            'temperatura': relatorio_express.temperatura or '',
            'endereco_visita': relatorio_express.endereco_visita or '',
            'observacoes_gerais': relatorio_express.observacoes_gerais or '',
            'pendencias': relatorio_express.pendencias or '',
            'recomendacoes': relatorio_express.recomendacoes or '',
            'status': relatorio_express.status,
            'created_at': relatorio_express.created_at.strftime('%d/%m/%Y %H:%M')
        }
        
        # Dados do autor (idênticos ao padrão)
        autor_data = {
            'nome': relatorio_express.autor.nome_completo,
            'cargo': relatorio_express.autor.cargo or 'Engenheiro',
            'email': relatorio_express.autor.email
        }
        
        # Processar fotos (idêntico ao padrão)
        fotos_data = []
        for foto in fotos_list:
            try:
                foto_path = os.path.join('uploads', foto.filename_anotada or foto.filename)
                if os.path.exists(foto_path):
                    with open(foto_path, 'rb') as f:
                        foto_base64 = base64.b64encode(f.read()).decode('utf-8')
                        fotos_data.append({
                            'titulo': foto.titulo or f'Foto {foto.ordem}',
                            'legenda': foto.legenda or '',
                            'descricao': foto.descricao or '',
                            'tipo_servico': foto.tipo_servico or '',
                            'base64': foto_base64,
                            'ordem': foto.ordem
                        })
            except Exception as e:
                print(f"Erro ao processar foto {foto.filename}: {e}")
                continue
        
        # Checklist (se houver)
        checklist_items = []
        if relatorio_express.checklist_completo:
            try:
                checklist_data = json.loads(relatorio_express.checklist_completo)
                checklist_items = checklist_data if isinstance(checklist_data, list) else []
            except:
                checklist_items = []
        
        # Retornar dados no formato do template padrão
        return {
            # ADAPTAÇÃO: empresa ao invés de projeto
            'empresa': empresa_data,  # Novo campo para dados da empresa
            
            # Dados idênticos ao relatório padrão
            'relatorio': relatorio_data,
            'autor': autor_data,
            'fotos': fotos_data,
            'checklist_items': checklist_items,
            
            # Logos (idênticos)
            'logo_elp': self._get_logo_base64('static/logo_elp_final.jpg'),
            'logo_cliente': None,  # Express não tem logo de cliente específico
            
            # Data de geração
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            
            # Flag para identificar como express
            'is_express': True
        }
    
    def _render_template(self, template_name, data):
        """
        Renderiza template HTML com dados do relatório express
        Usa o mesmo template do WeasyPrint mas com adaptações para empresa
        """
        from flask import render_template
        
        # Usar template específico para express ou adaptar o padrão
        return render_template('reports/express_template.html', **data)

# Funções auxiliares para compatibilidade com routes existentes
def gerar_pdf_relatorio_express(relatorio_express, output_path):
    """Função compatível com o sistema de rotas existente"""
    try:
        generator = ExpressReportGenerator()
        fotos = relatorio_express.fotos
        return generator.generate_express_report_pdf(relatorio_express, fotos, output_path)
    except Exception as e:
        return {'success': False, 'error': str(e)}

def gerar_numero_relatorio_express():
    """Gera número sequencial para relatórios express"""
    from models import RelatorioExpress
    from datetime import datetime
    
    # Buscar último número do ano atual
    ano_atual = datetime.now().year
    prefixo = f"EXP{ano_atual}"
    
    ultimo_relatorio = RelatorioExpress.query.filter(
        RelatorioExpress.numero.like(f"{prefixo}%")
    ).order_by(RelatorioExpress.numero.desc()).first()
    
    if ultimo_relatorio:
        try:
            ultimo_numero = int(ultimo_relatorio.numero.replace(prefixo, ''))
            novo_numero = ultimo_numero + 1
        except:
            novo_numero = 1
    else:
        novo_numero = 1
    
    return f"{prefixo}{novo_numero:03d}"