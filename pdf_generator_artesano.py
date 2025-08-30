import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PIL import Image as PILImage
from flask import current_app


class ArtesanoPDFGenerator:
    """Gerador de PDF seguindo exatamente o modelo Artesano fornecido"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        # Cores da ELP
        self.elp_cyan = HexColor('#20c997')
        self.elp_dark = HexColor('#2c3e50')
        
    def setup_custom_styles(self):
        """Configurar estilos seguindo exatamente o modelo Artesano"""
        
        # Título principal - centralizado, tamanho médio
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=14,
            spaceAfter=0,
            spaceBefore=0,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=16
        ))
        
        # Data no cabeçalho - pequena, direita
        self.styles.add(ParagraphStyle(
            name='HeaderDate',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_RIGHT,
            fontName='Helvetica',
            spaceAfter=0,
            leading=12
        ))
        
        # Seção "Relatório" - normal, esquerda
        self.styles.add(ParagraphStyle(
            name='RelatórioHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            spaceBefore=0
        ))
        
        # Número do relatório - grande, negrito
        self.styles.add(ParagraphStyle(
            name='ReportNumber',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=0,
            spaceBefore=0
        ))
        
        # Cabeçalho de seção - médio, negrito
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=0,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=3,
            leading=12
        ))
        
        # Cabeçalho de tabela
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=2
        ))
        
        # Dados de tabela
        self.styles.add(ParagraphStyle(
            name='TableData',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=2
        ))
        
        # Legenda de foto - pequena, centralizada
        self.styles.add(ParagraphStyle(
            name='PhotoCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=5,
            leading=10
        ))
        
        # Rodapé - pequeno, esquerda
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=10,
            spaceAfter=0
        ))
        
        # Rodapé direita
        self.styles.add(ParagraphStyle(
            name='FooterRight',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_RIGHT,
            fontName='Helvetica',
            leading=10
        ))

    def generate_report_pdf(self, relatorio, fotos, output_path=None):
        """Gerar PDF seguindo exatamente o modelo Artesano"""
        buffer = None
        try:
            if output_path:
                # Para arquivos, usar caminho direto
                doc = SimpleDocTemplate(
                    output_path, 
                    pagesize=A4,
                    rightMargin=20*mm,
                    leftMargin=20*mm,
                    topMargin=15*mm,
                    bottomMargin=15*mm
                )
            else:
                # Para bytes, usar buffer
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(
                    buffer, 
                    pagesize=A4,
                    rightMargin=20*mm,
                    leftMargin=20*mm,
                    topMargin=15*mm,
                    bottomMargin=15*mm
                )
            
            # Elementos do documento
            story = []
            
            # Cabeçalho com logos e título
            story.extend(self._create_header(relatorio))
            
            # Seção Relatório
            story.append(Paragraph("Relatório", self.styles['RelatórioHeader']))
            story.append(Spacer(1, 3))
            
            # Título "Relatório Número" 
            story.append(Paragraph("Relatório Número", self.styles['NormalText']))
            # Número do relatório grande
            story.append(Paragraph(f"{relatorio.numero}", self.styles['ReportNumber']))
            story.append(Spacer(1, 15*mm))
            
            # Dados gerais
            story.extend(self._create_dados_gerais(relatorio))
            story.append(Spacer(1, 15*mm))
            
            # Itens observados
            story.extend(self._create_itens_observados(relatorio, fotos))
            story.append(Spacer(1, 20*mm))
            
            # Assinaturas
            story.extend(self._create_assinaturas(relatorio))
            story.append(Spacer(1, 25*mm))
            
            # Rodapé
            story.append(self._create_footer())
            
            # Gerar PDF
            doc.build(story)
            
            if output_path:
                return output_path
            else:
                pdf_data = buffer.getvalue()
                buffer.close()
                return pdf_data
                
        except Exception as e:
            if buffer:
                buffer.close()
            raise Exception(f"Erro ao gerar PDF: {str(e)}")
    
    def _create_header(self, relatorio):
        """Criar cabeçalho exatamente como no modelo"""
        elements = []
        
        # Espaço inicial
        elements.append(Spacer(1, 10*mm))
        
        # Título centralizado
        title = Paragraph("Relatório de Visita", self.styles['MainTitle'])
        elements.append(title)
        
        # Espaço grande após título
        elements.append(Spacer(1, 50*mm))
        
        # Data no canto direito
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        date_p = Paragraph(f"Em: {data_atual}", self.styles['HeaderDate'])
        
        # Tabela para posicionar a data no canto direito
        date_table = Table([[date_p]], colWidths=[A4[0]-40*mm])
        date_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(date_table)
        
        # Espaço após data
        elements.append(Spacer(1, 20*mm))
        
        return elements
    
    def _create_dados_gerais(self, relatorio):
        """Criar seção de dados gerais exatamente como no modelo"""
        elements = []
        
        # Título da seção
        elements.append(Paragraph("Dados gerais", self.styles['SectionHeader']))
        elements.append(Spacer(1, 8))
        
        # Dados do projeto
        projeto = relatorio.projeto
        empresa = projeto.responsavel.nome_completo if projeto.responsavel else "ELP Consultoria"
        obra = projeto.nome
        endereco = projeto.endereco or "Não informado"
        
        # Criar tabela de dados gerais sem bordas, seguindo modelo
        data = [
            [
                Paragraph("Empresa", self.styles['TableHeader']),
                Paragraph("Obra", self.styles['TableHeader']),
                Paragraph("Endereço", self.styles['TableHeader'])
            ],
            [
                Paragraph(empresa, self.styles['TableData']),
                Paragraph(obra, self.styles['TableData']),
                Paragraph(endereco, self.styles['TableData'])
            ]
        ]
        
        # Larguras das colunas seguindo o modelo
        table = Table(data, colWidths=[55*mm, 55*mm, 65*mm])
        table.setStyle(TableStyle([
            # Sem bordas
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            
            # Cabeçalho em negrito
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
            
            # Dados normais
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 0),
            
            # Alinhamento à esquerda
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_itens_observados(self, relatorio, fotos):
        """Criar seção de itens observados exatamente como no modelo"""
        elements = []
        
        # Título da seção
        elements.append(Paragraph("Itens observados", self.styles['SectionHeader']))
        elements.append(Spacer(1, 8))
        
        # Texto de observações - seguir modelo exato
        if hasattr(relatorio, 'conteudo') and relatorio.conteudo:
            elements.append(Paragraph(relatorio.conteudo, self.styles['NormalText']))
        else:
            # Texto exato do modelo
            elements.append(Paragraph("..", self.styles['NormalText']))
            elements.append(Paragraph("Vide fotos.", self.styles['NormalText']))
        
        # Pontinhos para separação como no modelo
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(".", self.styles['NormalText']))
        elements.append(Spacer(1, 15))
        
        # Adicionar fotos em pares (2 por linha como no modelo)
        if fotos:
            elements.extend(self._create_photos_section(fotos))
        
        return elements
    
    def _create_photos_section(self, fotos):
        """Criar seção de fotos em pares seguindo modelo"""
        elements = []
        
        # Processar fotos em pares
        for i in range(0, len(fotos), 2):
            foto1 = fotos[i]
            foto2 = fotos[i + 1] if i + 1 < len(fotos) else None
            
            # Criar linha com fotos
            photo_row = self._create_photo_row(foto1, foto2)
            elements.extend(photo_row)
            
            # Espaço entre linhas de fotos
            if i + 2 < len(fotos):
                elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_photo_row(self, foto1, foto2=None):
        """Criar uma linha com fotos seguindo o modelo exato"""
        elements = []
        
        try:
            # Preparar legendas primeiro
            captions = []
            photos = []
            
            # Primeira foto
            if foto1:
                img1_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), foto1.filename)
                if os.path.exists(img1_path):
                    # Tamanho das fotos conforme modelo
                    img1 = Image(img1_path, width=75*mm, height=55*mm)
                    photos.append(img1)
                else:
                    photos.append(Paragraph("Foto não encontrada", self.styles['NormalText']))
                
                # Legenda da foto
                caption1 = foto1.descricao or f"Foto {foto1.ordem}"
                captions.append(caption1)
            
            # Segunda foto (se existir)
            if foto2:
                img2_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), foto2.filename)
                if os.path.exists(img2_path):
                    img2 = Image(img2_path, width=75*mm, height=55*mm)
                    photos.append(img2)
                else:
                    photos.append(Paragraph("Foto não encontrada", self.styles['NormalText']))
                
                caption2 = foto2.descricao or f"Foto {foto2.ordem}"
                captions.append(caption2)
            
            # Se só tiver uma foto, centralizar
            if len(photos) == 1:
                # Tabela com uma foto centralizada
                photo_table = Table([photos], colWidths=[75*mm])
                photo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                
                caption_table = Table([captions], colWidths=[75*mm])
                caption_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                
            else:
                # Tabela com duas fotos lado a lado
                photo_table = Table([photos], colWidths=[85*mm, 85*mm])
                photo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                
                caption_table = Table([captions], colWidths=[85*mm, 85*mm])
                caption_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
            
            elements.append(photo_table)
            elements.append(caption_table)
            
        except Exception as e:
            elements.append(Paragraph(f"Erro ao carregar fotos: {str(e)}", self.styles['NormalText']))
        
        return elements
    
    def _create_assinaturas(self, relatorio):
        """Criar seção de assinaturas exatamente como no modelo"""
        elements = []
        
        # Título da seção
        elements.append(Paragraph("Assinaturas", self.styles['SectionHeader']))
        elements.append(Spacer(1, 8))
        
        # Dados das assinaturas
        preenchido_por = relatorio.autor.nome_completo if relatorio.autor else "Não informado"
        liberado_por = "Eng. José Leopoldo Pugliese"  # Valor fixo conforme modelo
        responsavel = relatorio.projeto.responsavel.nome_completo if relatorio.projeto and relatorio.projeto.responsavel else "Não informado"
        
        # Tabela de assinaturas sem bordas
        sig_data = [
            [
                Paragraph("Preenchido por:", self.styles['TableHeader']),
                Paragraph("Liberado por:", self.styles['TableHeader']),
                Paragraph("Responsável pelo acompanhamento", self.styles['TableHeader'])
            ],
            [
                Paragraph(preenchido_por, self.styles['TableData']),
                Paragraph(liberado_por, self.styles['TableData']),
                Paragraph(responsavel, self.styles['TableData'])
            ]
        ]
        
        sig_table = Table(sig_data, colWidths=[55*mm, 55*mm, 65*mm])
        sig_table.setStyle(TableStyle([
            # Sem bordas
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            
            # Cabeçalho
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
            ('TOPPADDING', (0, 0), (-1, 0), 0),
            
            # Dados das assinaturas
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 0),
            
            # Alinhamento
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(sig_table)
        return elements
    
    def _create_footer(self):
        """Criar rodapé exatamente como no modelo"""
        # Texto do lado esquerdo (dados da empresa)
        footer_left = """<b>ELP Consultoria</b><br/>
Rua Jaboticabal, 530 apto. 31 - São Paulo - SP - CEP: 03188-000<br/>
leopoldo@elpconsultoria.eng.br<br/>
Telefone: (11) 99138-4517"""
        
        # Texto do lado direito
        footer_right = "Relatório gerado no Produttivo"
        
        footer_data = [
            [
                Paragraph(footer_left, self.styles['Footer']),
                Paragraph(footer_right, self.styles['FooterRight'])
            ]
        ]
        
        footer_table = Table(footer_data, colWidths=[120*mm, 60*mm])
        footer_table.setStyle(TableStyle([
            # Sem bordas
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            
            # Alinhamento
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        return footer_table