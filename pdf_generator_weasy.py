"""
Gerador de PDF usando WeasyPrint para replicar exatamente o modelo Artesano
"""

import os
import json
from datetime import datetime
from jinja2 import Template
from flask import current_app

# Try to import WeasyPrint with graceful fallback
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  WeasyPrint não disponível: {e}")
    print("🔄 Sistema funcionará com ReportLab como fallback")
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None

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
        if not WEASYPRINT_AVAILABLE:
            # Fallback para ReportLab se WeasyPrint não estiver disponível
            try:
                from pdf_generator import ReportGenerator
                reportlab_generator = ReportGenerator()
                return reportlab_generator.generate_report_pdf(relatorio, fotos, output_path)
            except Exception as e:
                raise Exception(f"Erro: WeasyPrint não disponível e falha no fallback ReportLab: {str(e)}")
        
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
            # Fallback para ReportLab se WeasyPrint falhar
            try:
                print(f"⚠️  WeasyPrint falhou: {e}")
                print("🔄 Tentando fallback para ReportLab...")
                from pdf_generator import ReportGenerator
                reportlab_generator = ReportGenerator()
                return reportlab_generator.generate_report_pdf(relatorio, fotos, output_path)
            except Exception as fallback_error:
                raise Exception(f"Erro ao gerar PDF - WeasyPrint: {str(e)} | ReportLab: {str(fallback_error)}")
    
    def _prepare_report_data(self, relatorio, fotos):
        """Preparar dados do relatório para o template"""
        projeto = relatorio.projeto
        
        # Carregar logo em base64
        logo_base64 = ""
        try:
            logo_path = os.path.join('static', 'logo_elp_new.jpg')
            if os.path.exists(logo_path):
                import base64
                with open(logo_path, 'rb') as f:
                    logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
        
        # Dados básicos - CHECKLIST REMOVIDO
        observacoes_filtradas = None
        if hasattr(relatorio, 'conteudo') and relatorio.conteudo:
            # Filtrar conteúdo para remover checklist
            content_lines = relatorio.conteudo.split('\n')
            filtered_lines = []
            in_checklist = False
            
            for line in content_lines:
                if 'CHECKLIST DA OBRA:' in line:
                    in_checklist = True
                    continue
                elif 'LOCALIZAÇÃO DO RELATÓRIO:' in line:
                    in_checklist = False
                    filtered_lines.append(line)
                    continue
                elif not in_checklist or not (line.startswith('✓') or line.startswith('○') or line.strip().startswith('Observações:')):
                    if not in_checklist:
                        filtered_lines.append(line)
            
            observacoes_filtradas = '\n'.join(filtered_lines).strip()
        
        data = {
            'titulo': 'Relatório de Visita',
            'data_atual': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'numero_relatorio': relatorio.numero,
            'empresa': projeto.responsavel.nome_completo if projeto.responsavel else "ELP Consultoria",
            'obra': projeto.nome,
            'endereco': projeto.endereco or "Não informado",
            'observacoes': observacoes_filtradas,
            'preenchido_por': relatorio.autor.nome_completo if relatorio.autor else "Não informado",
            'liberado_por': "Eng. José Leopoldo Pugliese",
            'responsavel': projeto.responsavel.nome_completo if projeto.responsavel else "Não informado",
            'data_relatorio': relatorio.data_relatorio.strftime('%d/%m/%Y %H:%M') if relatorio.data_relatorio else datetime.now().strftime('%d/%m/%Y %H:%M'),
            'logo_base64': logo_base64,
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
                    
                    # Criar legenda completa incluindo a legenda pré-definida
                    legenda_completa = foto.descricao or f"Foto {foto.ordem}"
                    if hasattr(foto, 'legenda') and foto.legenda:
                        legenda_completa += f" - {foto.legenda}"
                    
                    data['fotos'].append({
                        'base64': foto_base64,
                        'legenda': legenda_completa,
                        'ordem': foto.ordem
                    })
                else:
                    # Criar legenda completa incluindo a legenda pré-definida
                    legenda_completa = foto.descricao or f"Foto {foto.ordem}"
                    if hasattr(foto, 'legenda') and foto.legenda:
                        legenda_completa += f" - {foto.legenda}"
                    
                    # Adicionar placeholder para fotos não encontradas
                    data['fotos'].append({
                        'base64': None,
                        'legenda': legenda_completa,
                        'ordem': foto.ordem,
                        'not_found': True
                    })
        
        return data
    
    def _create_html_template(self):
        """Template HTML replicando EXATAMENTE o modelo: 2 fotos na 1ª página, 4 nas demais"""
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
            <img src="data:image/jpeg;base64,{{ data.logo_base64 }}" alt="ELP Consultoria" class="elp-logo">
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
    </div>

    <!-- PRIMEIRA PÁGINA: 2 IMAGENS LOGO ABAIXO DE "ITENS OBSERVADOS" -->
    {% if data.fotos %}
    {% set first_page_photos = data.fotos[:2] %}
    {% if first_page_photos %}
    <div class="first-page-photos">
        {% for foto in first_page_photos %}
        <div class="first-photo-container">
            {% if foto.base64 and not foto.not_found %}
                <img src="data:image/jpeg;base64,{{ foto.base64 }}" alt="Foto {{ foto.ordem }}" class="first-photo-img">
            {% else %}
                <div class="photo-placeholder-first">Foto não disponível</div>
            {% endif %}
            <div class="first-photo-caption">Foto {{ foto.ordem }} - {{ foto.legenda }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- DEMAIS PÁGINAS: 4 IMAGENS POR PÁGINA EM GRID 2x2 -->
    {% set remaining_photos = data.fotos[2:] %}
    {% for batch_start in range(0, remaining_photos|length, 4) %}
    <div class="page-break-before grid-photos-page">
        <div class="photos-grid-2x2">
            {% for foto in remaining_photos[batch_start:batch_start+4] %}
            {% if foto %}
            <div class="grid-photo-item">
                {% if foto.base64 and not foto.not_found %}
                    <img src="data:image/jpeg;base64,{{ foto.base64 }}" alt="Foto {{ foto.ordem }}" class="grid-photo-img">
                {% else %}
                    <div class="photo-placeholder-grid">Foto não disponível</div>
                {% endif %}
                <div class="grid-photo-caption">Foto {{ foto.ordem }} - {{ foto.legenda }}</div>
            </div>
            {% endif %}
            {% endfor %}
        </div>
    </div>
    {% endfor %}
    {% endif %}

    <!-- ASSINATURAS - SEMPRE NO FINAL após todas as imagens -->
    <div class="page-break-before assinaturas-page">
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
    </div>

    <!-- Rodapé ELP -->
    <div class="footer-section">
        <div class="footer-left">
            <img src="data:image/jpeg;base64,{{ data.logo_base64 }}" alt="ELP Consultoria" class="footer-logo">
            <div class="company-info">
                <div class="company-name">ELP Consultoria</div>
                <div>Rua Jaboticabal, 530 apto. 31 - São Paulo - SP - CEP: 03188-000</div>
                <div><a href="mailto:leopoldo@elpconsultoria.eng.br">leopoldo@elpconsultoria.eng.br</a></div>
                <div><a href="https://www.elpconsultoria.com" target="_blank">www.elpconsultoria.com</a></div>
                <div>Telefone: (11) 99138-4517</div>
            </div>
        </div>
        <div class="footer-right">
            <!-- Texto removido conforme solicitação -->
        </div>
    </div>
</body>
</html>
        """
    
    def _create_css_styles(self):
        """CSS replicando exatamente o layout do PDF de referência"""
        return """
@page {
    size: A4;
    margin: 20mm 15mm 25mm 15mm;
    
    @bottom-right {
        content: "Página " counter(page);
        font-family: Arial, Helvetica, sans-serif;
        font-size: 9pt;
        color: #666666;
    }
}

* {
    box-sizing: border-box;
}

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10pt;
    line-height: 1.1;
    color: #333333;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}

/* Cabeçalho - layout exato da imagem */
.header-section {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 1.2cm;
    padding-bottom: 0.3cm;
    border-bottom: 1px solid #e0e0e0;
}

.logo-container {
    width: 100px;
    height: 35px;
    flex-shrink: 0;
}

.elp-logo {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.main-title {
    font-size: 18pt;
    font-weight: bold;
    color: #333333;
    text-align: center;
    margin: 0;
    flex: 1;
    padding: 0 20px;
}

.date-info {
    font-size: 10pt;
    color: #666666;
    white-space: nowrap;
    align-self: flex-end;
}

/* Seções com fundo cinza - proporções exatas da imagem */
.report-section,
.dados-section,
.observacoes-section,
.assinaturas-section {
    background-color: #f8f8f8;
    border: 1px solid #d0d0d0;
    margin-bottom: 6px;
    padding: 0;
    break-inside: avoid;
}

.section-header {
    background-color: #e0e0e0;
    font-weight: bold;
    font-size: 10pt;
    color: #333333;
    padding: 6px 10px;
    border-bottom: 1px solid #d0d0d0;
    margin: 0;
}

/* Seção Relatório */
.report-content {
    padding: 10px;
}

.report-label {
    font-size: 10pt;
    color: #333333;
    margin-bottom: 3px;
}

.report-number {
    font-size: 12pt;
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
    padding: 6px 10px;
    border-right: 1px solid #d0d0d0;
    vertical-align: top;
}

.dados-cell:last-child {
    border-right: none;
}

.header-row .dados-cell {
    font-weight: bold;
    font-size: 9pt;
    background-color: #e0e0e0;
    color: #333333;
}

.value-row .dados-cell {
    font-size: 9pt;
    background-color: #f8f8f8;
    color: #333333;
    min-height: 32px;
}

/* Itens Observados - proporções da imagem */
.observacoes-content {
    padding: 10px;
}

.obs-text {
    font-size: 9pt;
    color: #333333;
    margin: 0 0 4px 0;
}

/* Quebra de página */
.page-break-before {
    page-break-before: always;
    break-before: page;
}

/* Layout geral de imagens */
img {
    display: block;
    max-width: 100%;
    height: auto;
}

figure {
    page-break-inside: avoid;
    break-inside: avoid;
    margin: 0;
    padding: 0;
}

/* PRIMEIRA PÁGINA: 2 FOTOS LOGO ABAIXO DE "ITENS OBSERVADOS" - SEM QUEBRA DE PÁGINA */
.first-page-photos {
    margin-top: 8mm;
    page-break-inside: avoid;
}

.first-photo-container {
    width: 100%;
    margin-bottom: 8mm;
    page-break-inside: avoid;
}

.first-photo-img {
    width: 100%;
    height: auto;
    max-height: 90mm;
    object-fit: contain;
    display: block;
    border: 1px solid #e0e0e0;
}

.photo-placeholder-first {
    width: 100%;
    height: 90mm;
    background-color: #f5f5f5;
    border: 2px dashed #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
    font-size: 10pt;
    font-style: italic;
}

.first-photo-caption {
    font-size: 9pt;
    color: #333;
    margin-top: 3mm;
    text-align: left;
    font-family: Arial, Helvetica, sans-serif;
}

/* DEMAIS PÁGINAS - GRID 2x2 (4 imagens por página) */
.grid-photos-page {
    page-break-after: always;
    padding: 5mm 0;
}

.photos-grid-2x2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 8mm;
    width: 100%;
    height: auto;
}

.grid-photo-item {
    page-break-inside: avoid;
    display: flex;
    flex-direction: column;
}

.grid-photo-img {
    width: 100%;
    height: auto;
    max-height: 85mm;
    object-fit: contain;
    display: block;
    border: 1px solid #e0e0e0;
}

.photo-placeholder-grid {
    width: 100%;
    height: 85mm;
    background-color: #f5f5f5;
    border: 2px dashed #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
    font-size: 9pt;
    font-style: italic;
}

.grid-photo-caption {
    font-size: 9pt;
    color: #333;
    margin-top: 3mm;
    text-align: left;
    font-family: Arial, Helvetica, sans-serif;
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
    padding: 6px 10px;
    border-right: 1px solid #d0d0d0;
    vertical-align: top;
}

.assin-cell:last-child {
    border-right: none;
}

.header-row .assin-cell {
    font-weight: bold;
    font-size: 9pt;
    background-color: #e0e0e0;
    color: #333333;
}

.value-row .assin-cell {
    font-size: 9pt;
    background-color: #f8f8f8;
    color: #333333;
    min-height: 32px;
}

/* Rodapé - proporções exatas da imagem */
.footer-section {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 0.8cm 1.5cm 0.5cm 1.5cm;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    background: white;
    border-top: 1px solid #e0e0e0;
}

.footer-left {
    display: flex;
    align-items: flex-start;
    gap: 8px;
}

.footer-logo {
    width: 50px;
    height: 25px;
    flex-shrink: 0;
    object-fit: contain;
}

.company-info {
    font-size: 8pt;
    color: #666666;
    line-height: 1.1;
}

.company-name {
    font-weight: bold;
    color: #333333;
    margin-bottom: 1px;
}

.company-info a {
    color: #4A90E2;
    text-decoration: none;
}

.footer-right {
    text-align: right;
}

.generated-info {
    font-size: 8pt;
    color: #666666;
}

.produttivo {
    color: #4A90E2;
    font-weight: bold;
}

/* PÁGINA DE ASSINATURAS - sempre no final após todas as imagens */
.assinaturas-page {
    page-break-before: always;
    padding-top: 20mm;
}

/* Quebras de página - evitar quebra dentro de seções */
.report-section,
.dados-section,
.observacoes-section,
.assinaturas-section {
    break-inside: avoid;
    page-break-inside: avoid;
}

/* Garantir que cada grade de fotos force quebra de página */
.grid-page {
    page-break-after: always;
}

/* Garantir que a primeira página de fotos quebre antes */
.pdf-images {
    page-break-before: always;
}
        """