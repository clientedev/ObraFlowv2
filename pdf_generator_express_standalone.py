"""
PDF Generator para Relatório Express Standalone
Gera PDFs sem vínculo com projeto/empresa cadastrada
"""

import os
import base64
from datetime import datetime
from io import BytesIO
from flask import current_app
from weasyprint import HTML, CSS
from jinja2 import Template


def gerar_pdf_relatorio_express_standalone(relatorio_id, salvar_arquivo=True):
    """
    Gerar PDF do relatório express standalone usando WeasyPrint
    
    Args:
        relatorio_id: ID do relatório express standalone
        salvar_arquivo: Se deve salvar o arquivo no disco
    
    Returns:
        Caminho do arquivo gerado ou BytesIO se salvar_arquivo=False
    """
    from models import RelatorioExpressStandalone, FotoRelatorioExpressStandalone
    
    try:
        # Buscar o relatório express standalone
        relatorio = RelatorioExpressStandalone.query.get_or_404(relatorio_id)
        
        # Buscar fotos
        fotos = FotoRelatorioExpressStandalone.query.filter_by(
            relatorio_id=relatorio_id
        ).order_by(FotoRelatorioExpressStandalone.ordem).all()
        
        # Preparar dados das fotos com base64
        fotos_data = []
        for foto in fotos:
            foto_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), foto.filename)
            if os.path.exists(foto_path):
                with open(foto_path, 'rb') as f:
                    foto_base64 = base64.b64encode(f.read()).decode('utf-8')
                    fotos_data.append({
                        'base64': foto_base64,
                        'legenda': foto.legenda,
                        'categoria': foto.categoria,
                        'filename': foto.filename
                    })
        
        # Preparar logo da empresa se disponível
        empresa_logo_base64 = None
        if relatorio.empresa_logo_filename:
            logo_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), relatorio.empresa_logo_filename)
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    empresa_logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Logo ELP (fixo)
        elp_logo_path = os.path.join('static', 'logo_elp_final.jpg')
        elp_logo_base64 = None
        if os.path.exists(elp_logo_path):
            with open(elp_logo_path, 'rb') as f:
                elp_logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Preparar dados para o template
        dados = {
            'relatorio': relatorio,
            'fotos': fotos_data,
            'data_atual': datetime.now().strftime('%d/%m/%Y'),
            'hora_atual': datetime.now().strftime('%H:%M'),
            'autor': relatorio.autor.nome_completo,
            'empresa_logo_base64': empresa_logo_base64,
            'elp_logo_base64': elp_logo_base64,
            'total_fotos': len(fotos_data)
        }
        
        # Template HTML do relatório express standalone
        html_template = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório Express {{ relatorio.numero }}</title>
            <style>
                @page {
                    size: A4;
                    margin: 2cm 1.5cm;
                    @bottom-center {
                        content: "Página " counter(page) " de " counter(pages);
                        font-size: 10px;
                        color: #666;
                    }
                }
                
                body {
                    font-family: 'Arial', 'Helvetica', sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }
                
                .header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding-bottom: 20px;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #20c1e8;
                }
                
                .header-left {
                    flex: 1;
                }
                
                .header-center {
                    flex: 2;
                    text-align: center;
                }
                
                .header-right {
                    flex: 1;
                    text-align: right;
                }
                
                .logo {
                    max-height: 60px;
                    max-width: 150px;
                }
                
                .empresa-logo {
                    max-height: 50px;
                    max-width: 120px;
                }
                
                .titulo-principal {
                    font-size: 18px;
                    font-weight: bold;
                    color: #343a40;
                    margin: 10px 0;
                }
                
                .subtitulo {
                    font-size: 14px;
                    color: #666;
                }
                
                .secao {
                    margin-bottom: 25px;
                    page-break-inside: avoid;
                }
                
                .secao-titulo {
                    background-color: #343a40;
                    color: white;
                    padding: 8px 12px;
                    font-size: 14px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    border-radius: 4px;
                }
                
                .dados-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 15px;
                }
                
                .campo {
                    margin-bottom: 10px;
                }
                
                .campo-label {
                    font-weight: bold;
                    color: #343a40;
                    margin-bottom: 3px;
                }
                
                .campo-valor {
                    color: #555;
                    word-wrap: break-word;
                }
                
                .fotos-container {
                    margin-top: 20px;
                }
                
                .foto-item {
                    margin-bottom: 30px;
                    page-break-inside: avoid;
                    text-align: center;
                }
                
                .foto-img {
                    max-width: 100%;
                    max-height: 400px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                
                .foto-legenda {
                    font-style: italic;
                    color: #666;
                    margin-top: 8px;
                    font-size: 11px;
                }
                
                .categoria-badge {
                    background-color: #20c1e8;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 10px;
                    margin-right: 5px;
                }
                
                .rodape {
                    position: fixed;
                    bottom: 1cm;
                    left: 1.5cm;
                    right: 1.5cm;
                    text-align: center;
                    font-size: 10px;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding-top: 10px;
                }
                
                @media print {
                    .foto-item {
                        page-break-inside: avoid;
                    }
                }
            </style>
        </head>
        <body>
            <!-- Cabeçalho -->
            <div class="header">
                <div class="header-left">
                    {% if elp_logo_base64 %}
                    <img src="data:image/jpeg;base64,{{ elp_logo_base64 }}" alt="ELP Logo" class="logo">
                    {% endif %}
                </div>
                <div class="header-center">
                    <div class="titulo-principal">{{ relatorio.titulo_relatorio }}</div>
                    <div class="subtitulo">Relatório {{ relatorio.numero }}</div>
                    <div class="subtitulo">{{ dados.data_atual }}</div>
                </div>
                <div class="header-right">
                    {% if empresa_logo_base64 %}
                    <img src="data:image/jpeg;base64,{{ empresa_logo_base64 }}" alt="Logo Cliente" class="empresa-logo">
                    {% endif %}
                </div>
            </div>
            
            <!-- Dados da Empresa -->
            <div class="secao">
                <div class="secao-titulo">DADOS DA EMPRESA</div>
                <div class="dados-grid">
                    <div class="campo">
                        <div class="campo-label">Nome da Empresa:</div>
                        <div class="campo-valor">{{ relatorio.empresa_nome }}</div>
                    </div>
                    <div class="campo">
                        <div class="campo-label">Contato:</div>
                        <div class="campo-valor">{{ relatorio.empresa_contato or '-' }}</div>
                    </div>
                    <div class="campo">
                        <div class="campo-label">Telefone:</div>
                        <div class="campo-valor">{{ relatorio.empresa_telefone or '-' }}</div>
                    </div>
                    <div class="campo">
                        <div class="campo-label">E-mail:</div>
                        <div class="campo-valor">{{ relatorio.empresa_email or '-' }}</div>
                    </div>
                    {% if relatorio.empresa_cnpj %}
                    <div class="campo">
                        <div class="campo-label">CNPJ:</div>
                        <div class="campo-valor">{{ relatorio.empresa_cnpj }}</div>
                    </div>
                    {% endif %}
                </div>
                {% if relatorio.empresa_endereco %}
                <div class="campo">
                    <div class="campo-label">Endereço:</div>
                    <div class="campo-valor">{{ relatorio.empresa_endereco }}</div>
                </div>
                {% endif %}
            </div>
            
            <!-- Dados do Projeto -->
            <div class="secao">
                <div class="secao-titulo">DADOS DO PROJETO</div>
                <div class="dados-grid">
                    <div class="campo">
                        <div class="campo-label">Nome do Projeto:</div>
                        <div class="campo-valor">{{ relatorio.projeto_nome }}</div>
                    </div>
                    <div class="campo">
                        <div class="campo-label">Endereço:</div>
                        <div class="campo-valor">{{ relatorio.projeto_endereco }}</div>
                    </div>
                    {% if relatorio.tipo_obra %}
                    <div class="campo">
                        <div class="campo-label">Tipo de Obra:</div>
                        <div class="campo-valor">{{ relatorio.tipo_obra }}</div>
                    </div>
                    {% endif %}
                    {% if relatorio.data_inicio %}
                    <div class="campo">
                        <div class="campo-label">Data de Início:</div>
                        <div class="campo-valor">{{ relatorio.data_inicio.strftime('%d/%m/%Y') }}</div>
                    </div>
                    {% endif %}
                    {% if relatorio.data_previsao_fim %}
                    <div class="campo">
                        <div class="campo-label">Previsão de Término:</div>
                        <div class="campo-valor">{{ relatorio.data_previsao_fim.strftime('%d/%m/%Y') }}</div>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Dados da Visita -->
            <div class="secao">
                <div class="secao-titulo">DADOS DA VISITA</div>
                <div class="dados-grid">
                    <div class="campo">
                        <div class="campo-label">Data da Visita:</div>
                        <div class="campo-valor">{{ relatorio.data_visita.strftime('%d/%m/%Y') }}</div>
                    </div>
                    {% if relatorio.hora_inicio %}
                    <div class="campo">
                        <div class="campo-label">Hora de Início:</div>
                        <div class="campo-valor">{{ relatorio.hora_inicio.strftime('%H:%M') }}</div>
                    </div>
                    {% endif %}
                    {% if relatorio.hora_fim %}
                    <div class="campo">
                        <div class="campo-label">Hora de Término:</div>
                        <div class="campo-valor">{{ relatorio.hora_fim.strftime('%H:%M') }}</div>
                    </div>
                    {% endif %}
                    <div class="campo">
                        <div class="campo-label">Responsável:</div>
                        <div class="campo-valor">{{ autor }}</div>
                    </div>
                    {% if relatorio.clima %}
                    <div class="campo">
                        <div class="campo-label">Clima:</div>
                        <div class="campo-valor">{{ relatorio.clima }}</div>
                    </div>
                    {% endif %}
                    {% if relatorio.temperatura %}
                    <div class="campo">
                        <div class="campo-label">Temperatura:</div>
                        <div class="campo-valor">{{ relatorio.temperatura }}</div>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Observações Gerais -->
            {% if relatorio.observacoes_gerais %}
            <div class="secao">
                <div class="secao-titulo">OBSERVAÇÕES GERAIS</div>
                <div class="campo-valor">{{ relatorio.observacoes_gerais | replace('\n', '<br>') | safe }}</div>
            </div>
            {% endif %}
            
            <!-- Problemas Identificados -->
            {% if relatorio.problemas_identificados %}
            <div class="secao">
                <div class="secao-titulo">PROBLEMAS IDENTIFICADOS</div>
                <div class="campo-valor">{{ relatorio.problemas_identificados | replace('\n', '<br>') | safe }}</div>
            </div>
            {% endif %}
            
            <!-- Recomendações -->
            {% if relatorio.recomendacoes %}
            <div class="secao">
                <div class="secao-titulo">RECOMENDAÇÕES</div>
                <div class="campo-valor">{{ relatorio.recomendacoes | replace('\n', '<br>') | safe }}</div>
            </div>
            {% endif %}
            
            <!-- Conclusões -->
            {% if relatorio.conclusoes %}
            <div class="secao">
                <div class="secao-titulo">CONCLUSÕES</div>
                <div class="campo-valor">{{ relatorio.conclusoes | replace('\n', '<br>') | safe }}</div>
            </div>
            {% endif %}
            
            <!-- Fotos -->
            {% if fotos %}
            <div class="secao">
                <div class="secao-titulo">REGISTRO FOTOGRÁFICO</div>
                <div class="fotos-container">
                    {% for foto in fotos %}
                    <div class="foto-item">
                        <img src="data:image/jpeg;base64,{{ foto.base64 }}" alt="Foto {{ loop.index }}" class="foto-img">
                        <div class="foto-legenda">
                            <span class="categoria-badge">{{ foto.categoria }}</span>
                            {{ foto.legenda }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- Assinaturas -->
            <div class="secao">
                <div class="secao-titulo">ASSINATURAS</div>
                <div style="margin-top: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px;">
                    <div style="text-align: center;">
                        <div style="border-bottom: 1px solid #333; margin-bottom: 5px; height: 40px;"></div>
                        <div style="font-size: 11px; font-weight: bold;">{{ autor }}</div>
                        <div style="font-size: 10px; color: #666;">ELP Consultoria e Engenharia</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="border-bottom: 1px solid #333; margin-bottom: 5px; height: 40px;"></div>
                        <div style="font-size: 11px; font-weight: bold;">{{ relatorio.empresa_contato or relatorio.empresa_nome }}</div>
                        <div style="font-size: 10px; color: #666;">Cliente</div>
                    </div>
                </div>
            </div>
            
            <!-- Rodapé -->
            <div class="rodape">
                ELP Consultoria e Engenharia - Engenharia Civil & Fachadas<br>
                Relatório gerado em {{ data_atual }} às {{ hora_atual }}
            </div>
        </body>
        </html>
        """
        
        # Renderizar template
        template = Template(html_template)
        html_content = template.render(**dados)
        
        # Gerar PDF
        html_doc = HTML(string=html_content)
        
        if salvar_arquivo:
            # Salvar no disco
            filename = f"relatorio_express_standalone_{relatorio.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
            html_doc.write_pdf(output_path)
            return output_path
        else:
            # Retornar em memória
            pdf_buffer = BytesIO()
            html_doc.write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            return pdf_buffer
            
    except Exception as e:
        print(f"Erro ao gerar PDF do relatório express standalone: {str(e)}")
        raise e