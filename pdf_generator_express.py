"""
Gerador de PDF para Relatórios Express
Replicação exata do template WeasyPrint padrão com dados da empresa no topo
"""

# Try to import WeasyPrint generator with graceful fallback
try:
    from pdf_generator_weasy import WeasyPrintReportGenerator, WEASYPRINT_AVAILABLE
except ImportError:
    print("⚠️  WeasyPrint generator não disponível")
    WEASYPRINT_AVAILABLE = False
    WeasyPrintReportGenerator = None
from models import RelatorioExpress, FotoRelatorioExpress
import os
import json
from datetime import datetime
import base64
from flask import current_app

class ExpressReportGenerator(WeasyPrintReportGenerator if WEASYPRINT_AVAILABLE else object):
    """
    Gerador de PDF para Relatórios Express
    Herda do WeasyPrintReportGenerator e adapta apenas os dados da empresa
    """
    
    def generate_express_report_pdf(self, relatorio_express, fotos_list, output_path):
        """
        Gera PDF do relatório express usando o mesmo método do WeasyPrint
        mas com dados da empresa ao invés de projeto
        """
        
        if not WEASYPRINT_AVAILABLE:
            # Fallback para ReportLab quando WeasyPrint não estiver disponível
            try:
                return self._generate_express_fallback_pdf(relatorio_express, fotos_list, output_path)
            except Exception as e:
                error_msg = f"Erro ao gerar PDF Express (fallback): {str(e)}"
                print(error_msg)
                return {'success': False, 'error': error_msg}
        
        try:
            # Criar um objeto mock que simula um relatório padrão
            mock_relatorio = self._create_mock_report(relatorio_express)
            
            # Processar fotos no formato esperado
            fotos_processadas = self._process_express_photos(fotos_list)
            
            # Usar o método generate_report_pdf da classe pai
            return super().generate_report_pdf(mock_relatorio, fotos_processadas, output_path)
                
        except Exception as e:
            # Tentar fallback para ReportLab
            try:
                print(f"⚠️  WeasyPrint falhou para Express: {e}")
                print("🔄 Tentando fallback para ReportLab...")
                return self._generate_express_fallback_pdf(relatorio_express, fotos_list, output_path)
            except Exception as fallback_error:
                error_msg = f"Erro ao gerar PDF Express - WeasyPrint: {str(e)} | Fallback: {str(fallback_error)}"
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
        
        class MockVisita:
            def __init__(self, express_data):
                self.data = express_data.data_visita
                self.periodo_inicio = express_data.periodo_inicio
                self.periodo_fim = express_data.periodo_fim
                self.condicoes_climaticas = express_data.condicoes_climaticas
                self.temperatura = express_data.temperatura
                self.endereco = express_data.endereco_visita
        
        class MockReport:
            def __init__(self, express_data):
                self.numero = express_data.numero
                self.data_relatorio = express_data.created_at
                self.projeto = MockProject(express_data)
                self.visita = MockVisita(express_data)
                self.autor = express_data.autor
                
                # Criar conteúdo combinando todas as observações e dados da visita
                conteudo_partes = []
                
                # Informações da visita primeiro
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
                
                # Adicionar participantes
                participantes = express_data.participantes
                if participantes:
                    participantes_nomes = [f"• {p.nome_completo} ({p.cargo})" for p in participantes]
                    info_visita.append(f"Funcionários Participantes:\n" + "\n".join(participantes_nomes))
                
                if info_visita:
                    conteudo_partes.append("INFORMAÇÕES DA VISITA:\n" + "\n".join(info_visita))
                
                # Processar checklist
                checklist_content = self._process_checklist(express_data)
                if checklist_content:
                    conteudo_partes.append(checklist_content)
                
                # Adicionar observações
                if express_data.observacoes_gerais:
                    conteudo_partes.append(f"OBSERVAÇÕES GERAIS:\n{express_data.observacoes_gerais}")
                if express_data.pendencias:
                    conteudo_partes.append(f"PENDÊNCIAS:\n{express_data.pendencias}")
                if express_data.recomendacoes:
                    conteudo_partes.append(f"RECOMENDAÇÕES:\n{express_data.recomendacoes}")
                
                self.conteudo = "\n\n".join(conteudo_partes) if conteudo_partes else "Relatório Express"
                    
            def _process_checklist(self, express_data):
                """CHECKLIST REMOVIDO DO PDF - retorna string vazia"""
                # Checklist não deve aparecer no PDF
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
                        # Criar descrição completa incluindo legenda pré-definida
                        base_descricao = f"Foto {foto_express.ordem}"
                        if foto_express.legenda:
                            base_descricao += f" - {foto_express.legenda}"
                        
                        self.legenda = base_descricao
                        self.titulo = getattr(foto_express, 'titulo', None) or base_descricao
                        self.descricao = base_descricao
                        self.ordem = foto_express.ordem
                
                fotos_processadas.append(MockFoto(foto))
            except Exception as e:
                print(f"Erro ao processar foto: {e}")
                continue
        
        return fotos_processadas
    
    def _generate_express_fallback_pdf(self, relatorio_express, fotos_list, output_path):
        """
        Fallback para gerar PDF usando ReportLab quando WeasyPrint não estiver disponível
        """
        from pdf_generator import ReportGenerator
        
        # Criar mock do relatório para usar com ReportLab
        mock_relatorio = self._create_mock_report(relatorio_express)
        
        # Processar fotos
        fotos_processadas = self._process_express_photos(fotos_list)
        
        # Usar ReportLab generator
        reportlab_generator = ReportGenerator()
        return reportlab_generator.generate_report_pdf(mock_relatorio, fotos_processadas, output_path)


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