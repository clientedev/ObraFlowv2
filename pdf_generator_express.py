import os
import base64
from datetime import datetime
from weasyprint import HTML, CSS
from jinja2 import Template
from models import ChecklistPadrao

def gerar_numero_relatorio_express():
    """Gera número sequencial para relatório express"""
    from models import RelatorioExpress
    from app import db
    
    # Buscar o último número
    ultimo = RelatorioExpress.query.order_by(RelatorioExpress.id.desc()).first()
    if ultimo:
        try:
            # Extrair número do formato "EXP-YYYY-NNNN"
            partes = ultimo.numero.split('-')
            if len(partes) >= 3:
                ultimo_numero = int(partes[-1])
                proximo_numero = ultimo_numero + 1
            else:
                proximo_numero = 1
        except (ValueError, IndexError):
            proximo_numero = 1
    else:
        proximo_numero = 1
    
    ano_atual = datetime.now().year
    return f"EXP-{ano_atual}-{proximo_numero:04d}"

def gerar_pdf_relatorio_express(relatorio_express, fotos, output_path):
    """
    Gera PDF do relatório express usando o mesmo template dos relatórios padrão
    """
    try:
        # Template HTML idêntico ao relatório padrão, mas adaptado para dados express
        template_html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ relatorio.titulo_obra }}</title>
    <style>
        /* Estilos idênticos ao template Artesano */
        @page {
            size: A4;
            margin: 2cm 1.5cm;
            @top-center {
                content: "{{ relatorio.nome_empresa }}";
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
            font-family: Arial, Helvetica, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #003f7f;
            padding-bottom: 20px;
        }
        
        .logo-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .logo {
            max-height: 80px;
            width: auto;
        }
        
        .title {
            font-size: 18pt;
            font-weight: bold;
            color: #003f7f;
            margin: 15px 0;
            text-transform: uppercase;
        }
        
        .subtitle {
            font-size: 14pt;
            color: #666;
            margin-bottom: 10px;
        }
        
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 10pt;
        }
        
        .info-table th, .info-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        .info-table th {
            background-color: #f5f5f5;
            font-weight: bold;
            width: 25%;
        }
        
        .section {
            margin: 25px 0;
            page-break-inside: avoid;
        }
        
        .section-title {
            font-size: 14pt;
            font-weight: bold;
            color: #003f7f;
            border-bottom: 1px solid #003f7f;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }
        
        .section-content {
            text-align: justify;
            margin-bottom: 15px;
        }
        
        .photo-section {
            margin: 20px 0;
            text-align: center;
        }
        
        .photo {
            max-width: 100%;
            max-height: 400px;
            border: 1px solid #ddd;
            margin: 10px 0;
        }
        
        .photo-caption {
            font-size: 10pt;
            color: #666;
            margin: 5px 0 15px 0;
            font-style: italic;
        }
        
        .checklist {
            margin: 20px 0;
        }
        
        .checklist-item {
            margin: 8px 0;
            padding: 5px;
            font-size: 10pt;
        }
        
        .checklist-item.ok {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
        }
        
        .checklist-item.nok {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }
        
        .checklist-item.na {
            background-color: #f8f9fa;
            border-left: 4px solid #6c757d;
        }
        
        .signature-section {
            margin-top: 40px;
            page-break-inside: avoid;
        }
        
        .signature-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .signature-table td {
            border: 1px solid #333;
            padding: 15px;
            text-align: center;
            vertical-align: bottom;
            height: 80px;
        }
        
        .signature-label {
            font-weight: bold;
            font-size: 10pt;
        }
        
        .page-break {
            page-break-before: always;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-container">
            {% if logo_elp %}
            <img src="data:image/jpeg;base64,{{ logo_elp }}" alt="Logo ELP" class="logo">
            {% endif %}
            <div style="flex-grow: 1; text-align: center;">
                <div class="title">RELATÓRIO TÉCNICO EXPRESS</div>
                <div class="subtitle">{{ relatorio.titulo_obra }}</div>
            </div>
            {% if logo_cliente %}
            <img src="data:image/jpeg;base64,{{ logo_cliente }}" alt="Logo Cliente" class="logo">
            {% endif %}
        </div>
    </div>

    <!-- Informações Gerais -->
    <table class="info-table">
        <tr>
            <th>Cliente:</th>
            <td>{{ relatorio.nome_empresa }}</td>
            <th>CNPJ:</th>
            <td>{{ relatorio.cnpj_empresa or 'N/A' }}</td>
        </tr>
        <tr>
            <th>Relatório Nº:</th>
            <td>{{ relatorio.numero }}</td>
            <th>Data da Visita:</th>
            <td>{{ relatorio.data_visita.strftime('%d/%m/%Y') if relatorio.data_visita else 'N/A' }}</td>
        </tr>
        <tr>
            <th>Obra/Projeto:</th>
            <td colspan="3">{{ relatorio.titulo_obra }}</td>
        </tr>
        {% if relatorio.endereco_obra %}
        <tr>
            <th>Endereço:</th>
            <td colspan="3">{{ relatorio.endereco_obra }}</td>
        </tr>
        {% endif %}
        {% if relatorio.tipo_servico %}
        <tr>
            <th>Tipo de Serviço:</th>
            <td>{{ relatorio.tipo_servico }}</td>
            <th>Responsável:</th>
            <td>{{ relatorio.responsavel_obra or 'N/A' }}</td>
        </tr>
        {% endif %}
    </table>

    <!-- Introdução -->
    {% if relatorio.introducao %}
    <div class="section">
        <h2 class="section-title">1. INTRODUÇÃO</h2>
        <div class="section-content">
            {{ relatorio.introducao|replace('\n', '<br>')|safe }}
        </div>
    </div>
    {% endif %}

    <!-- Metodologia -->
    {% if relatorio.metodologia %}
    <div class="section">
        <h2 class="section-title">2. METODOLOGIA</h2>
        <div class="section-content">
            {{ relatorio.metodologia|replace('\n', '<br>')|safe }}
        </div>
    </div>
    {% endif %}

    <!-- Itens Observados -->
    {% if relatorio.itens_observados %}
    <div class="section">
        <h2 class="section-title">3. ITENS OBSERVADOS</h2>
        <div class="section-content">
            {{ relatorio.itens_observados|replace('\n', '<br>')|safe }}
        </div>
    </div>
    {% endif %}

    <!-- Checklist -->
    {% if checklist_items %}
    <div class="section">
        <h2 class="section-title">4. CHECKLIST DE VERIFICAÇÃO</h2>
        <div class="checklist">
            {% for item in checklist_items %}
            <div class="checklist-item {{ item.status }}">
                <strong>{{ item.texto }}</strong>
                {% if item.status == 'ok' %}
                    <span style="float: right; color: #28a745;">✓ OK</span>
                {% elif item.status == 'nok' %}
                    <span style="float: right; color: #dc3545;">✗ NÃO OK</span>
                {% else %}
                    <span style="float: right; color: #6c757d;">- N/A</span>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <!-- Fotos -->
    {% if fotos %}
    <div class="section page-break">
        <h2 class="section-title">{{ '5.' if checklist_items else '4.' }} REGISTRO FOTOGRÁFICO</h2>
        {% for foto in fotos %}
        <div class="photo-section">
            {% if foto.imagem_base64 %}
            <img src="data:image/jpeg;base64,{{ foto.imagem_base64 }}" alt="Foto {{ loop.index }}" class="photo">
            {% endif %}
            <div class="photo-caption">
                <strong>Foto {{ loop.index }}</strong>
                {% if foto.titulo %} - {{ foto.titulo }}{% endif %}
                {% if foto.legenda %}<br>{{ foto.legenda }}{% endif %}
                {% if foto.descricao %}<br><em>{{ foto.descricao }}</em>{% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Observações Gerais -->
    {% if relatorio.observacoes_gerais %}
    <div class="section">
        <h2 class="section-title">{{ '6.' if checklist_items else '5.' }} OBSERVAÇÕES GERAIS</h2>
        <div class="section-content">
            {{ relatorio.observacoes_gerais|replace('\n', '<br>')|safe }}
        </div>
    </div>
    {% endif %}

    <!-- Conclusões -->
    {% if relatorio.conclusoes %}
    <div class="section">
        <h2 class="section-title">{{ '7.' if checklist_items else '6.' }} CONCLUSÕES</h2>
        <div class="section-content">
            {{ relatorio.conclusoes|replace('\n', '<br>')|safe }}
        </div>
    </div>
    {% endif %}

    <!-- Recomendações -->
    {% if relatorio.recomendacoes %}
    <div class="section">
        <h2 class="section-title">{{ '8.' if checklist_items else '7.' }} RECOMENDAÇÕES</h2>
        <div class="section-content">
            {{ relatorio.recomendacoes|replace('\n', '<br>')|safe }}
        </div>
    </div>
    {% endif %}

    <!-- Assinaturas -->
    <div class="signature-section">
        <h2 class="section-title">RESPONSABILIDADE TÉCNICA E ASSINATURAS</h2>
        <table class="signature-table">
            <tr>
                <td style="width: 50%;">
                    <div class="signature-label">RESPONSÁVEL TÉCNICO</div>
                    <br><br>
                    <div>{{ relatorio.responsavel_tecnico or 'ELP Consultoria e Engenharia' }}</div>
                    {% if relatorio.crea_responsavel %}
                    <div>{{ relatorio.crea_responsavel }}</div>
                    {% endif %}
                </td>
                <td style="width: 50%;">
                    <div class="signature-label">CLIENTE</div>
                    <br><br>
                    {% if relatorio.assinatura_cliente %}
                    <div>{{ relatorio.nome_cliente_assinatura or '' }}</div>
                    <div>{{ relatorio.cargo_cliente_assinatura or '' }}</div>
                    {% else %}
                    <div style="color: #666;">Assinatura Pendente</div>
                    {% endif %}
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 20px; font-size: 9pt; color: #666; text-align: center;">
            Relatório gerado em {{ datetime.now().strftime('%d/%m/%Y às %H:%M') }}<br>
            ELP Consultoria e Engenharia - Engenharia Civil & Fachadas
        </div>
    </div>
</body>
</html>
        """

        # Preparar dados das fotos com base64
        fotos_processadas = []
        for foto in fotos:
            foto_data = {
                'titulo': foto.titulo,
                'legenda': foto.legenda,
                'descricao': foto.descricao,
                'imagem_base64': None
            }
            
            # Usar imagem anotada se disponível, senão original
            image_path = None
            if foto.filename_anotada and os.path.exists(os.path.join('uploads', foto.filename_anotada)):
                image_path = os.path.join('uploads', foto.filename_anotada)
            elif foto.filename and os.path.exists(os.path.join('uploads', foto.filename)):
                image_path = os.path.join('uploads', foto.filename)
            
            if image_path:
                try:
                    with open(image_path, 'rb') as img_file:
                        foto_data['imagem_base64'] = base64.b64encode(img_file.read()).decode('utf-8')
                except Exception as e:
                    print(f"Erro ao processar foto {foto.filename}: {e}")
            
            fotos_processadas.append(foto_data)

        # Processar checklist
        checklist_items = []
        if relatorio_express.checklist_dados:
            try:
                import json
                checklist_data = json.loads(relatorio_express.checklist_dados)
                checklist_items = checklist_data.get('items', [])
            except:
                pass

        # Carregar logos
        logo_elp_base64 = None
        logo_cliente_base64 = None
        
        # Logo ELP
        logo_elp_path = 'static/logo_elp_final.jpg'
        if os.path.exists(logo_elp_path):
            try:
                with open(logo_elp_path, 'rb') as logo_file:
                    logo_elp_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Erro ao carregar logo ELP: {e}")

        # Renderizar template
        template = Template(template_html)
        html_content = template.render(
            relatorio=relatorio_express,
            fotos=fotos_processadas,
            checklist_items=checklist_items,
            logo_elp=logo_elp_base64,
            logo_cliente=logo_cliente_base64,
            datetime=datetime
        )

        # Gerar PDF
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(output_path)

        return {
            'success': True,
            'pdf_path': output_path,
            'message': 'PDF gerado com sucesso'
        }

    except Exception as e:
        print(f"Erro ao gerar PDF: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': f'Erro ao gerar PDF: {str(e)}'
        }