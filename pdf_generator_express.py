"""
Gerador de PDF para Relatórios Express
Sistema simplificado baseado no WeasyPrint para relatórios rápidos
"""

import os
import base64
from datetime import datetime
from weasyprint import HTML, CSS
from io import BytesIO
from flask import current_app, render_template_string

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

def gerar_pdf_relatorio_express(relatorio_express_id, salvar_arquivo=True):
    """
    Gerar PDF do relatório express usando WeasyPrint
    
    Args:
        relatorio_express_id: ID do relatório express
        salvar_arquivo: Se deve salvar o arquivo no disco
    
    Returns:
        Caminho do arquivo gerado ou BytesIO se salvar_arquivo=False
    """
    from models import RelatorioExpress, FotoRelatorioExpress
    
    try:
        # Buscar o relatório express
        relatorio = RelatorioExpress.query.get_or_404(relatorio_express_id)
        projeto = relatorio.projeto
        
        # Buscar fotos
        fotos = FotoRelatorioExpress.query.filter_by(
            relatorio_express_id=relatorio_express_id
        ).order_by(FotoRelatorioExpress.ordem).all()
        
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
                        'filename': foto.filename
                    })
        
        # Preparar dados para o template
        dados = {
            'relatorio': relatorio,
            'projeto': projeto,
            'fotos': fotos_data,
            'data_atual': datetime.now().strftime('%d/%m/%Y'),
            'hora_atual': datetime.now().strftime('%H:%M'),
            'autor': relatorio.autor.nome_completo
        }
        
        # Template HTML do relatório express
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
                
                /* Cabeçalho */
                .header {
                    border-bottom: 3px solid #4ECDC4;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                
                .header-left {
                    flex: 1;
                }
                
                .header-right {
                    text-align: right;
                }
                
                .logo-empresa {
                    font-size: 20px;
                    font-weight: bold;
                    color: #2C3E50;
                    margin-bottom: 5px;
                }
                
                .subtitulo-empresa {
                    font-size: 11px;
                    color: #666;
                    font-style: italic;
                }
                
                .titulo-relatorio {
                    font-size: 24px;
                    font-weight: bold;
                    color: #4ECDC4;
                    margin: 0;
                }
                
                .numero-relatorio {
                    font-size: 14px;
                    color: #666;
                    margin: 5px 0 0 0;
                }
                
                /* Seções */
                .secao {
                    margin-bottom: 25px;
                    break-inside: avoid;
                }
                
                .secao-titulo {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2C3E50;
                    background-color: #f8f9fa;
                    padding: 8px 12px;
                    border-left: 4px solid #4ECDC4;
                    margin-bottom: 12px;
                }
                
                .dados-projeto {
                    background-color: #fafafa;
                    padding: 15px;
                    border-radius: 5px;
                }
                
                .dados-linha {
                    margin-bottom: 8px;
                }
                
                .dados-label {
                    font-weight: bold;
                    color: #2C3E50;
                    display: inline-block;
                    width: 120px;
                }
                
                .dados-valor {
                    color: #333;
                }
                
                /* Observações */
                .observacoes-texto {
                    background-color: #fff;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 15px;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
                
                /* Fotos */
                .foto-container {
                    margin-bottom: 20px;
                    break-inside: avoid;
                    text-align: center;
                }
                
                .foto-imagem {
                    max-width: 100%;
                    max-height: 400px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .foto-legenda {
                    margin-top: 8px;
                    font-size: 11px;
                    color: #666;
                    font-style: italic;
                    max-width: 80%;
                    margin-left: auto;
                    margin-right: auto;
                }
                
                /* Rodapé */
                .rodape {
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 2px solid #4ECDC4;
                    font-size: 10px;
                    color: #666;
                    text-align: center;
                }
                
                .rodape-empresa {
                    font-weight: bold;
                    color: #2C3E50;
                    margin-bottom: 5px;
                }
                
                .rodape-info {
                    margin-bottom: 3px;
                }
                
                /* Assinatura */
                .assinatura {
                    margin-top: 25px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    text-align: center;
                    font-size: 11px;
                    color: #666;
                }
                
                .assinatura-linha {
                    margin-bottom: 5px;
                }
            </style>
        </head>
        <body>
            <!-- Cabeçalho -->
            <div class="header">
                <div class="header-left">
                    <div class="logo-empresa">ELP Consultoria e Engenharia</div>
                    <div class="subtitulo-empresa">Engenharia Civil & Fachadas</div>
                </div>
                <div class="header-right">
                    <h1 class="titulo-relatorio">Relatório Express</h1>
                    <p class="numero-relatorio">Nº {{ relatorio.numero }}</p>
                </div>
            </div>
            
            <!-- Dados do Projeto -->
            <div class="secao">
                <div class="secao-titulo">Dados do Projeto</div>
                <div class="dados-projeto">
                    <div class="dados-linha">
                        <span class="dados-label">Empresa:</span>
                        <span class="dados-valor">{{ projeto.cliente or 'N/A' }}</span>
                    </div>
                    <div class="dados-linha">
                        <span class="dados-label">Projeto/Obra:</span>
                        <span class="dados-valor">{{ projeto.nome }}</span>
                    </div>
                    <div class="dados-linha">
                        <span class="dados-label">Número:</span>
                        <span class="dados-valor">{{ projeto.numero }}</span>
                    </div>
                    <div class="dados-linha">
                        <span class="dados-label">Endereço:</span>
                        <span class="dados-valor">{{ projeto.endereco or 'N/A' }}</span>
                    </div>
                    <div class="dados-linha">
                        <span class="dados-label">Responsável:</span>
                        <span class="dados-valor">{{ projeto.responsavel.nome_completo if projeto.responsavel else 'N/A' }}</span>
                    </div>
                </div>
            </div>
            
            <!-- Observações Rápidas -->
            <div class="secao">
                <div class="secao-titulo">Observações Rápidas</div>
                <div class="observacoes-texto">{{ relatorio.observacoes }}</div>
            </div>
            
            <!-- Fotos (se houver) -->
            {% if fotos %}
            <div class="secao">
                <div class="secao-titulo">Fotos</div>
                {% for foto in fotos %}
                <div class="foto-container">
                    <img src="data:image/jpeg;base64,{{ foto.base64 }}" alt="Foto" class="foto-imagem">
                    <div class="foto-legenda">{{ foto.legenda }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Assinatura -->
            <div class="assinatura">
                <div class="assinatura-linha"><strong>Emitido por:</strong> {{ autor }}</div>
                <div class="assinatura-linha"><strong>Data/Hora:</strong> {{ data_atual }} às {{ hora_atual }}</div>
            </div>
            
            <!-- Rodapé -->
            <div class="rodape">
                <div class="rodape-empresa">ELP Consultoria e Engenharia</div>
                <div class="rodape-info">Engenharia Civil & Fachadas</div>
                <div class="rodape-info">contato@elp.com.br | (11) 9999-9999</div>
                <div class="rodape-info">www.elpconsultoria.com.br</div>
            </div>
        </body>
        </html>
        """
        
        # Renderizar template
        html_content = render_template_string(html_template, **dados)
        
        if salvar_arquivo:
            # Salvar em arquivo
            filename = f"relatorio_express_{relatorio.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join('uploads', filename)
            
            # Gerar PDF
            HTML(string=html_content).write_pdf(pdf_path)
            
            return pdf_path
        else:
            # Retornar como BytesIO
            pdf_bytes = HTML(string=html_content).write_pdf()
            return BytesIO(pdf_bytes)
            
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar PDF do relatório express: {e}")
        raise e