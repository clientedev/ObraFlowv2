import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import black, blue, orange, white, gray
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask import current_app, Flask
from PIL import Image as PILImage

class ReportPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for the PDF following exact template format"""
        # Main title style
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=30,
            textColor=black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Date in header style
        self.styles.add(ParagraphStyle(
            name='HeaderDate',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=black,
            alignment=TA_RIGHT,
            fontName='Helvetica'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=12,
            textColor=black,
            leftIndent=0,
            fontName='Helvetica-Bold'
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            leftIndent=0,
            fontName='Helvetica'
        ))
        
        # Photo caption style
        self.styles.add(ParagraphStyle(
            name='PhotoCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Helvetica'
        ))
        
        # Checklist styles
        self.styles.add(ParagraphStyle(
            name='ChecklistHeader',
            parent=self.styles['Heading2'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=15,
            textColor=black,
            fontName='Helvetica-Bold',
            leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='ChecklistItem',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leftIndent=20,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ChecklistObservation',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            leftIndent=40,
            textColor=gray,
            fontName='Helvetica-Oblique'
        ))
        
        # Footer company style
        self.styles.add(ParagraphStyle(
            name='FooterCompany',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Footer info style
        self.styles.add(ParagraphStyle(
            name='FooterInfo',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=black,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Footer right style
        self.styles.add(ParagraphStyle(
            name='FooterRight',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=black,
            alignment=TA_RIGHT,
            fontName='Helvetica'
        ))
    
    def generate_visit_report_pdf(self, relatorio, output_path=None):
        """Generate PDF report following exact template format"""
        if not output_path:
            output_path = f"relatorio_{relatorio.numero}.pdf"
        
        # Create PDF document with exact margins from template
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=80  # Space for footer
        )
        
        # Build PDF content
        story = []
        
        # Header section (title and date)
        self._add_template_header(story, relatorio)
        
        # Report section
        self._add_template_report_section(story, relatorio)
        
        # Company and project info
        self._add_template_company_info(story, relatorio)
        
        # Items observados section
        self._add_template_items_section(story, relatorio)
        
        # Photos grid (2x2 per page)
        if relatorio.fotos:
            self._add_template_photos_grid(story, relatorio.fotos)
        
        # Signatures section
        self._add_template_signatures(story, relatorio)
        
        # Build PDF with custom footer
        doc.build(story, onFirstPage=self._add_template_footer, onLaterPages=self._add_template_footer)
    
    def generate_report_pdf(self, relatorio, fotos=None):
        """Generate professional PDF report matching the template format"""
        buffer = io.BytesIO()
        
        # Create document with A4 page size
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Build story (content)
        story = []
        
        # Header with date
        header_table = Table([
            ['Relatório de Visita', f'Em: {datetime.now().strftime("%d/%m/%Y %H:%M")}']
        ], colWidths=[12*cm, 6*cm])
        
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('FONTSIZE', (1, 0), (1, 0), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Report section
        story.append(Paragraph("Relatório", self.styles['SectionHeader']))
        
        # Date info
        date_info = f"Data<br/>{relatorio.data_relatorio.strftime('%d/%m/%Y %H:%M:%S') if relatorio.data_relatorio else 'Não informada'}"
        story.append(Paragraph(date_info, self.styles['Info']))
        story.append(Spacer(1, 15))
        
        # General data section
        story.append(Paragraph("Dados gerais", self.styles['SectionHeader']))
        
        # Company and project info
        projeto_nome = relatorio.projeto.nome if relatorio.projeto else "Não informado"
        autor_nome = relatorio.autor.nome_completo if relatorio.autor else "Não informado"
        
        general_data = Table([
            ['Empresa', 'Empreendimento'],
            [autor_nome, projeto_nome]
        ], colWidths=[9*cm, 9*cm])
        
        general_data.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
        ]))
        
        story.append(general_data)
        story.append(Spacer(1, 20))
        
        # Content section
        if relatorio.conteudo:
            story.append(Paragraph("Observações", self.styles['SectionHeader']))
            story.append(Paragraph(relatorio.conteudo, self.styles['Info']))
            story.append(Spacer(1, 15))
        
        # Photos section
        if fotos:
            story.append(Paragraph("Itens observados", self.styles['SectionHeader']))
            story.append(Spacer(1, 10))
            
            # Process photos in pairs (2 per row)
            photo_pairs = [fotos[i:i+2] for i in range(0, len(fotos), 2)]
            
            for pair in photo_pairs:
                photo_row = []
                caption_row = []
                
                for foto in pair:
                    # Try to load image
                    try:
                        from flask import current_app
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads') if current_app else 'uploads'
                        image_path = os.path.join(upload_folder, foto.filename)
                        
                        if os.path.exists(image_path):
                            # Resize image to fit in PDF
                            img = Image(image_path, width=8*cm, height=6*cm)
                            photo_row.append(img)
                        else:
                            # Placeholder for missing image
                            photo_row.append(Paragraph("Imagem não encontrada", self.styles['PhotoCaption']))
                        
                        # Add caption
                        caption_row.append(Paragraph(foto.legenda or "Sem legenda", self.styles['PhotoCaption']))
                        
                    except Exception:
                        photo_row.append(Paragraph("Erro ao carregar imagem", self.styles['PhotoCaption']))
                        caption_row.append(Paragraph(foto.legenda or "Sem legenda", self.styles['PhotoCaption']))
                
                # Fill remaining cells if odd number of photos
                while len(photo_row) < 2:
                    photo_row.append('')
                    caption_row.append('')
                
                # Create photo table
                photo_table = Table([photo_row, caption_row], colWidths=[9*cm, 9*cm])
                photo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTSIZE', (0, 1), (-1, 1), 9),
                ]))
                
                story.append(photo_table)
                story.append(Spacer(1, 15))
        
        # Footer section
        story.append(Spacer(1, 30))
        story.append(Paragraph("Assinaturas", self.styles['SectionHeader']))
        
        # Signature table
        signature_table = Table([
            ['Preenchido por:', 'Liberado por:', 'Responsável pelo acompanhamento'],
            [autor_nome, 'Engenheiro Responsável', 'Responsável Técnico']
        ], colWidths=[6*cm, 6*cm, 6*cm])
        
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
        ]))
        
        story.append(signature_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _add_template_header(self, story, relatorio):
        """Add header following exact template format with ELP branding"""
        # Company header with logo
        try:
            from flask import current_app
            logo_path = os.path.join('static', 'logo_elp_new.jpg')
            if os.path.exists(logo_path):
                logo_img = Image(logo_path, width=3*cm, height=1.5*cm)
                
                # Create header table with logo and company info
                header_data = [
                    [logo_img, 'ELP CONSULTORIA E ENGENHARIA\nServiços de Engenharia\nEspecializada em Fachadas de Obras e Empreendimentos Verticais', '']
                ]
                
                header_table = Table(header_data, colWidths=[4*cm, 12*cm, 3*cm])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (1, 0), (1, 0), 10),
                    ('TEXTCOLOR', (1, 0), (1, 0), '#343a40'),
                ]))
                
                story.append(header_table)
                story.append(Spacer(1, 20))
            
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        # Title
        story.append(Paragraph("Relatório de Visita", self.styles['MainTitle']))
        story.append(Spacer(1, 20))
        
        # Date in right corner format
        data_formatada = relatorio.data_relatorio.strftime('%d/%m/%Y %H:%M') if relatorio.data_relatorio else datetime.now().strftime('%d/%m/%Y %H:%M')
        date_table = Table([['', f'Em: {data_formatada}']], colWidths=[15*cm, 4*cm])
        date_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, 0), 10),
        ]))
        story.append(date_table)
        story.append(Spacer(1, 20))
    
    def _add_template_report_section(self, story, relatorio):
        """Add report info section following template"""
        story.append(Paragraph("Relatório", self.styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        data_formatada = relatorio.data_relatorio.strftime('%d/%m/%Y %H:%M:%S') if relatorio.data_relatorio else datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        report_table = Table([
            ['Data', ''],
            [data_formatada, '']
        ], colWidths=[8*cm, 11*cm])
        
        report_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(report_table)
        story.append(Spacer(1, 20))
    
    def _add_template_company_info(self, story, relatorio):
        """Add company and project info following template"""
        story.append(Paragraph("Dados gerais", self.styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        # Get project info
        projeto = relatorio.projeto if relatorio.projeto else None
        empresa = projeto.responsavel.nome_completo if projeto and projeto.responsavel else 'Não informado'
        empreendimento = projeto.nome if projeto else 'Não informado'
        
        company_table = Table([
            ['Empresa', 'Empreendimento'],
            [empresa, empreendimento]
        ], colWidths=[9.5*cm, 9.5*cm])
        
        company_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(company_table)
        story.append(Spacer(1, 20))
    
    def _add_template_items_section(self, story, relatorio):
        """Add items observados section following template with improved checklist formatting"""
        story.append(Paragraph("Itens observados", self.styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        if relatorio.conteudo:
            # Process content to handle line breaks properly and format different sections
            content_lines = relatorio.conteudo.split('\n')
            in_checklist = False
            in_location = False
            
            for line in content_lines:
                if line.strip():
                    # Check if this is checklist section
                    if 'CHECKLIST DA OBRA:' in line:
                        in_checklist = True
                        in_location = False
                        story.append(Spacer(1, 10))
                        
                        # Create beautiful checklist header with border
                        checklist_table = Table([['📋 CHECKLIST DA OBRA']], colWidths=[18*cm])
                        checklist_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), '#f0f8ff'),
                            ('BORDER', (0, 0), (-1, -1), 1, '#4169e1'),
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 12),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ]))
                        story.append(checklist_table)
                        story.append(Spacer(1, 8))
                        
                    # Check if this is location information
                    elif 'LOCALIZAÇÃO DO RELATÓRIO:' in line:
                        in_checklist = False
                        in_location = True
                        story.append(Spacer(1, 10))
                        
                        # Create beautiful location header with border
                        location_table = Table([['📍 LOCALIZAÇÃO DO RELATÓRIO']], colWidths=[18*cm])
                        location_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), '#f0fff0'),
                            ('BORDER', (0, 0), (-1, -1), 1, '#228b22'),
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 12),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('TOPPADDING', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ]))
                        story.append(location_table)
                        story.append(Spacer(1, 8))
                        
                    # Format checklist items with improved design
                    elif in_checklist and (line.startswith('✓') or line.startswith('○')):
                        status_symbol = "✓" if line.startswith('✓') else "○"
                        item_text = line[1:].strip()  # Remove status symbol
                        
                        # Create a table for each checklist item with status and description
                        if status_symbol == "✓":
                            # Completed item - green background with ELP colors
                            item_table = Table([['✅', item_text]], colWidths=[1*cm, 17*cm])
                            item_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (0, 0), '#20c1e8'),  # ELP cyan for checkmark
                                ('BACKGROUND', (1, 0), (1, 0), '#f0fff0'),  # Very light green for text
                                ('BORDER', (0, 0), (-1, -1), 0.5, '#343a40'),  # ELP dark border
                                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                                ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
                                ('FONTSIZE', (0, 0), (-1, -1), 10),
                                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('TOPPADDING', (0, 0), (-1, -1), 8),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                                ('TEXTCOLOR', (1, 0), (1, 0), '#343a40'),  # ELP dark text
                            ]))
                        else:
                            # Incomplete item - orange background with ELP colors
                            item_table = Table([['❌', item_text]], colWidths=[1*cm, 17*cm])
                            item_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (0, 0), '#ff6b6b'),  # Light red for incomplete
                                ('BACKGROUND', (1, 0), (1, 0), '#fff0f0'),  # Very light red for text
                                ('BORDER', (0, 0), (-1, -1), 0.5, '#343a40'),  # ELP dark border
                                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                                ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
                                ('FONTSIZE', (0, 0), (-1, -1), 10),
                                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('TOPPADDING', (0, 0), (-1, -1), 8),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                                ('TEXTCOLOR', (1, 0), (1, 0), '#343a40'),  # ELP dark text
                            ]))
                        
                        story.append(item_table)
                        story.append(Spacer(1, 4))
                        
                    # Format checklist observations with indentation
                    elif in_checklist and line.strip().startswith('Observações:'):
                        obs_text = line.replace('Observações:', '').strip()
                        if obs_text:
                            obs_table = Table([['💬', f"Observações: {obs_text}"]], colWidths=[1*cm, 17*cm])
                            obs_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, -1), '#f8f8f8'),
                                ('BORDER', (0, 0), (-1, -1), 0.5, gray),
                                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Oblique'),
                                ('FONTSIZE', (0, 0), (-1, -1), 9),
                                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('TOPPADDING', (0, 0), (-1, -1), 4),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ]))
                            story.append(obs_table)
                            story.append(Spacer(1, 8))
                            
                    # Format GPS coordinates
                    elif line.startswith('Latitude:') or line.startswith('Longitude:') or '(Coordenadas:' in line:
                        story.append(Paragraph(f"<i>{line.strip()}</i>", self.styles['Info']))
                    # Format addresses in bold
                    elif any(keyword in line for keyword in ['Rua', 'Avenida', 'Estrada', 'Brasil', 'São Paulo', 'Rodovia']):
                        story.append(Paragraph(f"<b>{line.strip()}</b>", self.styles['Info']))
                    # Regular content
                    else:
                        story.append(Paragraph(line.strip(), self.styles['Info']))
                else:
                    story.append(Spacer(1, 6))
            
            story.append(Spacer(1, 20))
        else:
            # No content - show empty state
            empty_table = Table([['📝 Nenhum item observado foi registrado neste relatório.']], colWidths=[18*cm])
            empty_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), '#f5f5f5'),
                ('BORDER', (0, 0), (-1, -1), 1, gray),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Oblique'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            story.append(empty_table)
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
    
    def _add_template_photos_grid(self, story, fotos):
        """Add photos in 2x2 grid format following template with ELP branding"""
        fotos_ordenadas = sorted(fotos, key=lambda x: x.ordem if hasattr(x, 'ordem') else 0)
        
        # Process photos in groups of 4 (2x2 grid)
        for i in range(0, len(fotos_ordenadas), 4):
            batch = fotos_ordenadas[i:i+4]
            
            # Create 2x2 grid
            row1_data = []
            row2_data = []
            
            # First row (first 2 photos)
            for j in range(2):
                if j < len(batch):
                    foto = batch[j]
                    photo_cell = self._create_photo_cell(foto)
                    row1_data.append(photo_cell)
                else:
                    row1_data.append('.')  # Empty cell placeholder
            
            # Second row (next 2 photos)
            for j in range(2, 4):
                if j < len(batch):
                    foto = batch[j]
                    photo_cell = self._create_photo_cell(foto)
                    row2_data.append(photo_cell)
                else:
                    row2_data.append('.')  # Empty cell placeholder
            
            # Create table with 2x2 grid
            photo_table = Table([row1_data, row2_data], colWidths=[9.5*cm, 9.5*cm], rowHeights=[7*cm, 7*cm])
            photo_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(photo_table)
            
            # Add page break if not last batch
            if i + 4 < len(fotos_ordenadas):
                story.append(PageBreak())
    
    def _create_photo_cell(self, foto, single=False):
        """Create a photo cell with image and caption with ELP branding"""
        try:
            # Use annotated photo if available, otherwise use original
            photo_path = foto.filename_anotada if hasattr(foto, 'filename_anotada') and foto.filename_anotada else foto.filename
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_path)
            
            if os.path.exists(full_path):
                # Create image with appropriate size
                max_width = 12*cm if single else 8*cm
                max_height = 8*cm if single else 5*cm
                
                img = Image(full_path)
                img_width, img_height = self._calculate_image_size(full_path, max_width=max_width, max_height=max_height)
                img.drawWidth = img_width
                img.drawHeight = img_height
                
                # Create enhanced caption with ELP styling
                caption_text = foto.legenda if hasattr(foto, 'legenda') and foto.legenda else 'Foto da obra'
                
                # Create a styled caption table
                caption_table = Table([[caption_text]], colWidths=[max_width])
                caption_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), '#f8f9fa'),
                    ('BORDER', (0, 0), (-1, -1), 0.5, '#343a40'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TEXTCOLOR', (0, 0), (-1, -1), '#343a40'),
                ]))
                
                # Return as list for table cell
                return [img, Spacer(1, 3), caption_table]
            else:
                # Create error cell with ELP styling
                error_table = Table([['📷 Foto não encontrada']], colWidths=[8*cm])
                error_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), '#fff3cd'),
                    ('BORDER', (0, 0), (-1, -1), 1, '#856404'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 20),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
                ]))
                return error_table
        except Exception as e:
            current_app.logger.error(f"Error creating photo cell for {foto.filename}: {e}")
            # Create error cell with ELP styling
            error_table = Table([['❌ Erro ao carregar foto']], colWidths=[8*cm])
            error_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), '#f8d7da'),
                ('BORDER', (0, 0), (-1, -1), 1, '#721c24'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            return error_table
    
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
    
    def _add_template_signatures(self, story, relatorio):
        """Add signatures section following template with ELP branding"""
        story.append(Spacer(1, 30))
        
        story.append(Paragraph("Assinaturas", self.styles['SectionHeader']))
        story.append(Spacer(1, 20))
        
        # Get signature info
        preenchido_por = relatorio.autor.nome_completo if relatorio.autor else 'Não informado'
        liberado_por = 'Engenheiro Civil\nELP Consultoria e Engenharia'
        responsavel = 'ELP Consultoria e Engenharia\nEspecialista em Fachadas'
        
        signatures_table = Table([
            ['Preenchido por:', 'Liberado por:', 'Responsável pelo acompanhamento'],
            [preenchido_por, liberado_por, responsavel]
        ], colWidths=[6.3*cm, 6.3*cm, 6.3*cm])
        
        signatures_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('TEXTCOLOR', (0, 1), (-1, 1), '#343a40'),
        ]))
        
        story.append(signatures_table)
    
    def _add_template_footer(self, canvas, doc):
        """Add footer following exact template format with ELP branding"""
        # Company info on left
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawString(40, 60, 'ELP CONSULTORIA E ENGENHARIA')
        
        canvas.setFont('Helvetica', 8)
        canvas.drawString(40, 45, 'Serviços de Engenharia - Especializada em Fachadas')
        canvas.drawString(40, 32, 'Consultoria voltada para Engenharia Civil')
        canvas.drawString(40, 19, 'Sistema de Relatórios de Obras e Empreendimentos Verticais')
        
        # Generated info on right
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(555, 32, 'ELP Consultoria e Engenharia')
        canvas.drawRightString(555, 19, f'Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}')

def generate_visit_report_pdf(relatorio):
    """Generate PDF report for a visit"""
    generator = ReportPDFGenerator()
    
    # Create filename
    safe_filename = f"relatorio_{relatorio.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
    
    # Generate PDF
    pdf_path = generator.generate_visit_report_pdf(relatorio, output_path)
    
    return pdf_path, safe_filename

    def generate_reimbursement_pdf(self, reembolso, output_path):
        """Generate PDF for approved reimbursement"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            
            # Header
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=20,
                alignment=1,  # Center
                textColor=colors.HexColor('#1f5582')
            )
            
            story.append(Paragraph("COMPROVANTE DE REEMBOLSO APROVADO", title_style))
            story.append(Spacer(1, 20))
            
            # Reembolso info
            info_data = [
                ['ID do Reembolso:', f'#{reembolso.id}'],
                ['Solicitante:', reembolso.usuario.nome_completo if reembolso.usuario else '-'],
                ['Projeto:', reembolso.projeto.nome if reembolso.projeto else '-'],
                ['Período:', reembolso.periodo or '-'],
                ['Data da Solicitação:', reembolso.created_at.strftime('%d/%m/%Y %H:%M') if reembolso.created_at else '-'],
                ['Data da Aprovação:', reembolso.data_aprovacao.strftime('%d/%m/%Y %H:%M') if reembolso.data_aprovacao else '-'],
                ['Status:', reembolso.status]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Motivo
            if reembolso.motivo:
                story.append(Paragraph("<b>Motivo da Solicitação:</b>", styles['Normal']))
                story.append(Paragraph(reembolso.motivo, styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Detalhamento dos gastos
            story.append(Paragraph("<b>DETALHAMENTO DOS GASTOS</b>", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Calculate combustible total
            total_combustivel = (reembolso.quilometragem or 0) * (reembolso.valor_km or 0)
            
            gastos_data = [
                ['Descrição', 'Quantidade', 'Valor Unitário', 'Total'],
                ['Combustível (km percorrida)', f'{reembolso.quilometragem or 0:.1f} km', 
                 f'R$ {reembolso.valor_km or 0:.2f}', f'R$ {total_combustivel:.2f}'],
                ['Alimentação', '-', '-', f'R$ {reembolso.alimentacao or 0:.2f}'],
                ['Hospedagem', '-', '-', f'R$ {reembolso.hospedagem or 0:.2f}'],
                ['Outros gastos', '-', '-', f'R$ {reembolso.outros_gastos or 0:.2f}'],
                ['', '', 'TOTAL GERAL:', f'R$ {reembolso.total:.2f}']
            ]
            
            gastos_table = Table(gastos_data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.3*inch])
            gastos_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (2, -1), (-1, -1), colors.lightgrey),
            ]))
            
            story.append(gastos_table)
            story.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(story)
            return output_path
            
        except Exception as e:
            print(f"Error generating reimbursement PDF: {e}")
            raise