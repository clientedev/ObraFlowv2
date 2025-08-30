"""
Gerador de PDF usando WeasyPrint para replicar exatamente o modelo Artesano
"""

import os
import json
from datetime import datetime
from weasyprint import HTML, CSS
from jinja2 import Template
from flask import current_app

class WeasyPrintReportGenerator:
    def __init__(self):
        self.template_html = self._create_html_template()
        self.template_css = self._create_css_styles()
    
    def generate_report_pdf(self, relatorio, fotos=None, output_path=None):
        """
        Gera PDF do relatório usando WeasyPrint
        
        Args:
            relatorio: Objeto do relatório com dados
            fotos: Lista de fotos do relatório
            output_path: Caminho para salvar o arquivo (opcional)
            
        Returns:
            bytes ou caminho do arquivo gerado
        """
        try:
            # Preparar dados para o template
            data = self._prepare_report_data(relatorio, fotos)
            
            # Renderizar HTML com os dados
            template = Template(self.template_html)
            html_content = template.render(data=data)
            
            # Gerar PDF
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=self.template_css)
            
            if output_path:
                html_doc.write_pdf(output_path, stylesheets=[css_doc])
                return output_path
            else:
                pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc])
                return pdf_bytes
                
        except Exception as e:
            raise Exception(f"Erro ao gerar PDF com WeasyPrint: {str(e)}")
    
    def _prepare_report_data(self, relatorio, fotos):
        """Preparar dados do relatório para o template"""
        projeto = relatorio.projeto
        
        # Dados básicos
        data = {
            'titulo': 'Relatório de Visita',
            'data_atual': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'numero_relatorio': relatorio.numero,
            'empresa': projeto.responsavel.nome_completo if projeto.responsavel else "ELP Consultoria",
            'obra': projeto.nome,
            'endereco': projeto.endereco or "Não informado",
            'observacoes': relatorio.conteudo if hasattr(relatorio, 'conteudo') and relatorio.conteudo else None,
            'preenchido_por': relatorio.autor.nome_completo if relatorio.autor else "Não informado",
            'liberado_por': "Eng. José Leopoldo Pugliese",
            'responsavel': projeto.responsavel.nome_completo if projeto.responsavel else "Não informado",
            'data_relatorio': relatorio.data_relatorio.strftime('%d/%m/%Y %H:%M') if relatorio.data_relatorio else datetime.now().strftime('%d/%m/%Y %H:%M'),
            'fotos': []
        }
        
        # Processar fotos
        if fotos:
            try:
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            except RuntimeError:
                # Se não estiver no contexto da aplicação, usar pasta padrão
                upload_folder = 'uploads'
                
            for foto in fotos:
                foto_path = os.path.join(upload_folder, foto.filename)
                if os.path.exists(foto_path):
                    # Converter para base64 para embedding no HTML
                    import base64
                    with open(foto_path, 'rb') as f:
                        foto_base64 = base64.b64encode(f.read()).decode('utf-8')
                    
                    data['fotos'].append({
                        'base64': foto_base64,
                        'legenda': foto.descricao or f"Foto {foto.ordem}",
                        'ordem': foto.ordem
                    })
                else:
                    # Adicionar placeholder para fotos não encontradas
                    data['fotos'].append({
                        'base64': None,
                        'legenda': foto.descricao or f"Foto {foto.ordem}",
                        'ordem': foto.ordem,
                        'not_found': True
                    })
        
        return data
    
    def _create_html_template(self):
        """Criar template HTML seguindo exatamente o modelo Artesano PDF"""
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ data.titulo }}</title>
</head>
<body>
    <!-- Logo superior direito -->
    <div class="logo-header">
        <div class="logo-placeholder">LOGO</div>
    </div>
    
    <!-- Título centralizado -->
    <div class="main-header">
        <h1 class="main-title">{{ data.titulo }}</h1>
    </div>
    
    <!-- Data no canto direito -->
    <div class="date-header">
        <div class="date-info">Em: {{ data.data_atual }}</div>
    </div>
    
    <!-- Espaçamento grande -->
    <div class="spacer-large"></div>
    
    <!-- Seção Relatório -->
    <div class="section-report">
        <h2 class="report-header">Relatório</h2>
        <div class="report-number-section">
            <div class="report-number-label">Relatório Número</div>
            <div class="report-number">{{ data.numero_relatorio }}</div>
        </div>
    </div>
    
    <!-- Dados Gerais com linhas de tabela -->
    <div class="section-dados">
        <h3 class="section-title">Dados gerais</h3>
        <div class="data-table">
            <div class="data-row-header">
                <div class="data-cell-header">Empresa</div>
                <div class="data-cell-header">Obra</div>
                <div class="data-cell-header">Endereço</div>
            </div>
            <div class="data-row-values">
                <div class="data-cell-value">{{ data.empresa }}</div>
                <div class="data-cell-value">{{ data.obra }}</div>
                <div class="data-cell-value">{{ data.endereco }}</div>
            </div>
        </div>
    </div>
    
    <!-- Itens Observados -->
    <div class="section-observacoes">
        <h3 class="section-title">Itens observados</h3>
        <div class="observations">
            {% if data.observacoes %}
                <p class="obs-text">{{ data.observacoes }}</p>
            {% else %}
                <p class="obs-text">..</p>
                <p class="obs-text">Vide fotos.</p>
            {% endif %}
            <div class="dots-separator">
                <span class="dot-left">.</span>
                <span class="dot-right">.</span>
            </div>
        </div>
        
        <!-- Fotos lado a lado -->
        {% if data.fotos %}
        <div class="photos-section">
            {% for foto in data.fotos %}
                {% if loop.index0 % 2 == 0 %}
                <div class="photo-row">
                {% endif %}
                    <div class="photo-container">
                        {% if foto.base64 and not foto.not_found %}
                            <img src="data:image/jpeg;base64,{{ foto.base64 }}" alt="Foto {{ foto.ordem }}" class="photo">
                        {% else %}
                            <div class="photo-placeholder-box">Foto não disponível</div>
                        {% endif %}
                        <div class="photo-caption">{{ foto.legenda }}</div>
                    </div>
                {% if loop.index0 % 2 == 1 or loop.last %}
                </div>
                {% endif %}
            {% endfor %}
        </div>
        {% endif %}
    </div>
    
    <!-- Assinaturas com linhas de tabela -->
    <div class="section-assinaturas">
        <h3 class="section-title">Assinaturas</h3>
        <div class="signatures-table">
            <div class="sig-row-header">
                <div class="sig-cell-header">Preenchido por:</div>
                <div class="sig-cell-header">Liberado por:</div>
                <div class="sig-cell-header">Responsável pelo acompanhamento</div>
            </div>
            <div class="sig-row-values">
                <div class="sig-cell-value">{{ data.preenchido_por }}</div>
                <div class="sig-cell-value">{{ data.liberado_por }}</div>
                <div class="sig-cell-value">{{ data.responsavel }}</div>
            </div>
        </div>
    </div>
    
    <!-- Rodapé fixo -->
    <div class="footer">
        <div class="footer-content">
            <div class="footer-left">
                <div class="company-name"><strong>ELP Consultoria</strong></div>
                <div>Rua Jaboticabal, 530 apto. 31 - São Paulo - SP - CEP: 03188-000</div>
                <div>leopoldo@elpconsultoria.eng.br</div>
                <div>Telefone: (11) 99138-4517</div>
            </div>
            <div class="footer-right">
                <div>Relatório gerado no Produttivo</div>
            </div>
        </div>
    </div>
