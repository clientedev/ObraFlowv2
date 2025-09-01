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
from flask import current_app

class ExpressReportGenerator(WeasyPrintReportGenerator):
    """
    Gerador de PDF para Relatórios Express
    Herda do WeasyPrintReportGenerator e adapta apenas os dados da empresa
    """
    
    def generate_express_report_pdf(self, relatorio_express, fotos_list, output_path):
        """
        Gera PDF do relatório express usando o mesmo método do WeasyPrint
        mas com dados da empresa ao invés de projeto
        """
        
        try:
            # Criar um objeto mock que simula um relatório padrão
            mock_relatorio = self._create_mock_report(relatorio_express)
            
            # Processar fotos no formato esperado
            fotos_processadas = self._process_express_photos(fotos_list)
            
            # Usar o método generate_report_pdf da classe pai
            return super().generate_report_pdf(mock_relatorio, fotos_processadas, output_path)
                
        except Exception as e:
            error_msg = f"Erro ao gerar PDF Express: {str(e)}"
            print(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _create_mock_report(self, relatorio_express):
        """
        Cria um objeto mock que simula um relatório padrão
        para usar com o gerador WeasyPrint existente
        """
        
        class MockProject:
            def __init__(self, express_data):
                self.nome = express_data.empresa_nome
                self.endereco = express_data.empresa_endereco or "Não informado"
                self.responsavel = express_data.autor  # Usar autor como responsável
        
        class MockReport:
            def __init__(self, express_data):
                self.numero = express_data.numero
                self.data_relatorio = express_data.created_at
                self.projeto = MockProject(express_data)
                self.autor = express_data.autor
                # Criar conteúdo combinando todas as observações
                conteudo_partes = []
                if express_data.observacoes_gerais:
                    conteudo_partes.append(f"OBSERVAÇÕES GERAIS:\n{express_data.observacoes_gerais}")
                if express_data.pendencias:
                    conteudo_partes.append(f"PENDÊNCIAS:\n{express_data.pendencias}")
                if express_data.recomendacoes:
                    conteudo_partes.append(f"RECOMENDAÇÕES:\n{express_data.recomendacoes}")
                
                self.conteudo = "\n\n".join(conteudo_partes) if conteudo_partes else "Relatório Express"
                
                # Dados específicos da visita
                info_visita = []
                if express_data.data_visita:
                    info_visita.append(f"Data da Visita: {express_data.data_visita.strftime('%d/%m/%Y')}")
                if express_data.periodo_inicio and express_data.periodo_fim:
                    info_visita.append(f"Período: {express_data.periodo_inicio.strftime('%H:%M')} às {express_data.periodo_fim.strftime('%H:%M')}")
                if express_data.condicoes_climaticas:
                    info_visita.append(f"Condições Climáticas: {express_data.condicoes_climaticas}")
                if express_data.temperatura:
                    info_visita.append(f"Temperatura: {express_data.temperatura}")
                if express_data.endereco_visita:
                    info_visita.append(f"Local da Visita: {express_data.endereco_visita}")
                
                if info_visita:
                    self.conteudo = "INFORMAÇÕES DA VISITA:\n" + "\n".join(info_visita) + "\n\n" + self.conteudo
                    
                # Processar checklist se houver dados
                checklist_content = self._process_checklist(express_data)
                if checklist_content:
                    self.conteudo = self.conteudo + "\n\n" + checklist_content
                    
            def _process_checklist(self, express_data):
                """Processa dados do checklist para inclusão no PDF"""
                try:
                    import json
                    checklist_json = express_data.checklist_dados or express_data.checklist_completo
                    
                    if not checklist_json:
                        return ""
                    
                    checklist_data = json.loads(checklist_json)
                    
                    if not checklist_data or len(checklist_data) == 0:
                        return ""
                    
                    checklist_lines = ["ITENS OBSERVADOS:"]
                    
                    for item in checklist_data:
                        status = "✓" if item.get('concluido', False) else "✗"
                        titulo = item.get('titulo', '')
                        checklist_lines.append(f"• {status} {titulo}")
                    
                    return "\n".join(checklist_lines)
                    
                except Exception as e:
                    print(f"Erro ao processar checklist: {e}")
                    return ""
                
        return MockReport(relatorio_express)
    
    def _process_express_photos(self, fotos_list):
        """
        Processa fotos do relatório express para formato esperado
        """
        fotos_processadas = []
        
        for foto in fotos_list:
            try:
                # Criar objeto mock foto
                class MockFoto:
                    def __init__(self, foto_express):
                        self.filename = foto_express.filename
                        self.filename_anotada = getattr(foto_express, 'filename_anotada', None)
                        self.legenda = foto_express.legenda or f"Foto {foto_express.ordem}"
                        self.titulo = getattr(foto_express, 'titulo', None) or self.legenda
                        self.descricao = getattr(foto_express, 'descricao', None) or ""
                        self.ordem = foto_express.ordem
                
                fotos_processadas.append(MockFoto(foto))
            except Exception as e:
                print(f"Erro ao processar foto: {e}")
                continue
        
        return fotos_processadas
    


# Funções auxiliares para compatibilidade com routes existentes
def gerar_pdf_relatorio_express(relatorio_express, output_path):
    """Função compatível com o sistema de rotas existente"""
    try:
        generator = ExpressReportGenerator()
        fotos = relatorio_express.fotos
        
        # Usar o método da classe pai que já funciona
        result = generator.generate_express_report_pdf(relatorio_express, fotos, output_path)
        
        if isinstance(result, str):  # Se retornou path do arquivo
            return {'success': True, 'file_path': result}
        elif isinstance(result, bytes):  # Se retornou bytes
            with open(output_path, 'wb') as f:
                f.write(result)
            return {'success': True, 'file_path': output_path}
        else:
            return {'success': False, 'error': 'Formato de retorno inválido'}
            
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