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
        """Configurar estilos customizados seguindo o modelo exato"""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=40,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Data no cabeçalho
        self.styles.add(ParagraphStyle(
            name='HeaderDate',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_RIGHT,
            fontName='Helvetica',
            spaceAfter=30
        ))
        
        # Número do relatório
        self.styles.add(ParagraphStyle(
            name='ReportNumber',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=20,
            spaceBefore=20
        ))
        
        # Cabeçalho de seção
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=15,
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
            spaceAfter=6
        ))
        
        # Legenda de foto
        self.styles.add(ParagraphStyle(
            name='PhotoCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=10
        ))
        
        # Rodapé
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=11
        ))
        
        # Assinatura
        self.styles.add(ParagraphStyle(
            name='Signature',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=6
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
            
            # Número do relatório
            story.append(Paragraph("Relatório", self.styles['SectionHeader']))
            story.append(Paragraph(f"Relatório Número<br/><b>{relatorio.numero}</b>", self.styles['ReportNumber']))
            story.append(Spacer(1, 20))
            
            # Dados gerais
            story.extend(self._create_dados_gerais(relatorio))
            story.append(Spacer(1, 20))
            
            # Itens observados
            story.extend(self._create_itens_observados(relatorio, fotos))
            story.append(Spacer(1, 30))
            
            # Assinaturas
            story.extend(self._create_assinaturas(relatorio))
            story.append(Spacer(1, 30))
            
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
        
        # Linha 1: Título centralizado
        title = Paragraph("Relatório de Visita", self.styles['MainTitle'])
        elements.append(title)
        elements.append(Spacer(1, 40))
        
        # Linha 2: Data no canto direito
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        date_p = Paragraph(f"Em: {data_atual}", self.styles['HeaderDate'])
        
        # Tabela para posicionar a data no canto direito
        date_table = Table([[date_p]], colWidths=[A4[0]-40*mm])
        date_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(date_table)
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_dados_gerais(self, relatorio):
        """Criar seção de dados gerais"""
        elements = []
        
        # Título da seção
        elements.append(Paragraph("Dados gerais", self.styles['SectionHeader']))
        elements.append(Spacer(1, 10))
        
        # Tabela com dados gerais
        projeto = relatorio.projeto
        
        # Dados da tabela
        data = [
            ["Empresa", "Obra", "Endereço"],
            [
                projeto.responsavel.nome_completo if projeto.responsavel else "ELP Consultoria",
                f"{projeto.nome}",
                projeto.endereco or "Não informado"
            ]
        ]
        
        # Criar tabela
        table = Table(data, colWidths=[60*mm, 60*mm, 60*mm])
        table.setStyle(TableStyle([
            # Cabeçalho
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Alinhamento
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_itens_observados(self, relatorio, fotos):
        """Criar seção de itens observados com fotos"""
        elements = []
        
        # Título da seção
        elements.append(Paragraph("Itens observados", self.styles['SectionHeader']))
        elements.append(Spacer(1, 10))
        
        # Texto de observações (usar campo conteudo se disponível, senão texto padrão)
        if hasattr(relatorio, 'conteudo') and relatorio.conteudo:
            elements.append(Paragraph(relatorio.conteudo, self.styles['NormalText']))
        else:
            elements.append(Paragraph("..<br/>Vide fotos.", self.styles['NormalText']))
        
        elements.append(Spacer(1, 20))
        
        # Adicionar fotos em pares (2 por linha como no modelo)
        if fotos:
            elements.extend(self._create_photos_section(fotos))
        
        return elements
    
    def _create_photos_section(self, fotos):
        """Criar seção de fotos em pares"""
        elements = []
        
        # Processar fotos em pares
        for i in range(0, len(fotos), 2):
            foto1 = fotos[i]
            foto2 = fotos[i + 1] if i + 1 < len(fotos) else None
            
            # Criar linha com 1 ou 2 fotos
            photo_row = self._create_photo_row(foto1, foto2)
            elements.extend(photo_row)
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_photo_row(self, foto1, foto2=None):
        """Criar uma linha com 1 ou 2 fotos"""
        elements = []
        
        try:
            # Preparar dados da linha
            photos_data = []
            captions_data = []
            
            # Primeira foto
            if foto1:
                img1_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), foto1.filename)
                if os.path.exists(img1_path):
                    img1 = Image(img1_path, width=80*mm, height=60*mm)
                    photos_data.append(img1)
                    caption1 = foto1.descricao or f"Foto {foto1.ordem}"
                    captions_data.append(caption1)
                else:
                    photos_data.append("Imagem não encontrada")
                    captions_data.append(foto1.descricao or f"Foto {foto1.ordem}")
            
            # Segunda foto (se existir)
            if foto2:
                img2_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), foto2.filename)
                if os.path.exists(img2_path):
                    img2 = Image(img2_path, width=80*mm, height=60*mm)
                    photos_data.append(img2)
                    caption2 = foto2.descricao or f"Foto {foto2.ordem}"
                    captions_data.append(caption2)
                else:
                    photos_data.append("Imagem não encontrada")
                    captions_data.append(foto2.descricao or f"Foto {foto2.ordem}")
            else:
                # Preencher espaço vazio se só houver uma foto
                photos_data.append("")
                captions_data.append("")
            
            # Tabela de fotos
            if len(photos_data) == 2:
                photos_table = Table([photos_data], colWidths=[90*mm, 90*mm])
                captions_table = Table([captions_data], colWidths=[90*mm, 90*mm])
            else:
                photos_table = Table([photos_data], colWidths=[90*mm])
                captions_table = Table([captions_data], colWidths=[90*mm])
            
            # Estilo da tabela de fotos
            photos_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            # Estilo da tabela de legendas
            captions_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(photos_table)
            elements.append(captions_table)
            
        except Exception as e:
            # Em caso de erro, adicionar texto informativo
            elements.append(Paragraph(f"Erro ao carregar fotos: {str(e)}", self.styles['NormalText']))
        
        return elements
    
    def _create_assinaturas(self, relatorio):
        """Criar seção de assinaturas"""
        elements = []
        
        # Título da seção
        elements.append(Paragraph("Assinaturas", self.styles['SectionHeader']))
        elements.append(Spacer(1, 10))
        
        # Dados das assinaturas
        preenchido_por = relatorio.autor.nome_completo if relatorio.autor else "Não informado"
        liberado_por = "Eng. José Leopoldo Pugliese"  # Valor fixo conforme modelo
        responsavel = relatorio.projeto.responsavel.nome_completo if relatorio.projeto and relatorio.projeto.responsavel else "Não informado"
        
        # Tabela de assinaturas
        sig_data = [
            ["Preenchido por:", "Liberado por:", "Responsável pelo acompanhamento"],
            [preenchido_por, liberado_por, responsavel]
        ]
        
        sig_table = Table(sig_data, colWidths=[60*mm, 60*mm, 60*mm])
        sig_table.setStyle(TableStyle([
            # Cabeçalho
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Alinhamento
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(sig_table)
        return elements
    
    def _create_footer(self):
        """Criar rodapé da empresa"""
        footer_text = """<b>ELP Consultoria</b><br/>
Rua Jaboticabal, 530 apto. 31 - São Paulo - SP - CEP: 03188-000<br/>
leopoldo@elpconsultoria.eng.br<br/>
Telefone: (11) 99138-4517"""
        
        # Adicionar texto no canto direito sobre geração do relatório
        generated_text = "Relatório gerado no Sistema ELP"
        
        footer_data = [
            [Paragraph(footer_text, self.styles['Footer']), Paragraph(generated_text, self.styles['Footer'])]
        ]
        
        footer_table = Table(footer_data, colWidths=[120*mm, 60*mm])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        return footer_table