</body>
</html>
        """
    
    def _create_css_styles(self):
        """Criar estilos CSS seguindo pixel-perfect o modelo Artesano"""
        return """
@page {
    size: A4;
    margin: 2cm 2cm 3cm 2cm;
    
    @top-center {
        content: "";
    }
    
    @bottom-center {
        content: "";
    }
}

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    line-height: 1.0;
    color: #000000;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}

/* Logo no canto superior direito */
.logo-header {
    position: absolute;
    top: 1cm;
    right: 2cm;
    width: 60px;
    height: 40px;
}

.logo-placeholder {
    background-color: #e0e0e0;
    color: #666666;
    font-size: 8pt;
    text-align: center;
    line-height: 40px;
    border: 1px solid #cccccc;
}

/* Título centralizado */
.main-header {
    text-align: center;
    margin-top: 1.5cm;
    margin-bottom: 0;
}

.main-title {
    font-size: 14pt;
    font-weight: bold;
    color: #000000;
    margin: 0;
    padding: 0;
}

/* Data no canto direito */
.date-header {
    text-align: right;
    margin-top: 4cm;
    margin-bottom: 0;
}

.date-info {
    font-size: 11pt;
    color: #000000;
}

/* Espaçamento grande */
.spacer-large {
    height: 2.5cm;
}

