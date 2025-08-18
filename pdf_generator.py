import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import black, blue, orange
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask import current_app, Flask
from PIL import Image as PILImage

class ReportPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=blue,
            alignment=TA_CENTER
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='Header',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            textColor=orange,
            leftIndent=0
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leftIndent=20
        ))
        
        # Photo caption style
        self.styles.add(ParagraphStyle(
            name='PhotoCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Helvetica-Bold'
        ))
    
    def generate_visit_report_pdf(self, relatorio, output_path=None):
        """Generate a comprehensive PDF report for a visit"""
        if not output_path:
            output_path = f"relatorio_{relatorio.numero}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build PDF content
        story = []
        
        # Header
        self._add_header(story, relatorio)
        
        # Project information
        self._add_project_info(story, relatorio)
        
        # Visit information
        if relatorio.visita:
            self._add_visit_info(story, relatorio.visita)
        
        # Report content
        self._add_report_content(story, relatorio)
        
        # Photos with captions and annotations
        if relatorio.fotos:
            self._add_photos_section(story, relatorio.fotos)
        
        # Footer information
        self._add_footer_info(story, relatorio)
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        return output_path
    
    def _add_header(self, story, relatorio):
        """Add report header"""
        story.append(Paragraph("RELATÓRIO DE ACOMPANHAMENTO DE OBRA", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Report number and date
        info_data = [
            ['Número do Relatório:', relatorio.numero],
            ['Título:', relatorio.titulo],
            ['Data do Relatório:', relatorio.data_relatorio.strftime('%d/%m/%Y')],
            ['Status:', relatorio.status],
            ['Autor:', relatorio.autor.nome_completo if relatorio.autor else 'N/A']
        ]
        
        if relatorio.aprovador:
            info_data.append(['Aprovador:', relatorio.aprovador.nome_completo])
            if relatorio.data_aprovacao:
                info_data.append(['Data de Aprovação:', relatorio.data_aprovacao.strftime('%d/%m/%Y às %H:%M')])
        
        info_table = Table(info_data, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
    
    def _add_project_info(self, story, relatorio):
        """Add project information section"""
        story.append(Paragraph("INFORMAÇÕES DO PROJETO", self.styles['Header']))
        
        projeto = relatorio.projeto
        project_data = [
            ['Número do Projeto:', projeto.numero],
            ['Nome:', projeto.nome],
            ['Tipo de Obra:', projeto.tipo_obra.nome if projeto.tipo_obra else 'N/A'],
            ['Endereço:', projeto.endereco or 'N/A'],
            ['Responsável:', projeto.responsavel.nome_completo if projeto.responsavel else 'N/A'],
            ['Status:', projeto.status],
        ]
        
        if projeto.data_inicio:
            project_data.append(['Data de Início:', projeto.data_inicio.strftime('%d/%m/%Y')])
        if projeto.data_previsao_fim:
            project_data.append(['Previsão de Término:', projeto.data_previsao_fim.strftime('%d/%m/%Y')])
        
        project_table = Table(project_data, colWidths=[4*cm, 12*cm])
        project_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 20))
    
    def _add_visit_info(self, story, visita):
        """Add visit information section"""
        story.append(Paragraph("INFORMAÇÕES DA VISITA", self.styles['Header']))
        
        visit_data = [
            ['Data Agendada:', visita.data_agendada.strftime('%d/%m/%Y às %H:%M')],
            ['Status:', visita.status],
        ]
        
        if visita.data_realizada:
            visit_data.append(['Data Realizada:', visita.data_realizada.strftime('%d/%m/%Y às %H:%M')])
        
        if visita.objetivo:
            visit_data.append(['Objetivo:', visita.objetivo])
        
        if visita.atividades_realizadas:
            visit_data.append(['Atividades Realizadas:', visita.atividades_realizadas])
        
        if visita.observacoes:
            visit_data.append(['Observações:', visita.observacoes])
        
        if visita.endereco_gps:
            visit_data.append(['Localização GPS:', visita.endereco_gps])
        
        visit_table = Table(visit_data, colWidths=[4*cm, 12*cm])
        visit_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(visit_table)
        story.append(Spacer(1, 20))
    
    def _add_report_content(self, story, relatorio):
        """Add report content section"""
        if relatorio.conteudo:
            story.append(Paragraph("CONTEÚDO DO RELATÓRIO", self.styles['Header']))
            
            # Process content to handle line breaks
            content_lines = relatorio.conteudo.split('\n')
            for line in content_lines:
                if line.strip():
                    story.append(Paragraph(line, self.styles['Normal']))
                else:
                    story.append(Spacer(1, 6))
            
            story.append(Spacer(1, 20))
    
    def _add_photos_section(self, story, fotos):
        """Add photos section with captions and annotations"""
        story.append(PageBreak())
        story.append(Paragraph("REGISTRO FOTOGRÁFICO", self.styles['Header']))
        
        for foto in sorted(fotos, key=lambda x: x.ordem):
            try:
                # Use annotated photo if available, otherwise use original
                photo_path = foto.filename_anotada if foto.filename_anotada else foto.filename
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_path)
                
                if os.path.exists(full_path):
                    # Add photo title if available
                    if foto.titulo:
                        story.append(Paragraph(foto.titulo, self.styles['Header']))
                        story.append(Spacer(1, 10))
                    
                    # Add photo
                    img = Image(full_path)
                    # Calculate size to fit page width
                    img_width, img_height = self._calculate_image_size(full_path, max_width=15*cm)
                    img.drawWidth = img_width
                    img.drawHeight = img_height
                    
                    story.append(img)
                    story.append(Spacer(1, 10))
                    
                    # Add caption/legend
                    if foto.legenda:
                        story.append(Paragraph(f"<b>Legenda:</b> {foto.legenda}", self.styles['PhotoCaption']))
                    
                    # Add description
                    if foto.descricao:
                        story.append(Paragraph(f"<b>Descrição:</b> {foto.descricao}", self.styles['Normal']))
                    
                    # Add service type
                    if foto.tipo_servico:
                        story.append(Paragraph(f"<b>Tipo de Serviço:</b> {foto.tipo_servico}", self.styles['Normal']))
                    
                    story.append(Spacer(1, 20))
                    
            except Exception as e:
                current_app.logger.error(f"Error adding photo {foto.filename}: {e}")
                story.append(Paragraph(f"[Erro ao carregar foto: {foto.filename}]", self.styles['Normal']))
                story.append(Spacer(1, 10))
    
    def _calculate_image_size(self, image_path, max_width=15*cm, max_height=20*cm):
        """Calculate image size maintaining aspect ratio"""
        try:
            with PILImage.open(image_path) as img:
                width, height = img.size
                
            # Calculate scale to fit within max dimensions
            scale_width = max_width / width
            scale_height = max_height / height
            scale = min(scale_width, scale_height)
            
            return width * scale, height * scale
        except:
            return max_width, max_width * 0.75  # Default aspect ratio
    
    def _add_footer_info(self, story, relatorio):
        """Add footer information"""
        story.append(HRFlowable(width="100%"))
        story.append(Spacer(1, 10))
        
        footer_text = f"""
        Este relatório foi gerado automaticamente pelo Sistema de Acompanhamento de Visitas em Obras em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.
        """
        
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        if relatorio.comentario_aprovacao:
            story.append(Spacer(1, 10))
            story.append(Paragraph("COMENTÁRIOS DE APROVAÇÃO", self.styles['Header']))
            story.append(Paragraph(relatorio.comentario_aprovacao, self.styles['Normal']))
    
    def _add_page_number(self, canvas, doc):
        """Add page number to each page"""
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.drawRightString(200*mm, 20*mm, text)

def generate_visit_report_pdf(relatorio):
    """Generate PDF report for a visit"""
    generator = ReportPDFGenerator()
    
    # Create filename
    safe_filename = f"relatorio_{relatorio.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
    
    # Generate PDF
    pdf_path = generator.generate_visit_report_pdf(relatorio, output_path)
    
    return pdf_path, safe_filename