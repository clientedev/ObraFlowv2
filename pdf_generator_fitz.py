"""
Gerador de PDF usando PyMuPDF (fitz) para preservar exatamente o modelo Artesano
Mantém toda a identidade visual original e preenche apenas os campos dinâmicos
"""

import fitz  # PyMuPDF
import os
from datetime import datetime
from flask import current_app
import tempfile

class ArtesanoPDFGeneratorFitz:
    def __init__(self):
        self.template_path = "templates/pdf_template_artesano.pdf"
        
    def generate_report_pdf(self, relatorio, fotos, output_path=None):
        """
        Gera PDF usando o modelo como base e preenchendo os campos dinâmicos
        
        Args:
            relatorio: Objeto do relatório
            fotos: Lista de fotos do relatório
            output_path: Caminho para salvar o PDF (opcional)
            
        Returns:
            bytes do PDF ou caminho do arquivo salvo
        """
        try:
            # Verificar se template existe
            if not os.path.exists(self.template_path):
                raise Exception(f"Template PDF não encontrado: {self.template_path}")
            
            # Abrir o PDF template
            doc = fitz.open(self.template_path)
            page = doc[0]  # Primeira página
            
            # Preparar dados dinâmicos
            data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
            projeto = relatorio.projeto
            
            # Dados das assinaturas
            preenchido_por = relatorio.autor.nome_completo if relatorio.autor else "Não informado"
            liberado_por = "Eng. José Leopoldo Pugliese"
            responsavel = relatorio.projeto.responsavel.nome_completo if relatorio.projeto and relatorio.projeto.responsavel else "Não informado"
            
            # Substituições usando coordenadas exatas do template original
            substituicoes = [
                # Data no cabeçalho - substituir "Em: 12/03/2025 14:38"
                {"original": "Em: 12/03/2025 14:38", "novo": f"Em: {data_atual}", 
                 "posicao": (498.8, 74.7), "fonte": "helv", "tamanho": 10},
                
                # Número do relatório - substituir "45"
                {"original": "45", "novo": str(relatorio.numero).replace("REL-", ""), 
                 "posicao": (14.3, 156.3), "fonte": "helv", "tamanho": 14},  # Posição logo abaixo de "Relatório Número"
                
                # Empresa - substituir "R. Yazbek"
                {"original": "R. Yazbek", "novo": projeto.responsavel.nome_completo if projeto.responsavel else "ELP Consultoria",
                 "posicao": (14.3, 219.3), "fonte": "helv", "tamanho": 11},
                
                # Obra - substituir "Artesano Oscar Porto"
                {"original": "Artesano Oscar Porto", "novo": projeto.nome,
                 "posicao": (204.0, 219.3), "fonte": "helv", "tamanho": 11},
                
                # Endereço - substituir "Rua Coronel Oscar Porto 507 - Paraíso"
                {"original": "Rua Coronel Oscar Porto 507 - ", "novo": projeto.endereco or "Não informado",
                 "posicao": (393.8, 219.3), "fonte": "helv", "tamanho": 11},
                
                # Itens observados - substituir "Vide fotos."
                {"original": "Vide fotos.", "novo": relatorio.conteudo if hasattr(relatorio, 'conteudo') and relatorio.conteudo else "Vide fotos.",
                 "posicao": (14.3, 282.4), "fonte": "helv", "tamanho": 11},
                
                # Assinatura - Preenchido por
                {"original": "Eng. Mateus Almeida", "novo": preenchido_por,
                 "posicao": (14.3, 618.0), "fonte": "helv", "tamanho": 11},
                
                # Assinatura - Liberado por
                {"original": "Eng. José Leopoldo Pugliese", "novo": liberado_por,
                 "posicao": (204.0, 618.0), "fonte": "helv", "tamanho": 11},
                
                # Assinatura - Responsável
                {"original": "Raphael", "novo": responsavel,
                 "posicao": (393.8, 618.0), "fonte": "helv", "tamanho": 11},
            ]
            
            # Realizar substituições de texto mantendo formatação
            for sub in substituicoes:
                self._substituir_texto(page, sub["original"], sub["novo"], 
                                     sub["posicao"], sub["fonte"], sub["tamanho"])
            
            # Adicionar fotos se houver
            if fotos:
                self._inserir_fotos(page, fotos)
            
            # Salvar PDF
            if output_path:
                doc.save(output_path)
                doc.close()
                return output_path
            else:
                # Retornar bytes do PDF
                pdf_bytes = doc.write()
                doc.close()
                return pdf_bytes
                
        except Exception as e:
            raise Exception(f"Erro ao gerar PDF com PyMuPDF: {str(e)}")
    
    def _substituir_texto(self, page, texto_original, texto_novo, posicao, fonte, tamanho):
        """Substituir texto existente mantendo formatação original"""
        try:
            # Remover texto original criando retângulo branco sobre ele
            text_width = len(texto_original) * (tamanho * 0.6)  # Aproximação da largura
            text_height = tamanho + 2
            
            rect = fitz.Rect(posicao[0], posicao[1] - text_height + 2, 
                           posicao[0] + text_width, posicao[1] + 2)
            
            # Cobrir o texto original com um retângulo branco
            page.draw_rect(rect, color=None, fill=(1, 1, 1), width=0)
            
            # Inserir novo texto na mesma posição
            page.insert_text(
                posicao,
                texto_novo,
                fontname=fonte,
                fontsize=tamanho,
                color=(0, 0, 0)  # Preto
            )
        except Exception as e:
            print(f"Erro ao substituir texto '{texto_original}' por '{texto_novo}': {e}")
    
    def _inserir_fotos(self, page, fotos):
        """Inserir fotos no PDF mantendo layout em pares"""
        try:
            # Posições baseadas no template original onde aparecem as legendas das fotos
            pos_x_esq = 19.7   # Foto da esquerda (posição da primeira legenda)
            pos_x_dir = 302.5  # Foto da direita (posição da segunda legenda)
            pos_y = 350        # Posição vertical para as fotos (acima das legendas)
            
            foto_width = 140
            foto_height = 105
            espaco_vertical = 150
            
            # Determinar caminho do upload folder
            try:
                from flask import current_app
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            except RuntimeError:
                # Fora do contexto do Flask
                upload_folder = 'uploads'
            
            for i, foto in enumerate(fotos[:4]):  # Máximo 4 fotos para manter layout
                # Alternar entre esquerda e direita
                if i % 2 == 0:
                    pos_x = pos_x_esq
                else:
                    pos_x = pos_x_dir
                
                # Nova linha a cada 2 fotos
                if i > 0 and i % 2 == 0:
                    pos_y += espaco_vertical
                
                # Caminho da imagem
                img_path = os.path.join(upload_folder, foto.filename)
                
                if os.path.exists(img_path):
                    # Definir retângulo para a imagem
                    rect = fitz.Rect(pos_x, pos_y, pos_x + foto_width, pos_y + foto_height)
                    
                    # Inserir imagem
                    page.insert_image(rect, filename=img_path)
                    
                    # Adicionar legenda abaixo da foto
                    legenda = foto.descricao or f"Foto {foto.ordem}"
                    legenda_pos = (pos_x, pos_y + foto_height + 5)
                    
                    page.insert_text(
                        legenda_pos,
                        legenda,
                        fontname="helv",
                        fontsize=9,
                        color=(0.3, 0.3, 0.3)  # Cinza escuro
                    )
                    
        except Exception as e:
            print(f"Erro ao inserir fotos: {e}")
    
    def _criar_nome_arquivo(self, relatorio):
        """Criar nome do arquivo no padrão especificado"""
        data_str = datetime.now().strftime('%Y%m%d')
        numero_limpo = relatorio.numero.replace('/', '_')
        return f"relatorio_{numero_limpo}_{data_str}.pdf"