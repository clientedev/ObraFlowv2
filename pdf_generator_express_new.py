import os
import base64
from datetime import datetime
from flask import current_app
from models import RelatorioExpress, FotoRelatorioExpress
import weasyprint
from jinja2 import Template

def gerar_numero_relatorio_express():
    """Gerar número único para relatório express"""
    from models import RelatorioExpress
    
    # Buscar o último número
    ultimo_relatorio = RelatorioExpress.query.order_by(RelatorioExpress.id.desc()).first()
    
    if ultimo_relatorio:
        try:
            # Extrair número do último relatório (formato EXP001, EXP002, etc)
            numero_str = ultimo_relatorio.numero.replace('EXP', '')
            proximo_numero = int(numero_str) + 1
        except:
            proximo_numero = 1
    else:
        proximo_numero = 1
    
    return f"EXP{proximo_numero:03d}"

def gerar_pdf_relatorio_express_novo(relatorio_express_id, salvar_arquivo=True):
    """
    Gerar PDF do relatório express usando WeasyPrint com template idêntico aos relatórios normais
    
    Args:
        relatorio_express_id: ID do relatório express
        salvar_arquivo: Se deve salvar o arquivo no disco
    
    Returns:
        Caminho do arquivo gerado ou None se erro
    """
    
    try:
        # Buscar o relatório express
        relatorio = RelatorioExpress.query.get_or_404(relatorio_express_id)
        
        # Buscar fotos
        fotos = FotoRelatorioExpress.query.filter_by(
            relatorio_express_id=relatorio_express_id
        ).order_by(FotoRelatorioExpress.ordem).all()
        
        # Preparar dados das fotos com base64
        fotos_data = []
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        for foto in fotos:
            foto_path = os.path.join(upload_folder, foto.filename)
            if os.path.exists(foto_path):
                with open(foto_path, 'rb') as f:
                    foto_base64 = base64.b64encode(f.read()).decode('utf-8')
                    fotos_data.append({
                        'base64': foto_base64,
                        'legenda': foto.legenda,
                        'categoria': foto.categoria,
                        'filename': foto.filename
                    })
        
        # Preparar dados completos para o template
        dados = {
            'relatorio': {
                'numero': relatorio.numero,
                
                # Dados da empresa
                'nome_empresa': relatorio.nome_empresa or '',
                'cnpj_empresa': relatorio.cnpj_empresa or '',
                'telefone_empresa': relatorio.telefone_empresa or '',
                'email_empresa': relatorio.email_empresa or '',
                'endereco_empresa': relatorio.endereco_empresa or '',
                
                # Dados da obra
                'nome_obra': relatorio.nome_obra or '',
                'endereco_obra': relatorio.endereco_obra or '',
                'tipo_obra': relatorio.tipo_obra or '',
                'coordenadas_gps': relatorio.coordenadas_gps or '',
                
                # Dados do relatório
                'titulo_relatorio': relatorio.titulo_relatorio or f'Relatório de Visita Técnica - {relatorio.nome_obra}',
                'objetivo_visita': relatorio.objetivo_visita or '',
                'observacoes': relatorio.observacoes or '',
                'conclusoes': relatorio.conclusoes or '',
                'recomendacoes': relatorio.recomendacoes or '',
                
                # Itens técnicos
                'itens_observados': relatorio.itens_observados or '',
                'itens_conformes': relatorio.itens_conformes or '',
                'itens_nao_conformes': relatorio.itens_nao_conformes or '',
                
                # Dados da visita
                'data_visita': relatorio.data_visita.strftime('%d/%m/%Y') if relatorio.data_visita else '',
                'hora_inicio': relatorio.hora_inicio or '',
                'hora_fim': relatorio.hora_fim or '',
                'condicoes_climaticas': relatorio.condicoes_climaticas or '',
                
                # Responsáveis
                'preenchido_por': relatorio.preenchido_por or '',
                'liberado_por': relatorio.liberado_por or '',
                'responsavel_obra': relatorio.responsavel_obra or '',
                'cargo_responsavel_obra': relatorio.cargo_responsavel_obra or '',
                'data_relatorio': relatorio.data_relatorio.strftime('%d/%m/%Y') if relatorio.data_relatorio else '',
                
                # Sistema
                'status': relatorio.status
            },
            'fotos': fotos_data,
            'data_atual': datetime.now().strftime('%d/%m/%Y'),
            'hora_atual': datetime.now().strftime('%H:%M'),
            'autor': relatorio.autor.nome_completo
        }
        
        # Template HTML do relatório express (idêntico ao template normal com CSS profissional)
        html_template = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ relatorio.numero }} - {{ relatorio.nome_empresa }}</title>
            <style>
                /* Estilos idênticos aos relatórios normais */
                @page {
                    size: A4;
                    margin: 2.5cm 2cm 2cm 2cm;
                    @top-center {
                        content: "{{ relatorio.numero }} - {{ relatorio.nome_empresa }}";
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                        color: #666;
                    }
                    @bottom-center {
                        content: "Página " counter(page) " de " counter(pages);
                        font-family: Arial, sans-serif;
                        font-size: 9pt;
                        color: #666;
                    }
                }

                body {
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }

                .header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #343a40;
                }

                .logo {
                    width: 120px;
                    height: auto;
                    margin-right: 30px;
                }

                .company-info {
                    flex: 1;
                }

                .company-info h1 {
                    color: #343a40;
                    font-size: 18pt;
                    margin: 0 0 5px 0;
                    font-weight: bold;
                }

                .company-info .subtitle {
                    color: #20c1e8;
                    font-size: 12pt;
                    margin: 0;
                    font-weight: 600;
                }

                .report-title {
                    background: linear-gradient(135deg, #343a40 0%, #20c1e8 100%);
                    color: white;
                    text-align: center;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                    page-break-inside: avoid;
                }

                .report-title h2 {
                    margin: 0;
                    font-size: 16pt;
                    font-weight: bold;
                }

                .info-section {
                    margin: 20px 0;
                    page-break-inside: avoid;
                }

                .info-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }

                .info-table th,
                .info-table td {
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: left;
                }

                .info-table th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                    color: #343a40;
                    width: 30%;
                }

                .section-title {
                    color: #343a40;
                    font-size: 14pt;
                    font-weight: bold;
                    margin: 25px 0 15px 0;
                    padding-bottom: 5px;
                    border-bottom: 2px solid #20c1e8;
                }

                .observations {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-left: 4px solid #20c1e8;
                    margin: 15px 0;
                    border-radius: 0 5px 5px 0;
                }

                .photo-section {
                    margin: 20px 0;
                    page-break-inside: avoid;
                }

                .photo-container {
                    text-align: center;
                    margin: 20px 0;
                    page-break-inside: avoid;
                }

                .photo {
                    max-width: 100%;
                    max-height: 400px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .photo-caption {
                    margin-top: 10px;
                    font-style: italic;
                    color: #666;
                    font-size: 10pt;
                    text-align: center;
                }

                .signatures {
                    margin-top: 40px;
                    page-break-inside: avoid;
                }

                .signature-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }

                .signature-table td {
                    border: 1px solid #ddd;
                    padding: 40px 10px 10px 10px;
                    text-align: center;
                    vertical-align: bottom;
                    width: 33.33%;
                }

                .signature-label {
                    font-weight: bold;
                    color: #343a40;
                    border-top: 1px solid #333;
                    padding-top: 5px;
                    margin-top: 30px;
                }

                .footer-info {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #343a40;
                    text-align: center;
                    font-size: 9pt;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <!-- Cabeçalho -->
            <div class="header">
                <div class="company-info">
                    <h1>ELP CONSULTORIA E ENGENHARIA</h1>
                    <p class="subtitle">Engenharia Civil & Fachadas</p>
                </div>
            </div>

            <!-- Título do Relatório -->
            <div class="report-title">
                <h2>RELATÓRIO EXPRESS - {{ relatorio.numero }}</h2>
            </div>

            <!-- Informações do Cliente/Obra -->
            <div class="info-section">
                <h3 class="section-title">INFORMAÇÕES DO CLIENTE E OBRA</h3>
                <table class="info-table">
                    <tr>
                        <th>Cliente/Empresa:</th>
                        <td>{{ relatorio.nome_empresa }}</td>
                    </tr>
                    <tr>
                        <th>Obra/Projeto:</th>
                        <td>{{ relatorio.nome_obra }}</td>
                    </tr>
                    <tr>
                        <th>Endereço:</th>
                        <td>{{ relatorio.endereco_obra }}</td>
                    </tr>
                    <tr>
                        <th>Data do Relatório:</th>
                        <td>{{ relatorio.data_relatorio.strftime('%d/%m/%Y') }}</td>
                    </tr>
                </table>
            </div>

            <!-- Observações -->
            <div class="info-section">
                <h3 class="section-title">OBSERVAÇÕES GERAIS</h3>
                <div class="observations">
                    {{ relatorio.observacoes|replace('\n', '<br>') }}
                </div>
            </div>

            {% if relatorio.itens_observados %}
            <!-- Itens Observados -->
            <div class="info-section">
                <h3 class="section-title">ITENS OBSERVADOS</h3>
                <div class="observations">
                    {{ relatorio.itens_observados|replace('\n', '<br>') }}
                </div>
            </div>
            {% endif %}

            <!-- Fotos -->
            {% if fotos %}
            <div class="info-section">
                <h3 class="section-title">REGISTRO FOTOGRÁFICO</h3>
                {% for foto in fotos %}
                <div class="photo-container">
                    <img src="data:image/jpeg;base64,{{ foto.base64 }}" alt="Foto {{ loop.index }}" class="photo">
                    <div class="photo-caption">
                        <strong>Foto {{ loop.index }}{% if foto.categoria %} - {{ foto.categoria }}{% endif %}:</strong><br>
                        {{ foto.legenda }}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <!-- Assinaturas -->
            <div class="signatures">
                <h3 class="section-title">RESPONSÁVEIS</h3>
                <table class="signature-table">
                    <tr>
                        <td>
                            <div class="signature-label">{{ relatorio.preenchido_por }}<br>Preenchido por</div>
                        </td>
                        <td>
                            <div class="signature-label">{{ relatorio.liberado_por or '_________________' }}<br>Liberado por</div>
                        </td>
                        <td>
                            <div class="signature-label">{{ relatorio.responsavel_obra or '_________________' }}<br>Responsável da Obra</div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Rodapé -->
            <div class="footer-info">
                <p>Este relatório foi gerado automaticamente em {{ data_atual }} às {{ hora_atual }}</p>
                <p>ELP Consultoria e Engenharia - Engenharia Civil & Fachadas</p>
            </div>
        </body>
        </html>
        """
        
        # Renderizar template
        template = Template(html_template)
        html_content = template.render(**dados)
        
        # Configurar WeasyPrint
        if salvar_arquivo:
            # Definir caminho do arquivo
            filename = f'{relatorio.numero}_{relatorio.nome_empresa.replace(" ", "_")}.pdf'
            pdf_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
            
            # Gerar PDF
            weasyprint.HTML(string=html_content).write_pdf(pdf_path)
            
            return pdf_path
        else:
            # Retornar PDF como bytes
            pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
            return pdf_bytes
            
    except Exception as e:
        print(f"Erro ao gerar PDF do relatório express: {str(e)}")
        return None