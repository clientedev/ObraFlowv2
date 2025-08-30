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
        """Criar template HTML seguindo exatamente o modelo"""
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ data.titulo }}</title>
</head>
<body>
    <!-- Cabeçalho -->
    <div class="header">
        <div class="header-content">
            <h1 class="main-title">{{ data.titulo }}</h1>
            <div class="date-info">Em: {{ data.data_atual }}</div>
        </div>
    </div>
    
    <!-- Conteúdo Principal -->
    <div class="content">
        <!-- Seção Relatório -->
        <div class="section">
            <h2 class="report-header">Relatório</h2>
            <div class="report-number-section">
                <div class="report-number-label">Relatório Número</div>
                <div class="report-number">{{ data.numero_relatorio }}</div>
            </div>
        </div>
        
        <!-- Dados Gerais -->
        <div class="section">
            <h3 class="section-title">Dados gerais</h3>
            <div class="data-row">
                <div class="data-item">
                    <div class="data-label">Empresa</div>
                    <div class="data-value">{{ data.empresa }}</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Obra</div>
                    <div class="data-value">{{ data.obra }}</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Endereço</div>
                    <div class="data-value">{{ data.endereco }}</div>
                </div>
            </div>
        </div>
        
        <!-- Itens Observados -->
        <div class="section">
            <h3 class="section-title">Itens observados</h3>
            <div class="observations">
                {% if data.observacoes %}
                    <p>{{ data.observacoes }}</p>
                {% else %}
                    <p>..</p>
                    <p>Vide fotos.</p>
                {% endif %}
                <div class="dots-separator">.</div>
            </div>
            
            <!-- Fotos -->
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
                                <div class="photo-placeholder">Foto não disponível</div>
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
        
        <!-- Assinaturas -->
        <div class="section">
            <h3 class="section-title">Assinaturas</h3>
            <div class="signatures">
                <div class="signature-row">
                    <div class="signature-item">
                        <div class="signature-label">Preenchido por:</div>
                        <div class="signature-value">{{ data.preenchido_por }}</div>
                    </div>
                    <div class="signature-item">
                        <div class="signature-label">Liberado por:</div>
                        <div class="signature-value">{{ data.liberado_por }}</div>
                    </div>
                    <div class="signature-item">
                        <div class="signature-label">Responsável pelo acompanhamento</div>
                        <div class="signature-value">{{ data.responsavel }}</div>
                    </div>
                </div>
                <div class="signature-date">
                    <strong>Em:</strong> {{ data.data_relatorio }}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Rodapé -->
    <div class="footer">
        <div class="footer-left">
            <div class="company-name"><strong>ELP Consultoria</strong></div>
            <div>Rua Jaboticabal, 530 apto. 31 - São Paulo - SP - CEP: 03188-000</div>
            <div>leopoldo@elpconsultoria.eng.br</div>
            <div>Telefone: (11) 99138-4517</div>
        </div>
        <div class="footer-right">
            Relatório gerado no Produttivo
        </div>
    </div>
</body>
</html>
        """
    
    def _create_css_styles(self):
        """Criar estilos CSS seguindo exatamente o modelo visual"""
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
    font-size: 11px;
    line-height: 1.2;
    color: #000000;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}

/* Cabeçalho */
.header {
    text-align: center;
    margin-bottom: 60px;
}

.main-title {
    font-size: 12pt;
    font-weight: bold;
    color: #000000;
    margin: 0;
    padding: 0;
    text-align: center;
}

.date-info {
    font-size: 10pt;
    color: #000000;
    text-align: right;
    margin-top: 40px;
    margin-bottom: 20px;
}

/* Seções */
.section {
    margin-bottom: 25px;
}

.report-header {
    font-size: 16pt;
    font-weight: bold;
    color: #000000;
    margin: 0 0 8px 0;
}

.report-number-section {
    margin-bottom: 20px;
}

.report-number-label {
    font-size: 12pt;
    color: #000000;
    margin-bottom: 2px;
}

.report-number {
    font-size: 16pt;
    font-weight: bold;
    color: #000000;
}

.section-title {
    font-size: 12pt;
    font-weight: bold;
    color: #000000;
    margin: 0 0 8px 0;
}

/* Dados Gerais */
.data-row {
    display: flex;
    gap: 40px;
    margin-bottom: 15px;
}

.data-item {
    flex: 1;
}

.data-label {
    font-weight: bold;
    font-size: 11pt;
    color: #000000;
    margin-bottom: 3px;
}

.data-value {
    font-size: 11pt;
    color: #000000;
    margin-bottom: 3px;
}

/* Observações */
.observations p {
    font-size: 11pt;
    color: #000000;
    margin: 0 0 3px 0;
}

.dots-separator {
    font-size: 11pt;
    color: #000000;
    text-align: center;
    margin: 15px 0;
}

/* Fotos */
.photos-section {
    margin-top: 20px;
}

.photo-row {
    display: flex;
    gap: 20px;
    margin-bottom: 15px;
    justify-content: center;
}

.photo-container {
    text-align: center;
    flex: 1;
    max-width: 300px;
}

.photo {
    width: 100%;
    max-width: 280px;
    height: auto;
    border: none;
}

.photo-caption {
    font-size: 10pt;
    color: #555555;
    text-align: center;
    margin-top: 5px;
    line-height: 1.2;
}

.photo-placeholder {
    width: 100%;
    max-width: 280px;
    height: 200px;
    background-color: #f5f5f5;
    border: 1px dashed #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    font-size: 10pt;
}

/* Assinaturas */
.signatures {
    margin-top: 10px;
}

.signature-row {
    display: flex;
    gap: 30px;
    margin-bottom: 15px;
}

.signature-item {
    flex: 1;
}

.signature-label {
    font-weight: bold;
    font-size: 11pt;
    color: #000000;
    margin-bottom: 3px;
}

.signature-value {
    font-size: 11pt;
    color: #000000;
}

.signature-date {
    font-size: 11pt;
    color: #000000;
    margin-top: 10px;
}

/* Rodapé */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    font-size: 9pt;
    color: #000000;
    line-height: 1.1;
    padding: 0 2cm;
    margin-bottom: 1cm;
}

.footer-left {
    flex: 1;
}

.footer-right {
    text-align: right;
    font-size: 9pt;
}

.company-name {
    margin-bottom: 2px;
}

/* Quebras de página */
.section {
    break-inside: avoid;
}

.photo-row {
    break-inside: avoid;
}
        """