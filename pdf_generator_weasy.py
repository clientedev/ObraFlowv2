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
        """Template HTML seguindo exatamente o modelo das screenshots"""
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ data.titulo }}</title>
</head>
<body>
    <!-- Cabeçalho com logo ELP e título -->
    <div class="header-section">
        <div class="logo-container">
            <svg class="elp-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40">
                <!-- Logo ELP -->
                <rect x="8" y="8" width="24" height="24" fill="none" stroke="#4A90E2" stroke-width="2"/>
                <rect x="12" y="12" width="8" height="8" fill="#4A90E2"/>
                <rect x="20" y="12" width="8" height="8" fill="none" stroke="#4A90E2" stroke-width="1"/>
                <rect x="12" y="20" width="8" height="8" fill="none" stroke="#4A90E2" stroke-width="1"/>
                <rect x="20" y="20" width="8" height="8" fill="#4A90E2"/>
                
                <!-- Texto ELP -->
                <text x="38" y="20" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#333">ELP</text>
                <text x="38" y="30" font-family="Arial, sans-serif" font-size="8" fill="#666">CONSULTORIA</text>
            </svg>
        </div>
        
        <h1 class="main-title">{{ data.titulo }}</h1>
        
        <div class="date-info">Em: {{ data.data_atual }}</div>
    </div>

    <!-- Seção Relatório com fundo cinza -->
    <div class="report-section">
        <div class="section-header">Relatório</div>
        <div class="report-content">
            <div class="report-label">Relatório Número</div>
            <div class="report-number">{{ data.numero_relatorio }}</div>
        </div>
    </div>

    <!-- Dados Gerais com fundo cinza -->
    <div class="dados-section">
        <div class="section-header">Dados gerais</div>
        <div class="dados-table">
            <div class="dados-row header-row">
                <div class="dados-cell">Empresa</div>
                <div class="dados-cell">Obra</div>
                <div class="dados-cell">Endereço</div>
            </div>
            <div class="dados-row value-row">
                <div class="dados-cell">{{ data.empresa }}</div>
                <div class="dados-cell">{{ data.obra }}</div>
                <div class="dados-cell">{{ data.endereco }}</div>
            </div>
        </div>
    </div>

    <!-- Itens Observados com fundo cinza -->
    <div class="observacoes-section">
        <div class="section-header">Itens observados</div>
        <div class="observacoes-content">
            {% if data.observacoes %}
                <div class="obs-text">{{ data.observacoes }}</div>
            {% else %}
                <div class="obs-text">..</div>
                <div class="obs-text">Vide fotos.</div>
            {% endif %}
        </div>
        
        <!-- Fotos em grade -->
        {% if data.fotos %}
        <div class="photos-grid">
            {% for foto in data.fotos %}
            <div class="photo-item">
                {% if foto.base64 and not foto.not_found %}
                    <div class="photo-wrapper">
                        <img src="data:image/jpeg;base64,{{ foto.base64 }}" alt="Foto {{ foto.ordem }}" class="photo-img">
                    </div>
                {% else %}
                    <div class="photo-placeholder">Foto não disponível</div>
                {% endif %}
                <div class="photo-caption">{{ foto.legenda }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <!-- Assinaturas com fundo cinza -->
    <div class="assinaturas-section">
        <div class="section-header">Assinaturas</div>
        <div class="assinaturas-table">
            <div class="assin-row header-row">
                <div class="assin-cell">Preenchido por:</div>
                <div class="assin-cell">Liberado por:</div>
                <div class="assin-cell">Responsável pelo acompanhamento</div>
            </div>
            <div class="assin-row value-row">
                <div class="assin-cell">{{ data.preenchido_por }}</div>
                <div class="assin-cell">{{ data.liberado_por }}</div>
                <div class="assin-cell">{{ data.responsavel }}</div>
            </div>
        </div>
    </div>

    <!-- Rodapé ELP -->
    <div class="footer-section">
        <div class="footer-left">
            <svg class="footer-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 30">
                <rect x="4" y="6" width="18" height="18" fill="none" stroke="#4A90E2" stroke-width="1.5"/>
                <rect x="7" y="9" width="6" height="6" fill="#4A90E2"/>
                <rect x="13" y="9" width="6" height="6" fill="none" stroke="#4A90E2" stroke-width="0.8"/>
                <rect x="7" y="15" width="6" height="6" fill="none" stroke="#4A90E2" stroke-width="0.8"/>
                <rect x="13" y="15" width="6" height="6" fill="#4A90E2"/>
                <text x="26" y="17" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#333">ELP</text>
            </svg>
            <div class="company-info">
                <div class="company-name">ELP Consultoria</div>
                <div>Rua Jaboticabal, 530 apto. 31 - São Paulo - SP - CEP: 03188-000</div>
                <div><a href="mailto:leopoldo@elpconsultoria.eng.br">leopoldo@elpconsultoria.eng.br</a></div>
                <div>Telefone: (11) 99138-4517</div>
            </div>
        </div>
        <div class="footer-right">
            <div class="generated-info">Relatório gerado no <span class="produttivo">Produttivo</span></div>
        </div>
    </div>
</body>
</html>
        """
    
    def _create_css_styles(self):
        """CSS seguindo exatamente as screenshots do modelo"""
        return """
@page {
    size: A4;
    margin: 1.5cm 2cm 2cm 2cm;
}

* {
    box-sizing: border-box;
}

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    line-height: 1.2;
    color: #333333;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}

/* Cabeçalho */
.header-section {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 2cm;
    padding-bottom: 0.5cm;
}

.logo-container {
    width: 120px;
    height: 40px;
}

.elp-logo {
    width: 100%;
    height: 100%;
}

.main-title {
    font-size: 24pt;
    font-weight: normal;
    color: #333333;
    text-align: center;
    margin: 0;
    flex: 1;
}

.date-info {
    font-size: 11pt;
    color: #333333;
    white-space: nowrap;
}

/* Seções com fundo cinza */
.report-section,
.dados-section,
.observacoes-section,
.assinaturas-section {
    background-color: #f5f5f5;
    border: 1px solid #cccccc;
    margin-bottom: 8px;
    padding: 0;
    break-inside: avoid;
}

.section-header {
    background-color: #e8e8e8;
    font-weight: bold;
    font-size: 12pt;
    color: #333333;
    padding: 8px 12px;
    border-bottom: 1px solid #cccccc;
    margin: 0;
}

/* Seção Relatório */
.report-content {
    padding: 12px;
}

.report-label {
    font-size: 11pt;
    color: #333333;
    margin-bottom: 4px;
}

.report-number {
    font-size: 14pt;
    font-weight: bold;
    color: #333333;
}

/* Dados Gerais - Tabela */
.dados-table {
    width: 100%;
    border-collapse: collapse;
}

.dados-row {
    display: flex;
    width: 100%;
}

.dados-cell {
    flex: 1;
    padding: 8px 12px;
    border-right: 1px solid #cccccc;
    vertical-align: top;
}

.dados-cell:last-child {
    border-right: none;
}

.header-row .dados-cell {
    font-weight: bold;
    font-size: 11pt;
    background-color: #e8e8e8;
    color: #333333;
}

.value-row .dados-cell {
    font-size: 11pt;
    background-color: #f5f5f5;
    color: #333333;
    min-height: 40px;
}

/* Itens Observados */
.observacoes-content {
    padding: 12px;
}

.obs-text {
    font-size: 11pt;
    color: #333333;
    margin: 0 0 6px 0;
}

/* Grid de Fotos - Responsivo */
.photos-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    padding: 15px;
    margin-top: 10px;
}