/* Seção Relatório */
.section-report {
    margin-bottom: 1.5cm;
}

.report-header {
    font-size: 14pt;
    font-weight: bold;
    color: #000000;
    margin: 0 0 8px 0;
}

.report-number-section {
    margin-top: 8px;
}

.report-number-label {
    font-size: 11pt;
    color: #000000;
    margin-bottom: 2px;
}

.report-number {
    font-size: 18pt;
    font-weight: bold;
    color: #000000;
    margin-top: 2px;
}

/* Títulos de seção */
.section-title {
    font-size: 12pt;
    font-weight: bold;
    color: #000000;
    margin: 0 0 10px 0;
}

/* Seção Dados Gerais com tabela */
.section-dados {
    margin-bottom: 1.5cm;
}

.data-table {
    border-collapse: collapse;
    width: 100%;
}

.data-row-header,
.data-row-values {
    display: flex;
    width: 100%;
}

.data-cell-header,
.data-cell-value {
    flex: 1;
    padding: 8px 5px;
    border-bottom: 1px solid #cccccc;
    text-align: left;
    vertical-align: top;
}

.data-cell-header {
    font-weight: bold;
    font-size: 11pt;
    color: #000000;
    background-color: #f8f8f8;
}

.data-cell-value {
    font-size: 11pt;
    color: #000000;
    background-color: #ffffff;
}

/* Seção Itens Observados */
.section-observacoes {
    margin-bottom: 1.5cm;
}

.observations {
    margin-bottom: 15px;
}

.obs-text {
    font-size: 11pt;
    color: #000000;
    margin: 0 0 5px 0;
    line-height: 1.2;
}

.dots-separator {
    display: flex;
    justify-content: space-between;
    margin: 20px 0;
    height: 15px;
}

.dot-left,
.dot-right {
    font-size: 11pt;
    color: #000000;
}

/* Seção de Fotos */
.photos-section {
    margin-top: 25px;
    margin-bottom: 20px;
}

.photo-row {
    display: flex;
    gap: 40px;
    margin-bottom: 20px;
    justify-content: space-around;
}

.photo-container {
    text-align: center;
    flex: 1;
    max-width: 45%;
}

.photo {
    width: 100%;
    max-width: 250px;
    height: auto;
    border: 1px solid #e0e0e0;
}

.photo-caption {
    font-size: 10pt;
    color: #000000;
    text-align: center;
    margin-top: 8px;
    line-height: 1.2;
    font-weight: normal;
}

.photo-placeholder-box {
    width: 100%;
    max-width: 250px;
    height: 180px;
    background-color: #f5f5f5;
    border: 1px dashed #cccccc;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666666;
    font-size: 10pt;
}

/* Seção Assinaturas com tabela */
.section-assinaturas {
    margin-bottom: 2cm;
    break-inside: avoid;
}

.signatures-table {
    border-collapse: collapse;
    width: 100%;
}

.sig-row-header,
.sig-row-values {
    display: flex;
    width: 100%;
}

.sig-cell-header,
.sig-cell-value {
    flex: 1;
    padding: 8px 5px;
    border-bottom: 1px solid #cccccc;
    text-align: left;
    vertical-align: top;
}

.sig-cell-header {
    font-weight: bold;
    font-size: 11pt;
    color: #000000;
    background-color: #f8f8f8;
}

.sig-cell-value {
    font-size: 11pt;
    color: #000000;
    background-color: #ffffff;
    padding-top: 15px;
}

/* Rodapé fixo */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 0 2cm 1cm 2cm;
}

.footer-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    font-size: 9pt;
    color: #000000;
    line-height: 1.1;
}

.footer-left {
    flex: 1;
}

.footer-right {
    text-align: right;
}

.company-name {
    margin-bottom: 3px;
}

/* Quebras de página */
.section-report,
.section-dados,
.section-observacoes,
.section-assinaturas {
    break-inside: avoid;
}

.photo-row {
    break-inside: avoid;
}
        """