.photo-item {
    text-align: center;
}

.photo-wrapper {
    border: 1px solid #ddd;
    overflow: hidden;
    background: white;
    margin-bottom: 8px;
}

.photo-img {
    width: 100%;
    height: auto;
    max-height: 200px;
    object-fit: cover;
    display: block;
}

.photo-placeholder {
    width: 100%;
    height: 120px;
    background-color: #f0f0f0;
    border: 1px dashed #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    font-size: 10pt;
    margin-bottom: 8px;
}

.photo-caption {
    font-size: 9pt;
    color: #333333;
    line-height: 1.2;
    margin: 0;
    text-align: left;
    font-weight: normal;
}

/* Mais de 2 fotos - ajustar grid */
.photos-grid:has(.photo-item:nth-child(3)) {
    grid-template-columns: 1fr 1fr;
}

.photos-grid:has(.photo-item:nth-child(5)) {
    grid-template-columns: 1fr 1fr 1fr;
}

.photos-grid:has(.photo-item:nth-child(5)) .photo-img {
    max-height: 150px;
}

.photos-grid:has(.photo-item:nth-child(5)) .photo-caption {
    font-size: 8pt;
}

/* Assinaturas - Tabela */
.assinaturas-table {
    width: 100%;
    border-collapse: collapse;
}

.assin-row {
    display: flex;
    width: 100%;
}

.assin-cell {
    flex: 1;
    padding: 8px 12px;
    border-right: 1px solid #cccccc;
    vertical-align: top;
}

.assin-cell:last-child {
    border-right: none;
}

.header-row .assin-cell {
    font-weight: bold;
    font-size: 11pt;
    background-color: #e8e8e8;
    color: #333333;
}

.value-row .assin-cell {
    font-size: 11pt;
    background-color: #f5f5f5;
    color: #333333;
    min-height: 40px;
}

/* Rodapé */
.footer-section {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 1cm 2cm;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    background: white;
    border-top: 1px solid #ddd;
}

.footer-left {
    display: flex;
    align-items: flex-start;
    gap: 12px;
}

.footer-logo {
    width: 60px;
    height: 30px;
    flex-shrink: 0;
}

.company-info {
    font-size: 9pt;
    color: #666666;
    line-height: 1.2;
}

.company-name {
    font-weight: bold;
    color: #333333;
    margin-bottom: 2px;
}

.company-info a {
    color: #4A90E2;
    text-decoration: none;
}

.footer-right {
    text-align: right;
}

.generated-info {
    font-size: 9pt;
    color: #666666;
}

.produttivo {
    color: #4A90E2;
    font-weight: bold;
}

/* Ajustes para caber em uma página */
@media print {
    .photos-grid:has(.photo-item:nth-child(3)) .photo-img {
        max-height: 160px;
    }
    
    .photos-grid:has(.photo-item:nth-child(4)) .photo-img {
        max-height: 140px;
    }
    
    .photos-grid:has(.photo-item:nth-child(5)) .photo-img {
        max-height: 120px;
    }
}

/* Quebras de página */
.report-section,
.dados-section,
.observacoes-section,
.assinaturas-section {
    break-inside: avoid;
}
        """