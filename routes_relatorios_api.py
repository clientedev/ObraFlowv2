"""
API REST para gerenciamento de relatórios com salvamento automático
Implementação conforme especificação técnica profissional
"""
import os
import logging
import uuid
import shutil
from datetime import datetime
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app import app, db, csrf
from models import Relatorio, FotoRelatorio, Projeto, User
import traceback # Import traceback for detailed error logging
import json # Import json for handling JSON data

# Configuração de logging
logger = logging.getLogger(__name__)

# Configurações de upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
TEMP_UPLOAD_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file, relatorio_id):
    """
    Salva imagem enviada e retorna informações do arquivo

    Args:
        file: FileStorage object do werkzeug
        relatorio_id: ID do relatório

    Returns:
        dict: Informações do arquivo salvo (filename, url, content_type, size)
    """
    if not file or not allowed_file(file.filename):
        raise ValueError("Arquivo inválido ou tipo não permitido")

    # Salvar temporariamente para verificar tamanho
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False) as temp_file:
        file.save(temp_file.name)
        file_size = os.path.getsize(temp_file.name)

        # Validar tamanho do arquivo
        if file_size > MAX_FILE_SIZE:
            os.unlink(temp_file.name)  # Remover arquivo temporário
            raise ValueError(f"Arquivo muito grande: {file_size / (1024*1024):.2f}MB. Máximo permitido: {MAX_FILE_SIZE / (1024*1024):.0f}MB")

        # Gerar nome de arquivo seguro e único
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        filename = f"relatorio_{relatorio_id}_{timestamp}_{original_filename}"

        # Caminho completo para salvar
        upload_folder = app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, filename)

        # Mover arquivo temporário para destino final
        import shutil
        shutil.move(temp_file.name, filepath)

        # URL relativa
        url = f"/uploads/{filename}"

        return {
            'filename': filename,
            'url': url,
            'content_type': file.content_type,
            'size': file_size
        }

# Criar pasta de uploads temporários se não existir
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/uploads/temp', methods=['POST'])
@csrf.exempt  # 🔐 Excluir da proteção CSRF - autenticação via session é suficiente
@login_required
def api_upload_temp():
    """
    POST /api/uploads/temp

    Upload rápido de imagem para storage temporário.
    Retorna temp_id para posterior associação ao relatório via autosave.

    Conforme especificação técnica do AutoSave.

    Nota: CSRF é verificado apenas se o token estiver presente.
    A autenticação via session/cookie é suficiente para segurança.

    Returns:
        JSON: {temp_id, path, filename, size, mime_type, category, local, caption}
    """
    try:
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nome de arquivo vazio'
            }), 400

        # Validar extensão do arquivo
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Tipo de arquivo não permitido. Tipos aceitos: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Obter metadados adicionais do form
        category = request.form.get('category', '')
        local = request.form.get('local', '')
        caption = request.form.get('caption', '')

        # Salvar temporariamente para verificar tamanho
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            file_size = os.path.getsize(temp_file.name)

            # Validar tamanho do arquivo
            if file_size > MAX_FILE_SIZE:
                os.unlink(temp_file.name)
                return jsonify({
                    'success': False,
                    'error': f'Arquivo muito grande: {file_size / (1024*1024):.2f}MB. Máximo: {MAX_FILE_SIZE / (1024*1024):.0f}MB'
                }), 413

            # Gerar temp_id único
            temp_id = str(uuid.uuid4())

            # Nome de arquivo seguro e único
            original_filename = secure_filename(file.filename)
            extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
            temp_filename = f"{temp_id}.{extension}"

            # Caminho completo para salvar na pasta temporária
            temp_filepath = os.path.join(TEMP_UPLOAD_FOLDER, temp_filename)

            # Mover arquivo temporário para pasta de uploads temporários
            shutil.move(temp_file.name, temp_filepath)

            # Path relativo para retornar ao frontend
            relative_path = f"/uploads/temp/{temp_filename}"

            logger.info(f"✅ Upload temporário: {temp_filename} ({file_size / 1024:.2f}KB) - temp_id: {temp_id}")

            return jsonify({
                'success': True,
                'temp_id': temp_id,
                'path': relative_path,
                'filename': temp_filename,
                'original_filename': file.filename,
                'size': file_size,
                'mime_type': file.content_type or 'image/jpeg',
                'category': category,
                'local': local,
                'caption': caption
            }), 200

    except Exception as e:
        logger.error(f"Erro no upload temporário: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erro ao processar upload',
            'details': str(e)
        }), 500

@app.route('/api/relatorios', methods=['POST'])
@login_required
def api_criar_relatorio():
    """
    POST /api/relatorios

    Cria um novo relatório e retorna o id.
    Suporte a upload inicial de imagens (multipart/form-data).
    Persiste metadados e estrutura completa conforme o novo modelo.
    """
    try:
        # Verificar se é multipart (com imagens) ou JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Dados do formulário multipart
            data = request.form.to_dict()
            files = request.files.getlist('imagens')
        else:
            # Dados JSON
            data = request.get_json()
            files = []

        # Validar campos obrigatórios
        if not data.get('projeto_id'):
            return jsonify({
                'success': False,
                'error': 'Campo projeto_id é obrigatório'
            }), 400

        # Verificar se projeto existe
        projeto = Projeto.query.get(data['projeto_id'])
        if not projeto:
            return jsonify({
                'success': False,
                'error': f"Projeto {data['projeto_id']} não encontrado"
            }), 404

        # Gerar número do relatório
        # Buscar último número do projeto
        ultimo_relatorio = Relatorio.query.filter_by(
            projeto_id=data['projeto_id']
        ).order_by(Relatorio.numero_projeto.desc()).first()

        if ultimo_relatorio and ultimo_relatorio.numero_projeto:
            proximo_numero = ultimo_relatorio.numero_projeto + 1
        else:
            proximo_numero = projeto.numeracao_inicial or 1

        numero_formatado = f"{projeto.numero}-R{proximo_numero:03d}"

        # Criar novo relatório
        novo_relatorio = Relatorio(
            numero=numero_formatado,
            numero_projeto=proximo_numero,
            titulo=data.get('titulo', 'Relatório de visita'),
            descricao=data.get('descricao'),
            projeto_id=data['projeto_id'],
            visita_id=data.get('visita_id'),
            autor_id=current_user.id,
            criado_por=current_user.id,
            atualizado_por=current_user.id,

            # Novos campos conforme especificação
            categoria=data.get('categoria'),
            local=data.get('local'),
            observacoes_finais=data.get('observacoes_finais'),

            # Data/hora
            data_relatorio=datetime.utcnow(),

            # Status
            status=data.get('status', 'em_andamento'),

            # Outros campos
            conteudo=data.get('conteudo'),
            checklist_data=data.get('checklist_data'),
            acompanhantes=data.get('acompanhantes')
        )

        # Processar lembrete_proxima_visita se fornecido
        if data.get('lembrete_proxima_visita'):
            try:
                if isinstance(data['lembrete_proxima_visita'], str):
                    novo_relatorio.lembrete_proxima_visita = datetime.fromisoformat(
                        data['lembrete_proxima_visita'].replace('Z', '+00:00')
                    )
                else:
                    novo_relatorio.lembrete_proxima_visita = data['lembrete_proxima_visita']
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro ao processar lembrete_proxima_visita: {e}")

        # Salvar relatório no banco
        db.session.add(novo_relatorio)
        db.session.flush()  # Obter ID sem fazer commit

        # Processar imagens se houver
        imagens_salvas = []
        if files:
            for ordem, file in enumerate(files):
                if file and file.filename:
                    try:
                        # Salvar arquivo (pode lançar ValueError se tamanho exceder limite)
                        file_info = save_uploaded_image(file, novo_relatorio.id)

                        # Criar registro no banco
                        foto = FotoRelatorio(
                            relatorio_id=novo_relatorio.id,
                            filename=file_info['filename'],
                            url=file_info['url'],
                            legenda=request.form.get(f'legenda_{ordem}', ''),
                            ordem=ordem,
                            content_type=file_info['content_type'],
                            imagem_size=file_info['size']
                        )
                        db.session.add(foto)

                        imagens_salvas.append({
                            'id': None,  # Será preenchido após commit
                            'url': file_info['url'],
                            'legenda': foto.legenda,
                            'ordem': ordem
                        })
                    except ValueError as val_error:
                        # Erro de validação (tamanho, tipo, etc)
                        db.session.rollback()
                        logger.error(f"Erro de validação ao processar imagem: {val_error}")
                        return jsonify({
                            'success': False,
                            'error': 'Erro de validação de arquivo',
                            'details': str(val_error)
                        }), 413  # Payload Too Large
                    except Exception as img_error:
                        # Outros erros inesperados
                        db.session.rollback()
                        logger.error(f"Erro inesperado ao processar imagem: {img_error}")
                        return jsonify({
                            'success': False,
                            'error': 'Erro ao processar imagem',
                            'details': str(img_error)
                        }), 400

        # Commit da transação
        db.session.commit()

        # Atualizar IDs das imagens
        for i, foto in enumerate(novo_relatorio.imagens.order_by(FotoRelatorio.ordem).all()):
            if i < len(imagens_salvas):
                imagens_salvas[i]['id'] = foto.id

        return jsonify({
            'success': True,
            'id': novo_relatorio.id,
            'numero': novo_relatorio.numero,
            'imagens': imagens_salvas,
            'message': 'Relatório criado com sucesso'
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Erro de integridade ao criar relatório: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro de integridade no banco de dados',
            'details': str(e)
        }), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar relatório: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao criar relatório',
            'details': str(e)
        }), 500

@app.route('/api/relatorios/<int:relatorio_id>', methods=['GET'])
@login_required
def get_relatorio(relatorio_id):
    """Buscar dados completos de um relatório específico para edição"""
    try:
        relatorio = Relatorio.query.get_or_404(relatorio_id)

        # Verificar permissão
        if not current_user.is_master and relatorio.autor_id != current_user.id:
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        # Buscar dados do projeto
        projeto = None
        if relatorio.projeto_id:
            projeto_obj = Projeto.query.get(relatorio.projeto_id)
            if projeto_obj:
                projeto = {
                    'id': projeto_obj.id,
                    'nome': projeto_obj.nome,
                    'numero': projeto_obj.numero,
                    'endereco': projeto_obj.endereco
                }

        # Buscar imagens do relatório
        imagens = []
        fotos = FotoRelatorio.query.filter_by(relatorio_id=relatorio.id).order_by(FotoRelatorio.ordem).all()
        for foto in fotos:
            # Determinar o path da imagem - CORRIGIDO: verificar se não é string vazia
            image_path = None
            if foto.url and foto.url.strip():
                image_path = foto.url
            elif foto.filename and foto.filename.strip():
                image_path = f"/uploads/{foto.filename}"
            else:
                # Fallback para gerar URL a partir do ID - para fotos antigas sem url/filename
                image_path = f"/get_imagem/{foto.id}"

            imagens.append({
                'id': foto.id,
                'path': image_path,
                'url': image_path,
                'filename': foto.filename,
                'legenda': foto.legenda or '',
                'caption': foto.legenda or '',
                'tipo_servico': foto.tipo_servico or '',
                'category': foto.tipo_servico or '',
                'local': foto.local or '',
                'ordem': foto.ordem or 0
            })

        # Processar checklist_data
        checklist = []
        if relatorio.checklist_data:
            try:
                if isinstance(relatorio.checklist_data, str):
                    checklist = json.loads(relatorio.checklist_data)
                elif isinstance(relatorio.checklist_data, list):
                    checklist = relatorio.checklist_data
            except:
                checklist = []

        # Processar acompanhantes
        acompanhantes = []
        if relatorio.acompanhantes:
            try:
                if isinstance(relatorio.acompanhantes, str):
                    acompanhantes = json.loads(relatorio.acompanhantes)
                elif isinstance(relatorio.acompanhantes, list):
                    acompanhantes = relatorio.acompanhantes
            except:
                acompanhantes = []

        # Serializar relatório completo
        relatorio_data = {
            'id': relatorio.id,
            'numero': relatorio.numero,
            'titulo': relatorio.titulo or 'Relatório de visita',
            'projeto_id': relatorio.projeto_id,
            'data_relatorio': relatorio.data_relatorio.isoformat() if relatorio.data_relatorio else None,
            'categoria': relatorio.categoria or '',
            'local': relatorio.local or '',
            'observacoes_finais': relatorio.observacoes_finais or '',
            'lembrete_proxima_visita': relatorio.lembrete_proxima_visita.isoformat() if relatorio.lembrete_proxima_visita else None,
            'conteudo': relatorio.conteudo or '',
            'status': relatorio.status or 'em_andamento',
            'created_at': relatorio.created_at.isoformat() if relatorio.created_at else None,
            'updated_at': relatorio.updated_at.isoformat() if relatorio.updated_at else None
        }

        return jsonify({
            'success': True,
            'relatorio': relatorio_data,
            'projeto': projeto,
            'imagens': imagens,
            'checklist': checklist,
            'acompanhantes': acompanhantes
        })

    except Exception as e:
        current_app.logger.error(f'Erro ao buscar relatório {relatorio_id}: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios/<int:relatorio_id>', methods=['PUT'])
@login_required
def api_atualizar_relatorio(relatorio_id):
    """
    PUT /api/relatorios/<id>

    Atualiza todos os campos do relatório existente.
    Sincroniza imagens: adiciona novas, atualiza legendas/ordem e remove as excluídas.
    Suporta salvamento automático incremental (via timestamps).
    Trata corretamente tanto payload JSON quanto multipart.
    """
    try:
        relatorio = Relatorio.query.get(relatorio_id)

        if not relatorio:
            return jsonify({
                'success': False,
                'error': 'Relatório não encontrado'
            }), 404

        # Verificar se é multipart (com imagens) ou JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            files = request.files.getlist('novas_imagens')
        else:
            data = request.get_json()
            files = []

        # Atualizar campos do relatório
        if 'titulo' in data:
            relatorio.titulo = data['titulo']
        if 'descricao' in data:
            relatorio.descricao = data['descricao']
        if 'categoria' in data:
            relatorio.categoria = data['categoria']
        if 'local' in data:
            relatorio.local = data['local']
        if 'observacoes_finais' in data:
            relatorio.observacoes_finais = data['observacoes_finais']
        if 'conteudo' in data:
            relatorio.conteudo = data['conteudo']
        if 'checklist_data' in data:
            relatorio.checklist_data = data['checklist_data']
        if 'status' in data:
            relatorio.status = data['status']

        # Processar lembrete_proxima_visita
        if 'lembrete_proxima_visita' in data:
            if data['lembrete_proxima_visita']:
                try:
                    if isinstance(data['lembrete_proxima_visita'], str):
                        relatorio.lembrete_proxima_visita = datetime.fromisoformat(
                            data['lembrete_proxima_visita'].replace('Z', '+00:00')
                        )
                    else:
                        relatorio.lembrete_proxima_visita = data['lembrete_proxima_visita']
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar lembrete_proxima_visita: {e}")
            else:
                relatorio.lembrete_proxima_visita = None

        # Atualizar metadados
        relatorio.atualizado_por = current_user.id
        relatorio.updated_at = datetime.utcnow()

        # Processar sincronização de imagens
        imagens_atualizadas = []

        # 1. Processar remoção de imagens (se especificado)
        if 'imagens_excluidas' in data:
            try:
                imagens_excluidas = data['imagens_excluidas']
                if isinstance(imagens_excluidas, str):
                    import json
                    imagens_excluidas = json.loads(imagens_excluidas)

                for img_id in imagens_excluidas:
                    foto = FotoRelatorio.query.get(img_id)
                    if foto and foto.relatorio_id == relatorio_id:
                        # Remover arquivo físico se existir
                        if foto.filename:
                            filepath = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
                            if os.path.exists(filepath):
                                os.remove(filepath)
                        db.session.delete(foto)
            except Exception as e:
                logger.error(f"Erro ao processar exclusão de imagens: {e}")

        # 2. Atualizar legendas e ordem de imagens existentes
        if 'imagens' in data:
            try:
                imagens_info = data['imagens']
                if isinstance(imagens_info, str):
                    import json
                    imagens_info = json.loads(imagens_info)

                for img_info in imagens_info:
                    if 'id' in img_info:
                        foto = FotoRelatorio.query.get(img_info['id'])
                        if foto and foto.relatorio_id == relatorio_id:
                            if 'legenda' in img_info:
                                foto.legenda = img_info['legenda']
                            if 'ordem' in img_info:
                                foto.ordem = img_info['ordem']
            except Exception as e:
                logger.error(f"Erro ao atualizar imagens: {e}")

        # 3. Adicionar novas imagens
        if files:
            # Obter ordem máxima atual
            max_ordem = db.session.query(db.func.max(FotoRelatorio.ordem)).filter_by(
                relatorio_id=relatorio_id
            ).scalar() or -1

            for idx, file in enumerate(files):
                if file and file.filename:
                    try:
                        # Salvar arquivo (pode lançar ValueError se tamanho exceder limite)
                        file_info = save_uploaded_image(file, relatorio_id)

                        nova_foto = FotoRelatorio(
                            relatorio_id=relatorio_id,
                            filename=file_info['filename'],
                            url=file_info['url'],
                            legenda=request.form.get(f'legenda_{idx}', ''),
                            ordem=max_ordem + idx + 1,
                            content_type=file_info['content_type'],
                            imagem_size=file_info['size']
                        )
                        db.session.add(nova_foto)

                        imagens_atualizadas.append({
                            'url': file_info['url'],
                            'legenda': nova_foto.legenda,
                            'ordem': nova_foto.ordem
                        })
                    except ValueError as val_error:
                        # Erro de validação (tamanho, tipo, etc)
                        db.session.rollback()
                        logger.error(f"Erro de validação ao adicionar nova imagem: {val_error}")
                        return jsonify({
                            'success': False,
                            'error': 'Erro de validação de arquivo',
                            'details': str(val_error)
                        }), 413  # Payload Too Large
                    except Exception as img_error:
                        # Outros erros inesperados
                        db.session.rollback()
                        logger.error(f"Erro inesperado ao adicionar nova imagem: {img_error}")
                        return jsonify({
                            'success': False,
                            'error': 'Erro ao processar imagem',
                            'details': str(img_error)
                        }), 400

        # Commit das alterações
        db.session.commit()

        # Buscar estado atualizado das imagens
        imagens_finais = [{
            'id': img.id,
            'url': img.url or f"/uploads/{img.filename}" if img.filename else None,
            'legenda': img.legenda,
            'ordem': img.ordem
        } for img in relatorio.imagens.order_by(FotoRelatorio.ordem).all()]

        return jsonify({
            'success': True,
            'relatorio': {
                'id': relatorio.id,
                'numero': relatorio.numero,
                'titulo': relatorio.titulo,
                'updated_at': relatorio.updated_at.isoformat()
            },
            'imagens': imagens_finais,
            'message': 'Relatório atualizado com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar relatório {relatorio_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar relatório',
            'details': str(e)
        }), 500

@app.route('/api/relatorios/<int:relatorio_id>/imagens/<int:imagem_id>', methods=['DELETE'])
@login_required
def api_remover_imagem(relatorio_id, imagem_id):
    """
    DELETE /api/relatorios/<id>/imagens/<imagem_id>

    Remove uma imagem do relatório, tanto no banco quanto no armazenamento físico.
    """
    try:
        # Buscar imagem
        foto = FotoRelatorio.query.get(imagem_id)

        if not foto:
            return jsonify({
                'success': False,
                'error': 'Imagem não encontrada'
            }), 404

        # Verificar se a imagem pertence ao relatório especificado
        if foto.relatorio_id != relatorio_id:
            return jsonify({
                'success': False,
                'error': 'Imagem não pertence a este relatório'
            }), 403

        # Remover arquivo físico se existir
        if foto.filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Arquivo removido: {filepath}")
            except Exception as file_error:
                logger.error(f"Erro ao remover arquivo físico: {file_error}")
                # Continuar mesmo se falhar a remoção do arquivo

        # Remover registro do banco
        db.session.delete(foto)

        # Atualizar timestamp do relatório
        relatorio = Relatorio.query.get(relatorio_id)
        if relatorio:
            relatorio.updated_at = datetime.utcnow()
            relatorio.atualizado_por = current_user.id

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Imagem removida com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover imagem {imagem_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao remover imagem',
            'details': str(e)
        }), 500

@app.route('/api/relatorios/autosave', methods=['POST'])
@login_required
def api_autosave_relatorio():
    """
    POST /api/relatorios/autosave

    AutoSave completo do relatório - REPLICA EXATAMENTE o comportamento do botão "Concluir relatório"
    """
    try:
        data = request.get_json()

        # LOG: Dados recebidos
        print("📦 AutoSave - Dados recebidos:", data)

        if not data:
            print("❌ AutoSave: Nenhum dado fornecido")
            return jsonify({
                'success': False,
                'error': 'Nenhum dado fornecido'
            }), 400

        relatorio_id = data.get('id')
        print(f"🔍 AutoSave: relatório_id = {relatorio_id}")

        # 1️⃣ CRIAR NOVO RELATÓRIO SE NÃO EXISTIR
        if not relatorio_id:
            # Validar campos obrigatórios para criação
            if not data.get('projeto_id'):
                return jsonify({
                    'success': False,
                    'error': 'Campo projeto_id é obrigatório para criar novo relatório'
                }), 400

            # Verificar se projeto existe
            projeto = Projeto.query.get(data['projeto_id'])
            if not projeto:
                return jsonify({
                    'success': False,
                    'error': f"Projeto {data['projeto_id']} não encontrado"
                }), 404

            # Gerar número do relatório
            ultimo_relatorio = Relatorio.query.filter_by(
                projeto_id=data['projeto_id']
            ).order_by(Relatorio.numero_projeto.desc()).first()

            if ultimo_relatorio and ultimo_relatorio.numero_projeto:
                proximo_numero = ultimo_relatorio.numero_projeto + 1
            else:
                proximo_numero = projeto.numeracao_inicial or 1

            numero_formatado = data.get('numero') or f"{projeto.numero}-R{proximo_numero:03d}"

            # Processar lembrete_proxima_visita
            lembrete_proxima_visita = None
            if data.get('lembrete_proxima_visita'):
                try:
                    if isinstance(data['lembrete_proxima_visita'], str):
                        lembrete_proxima_visita = datetime.fromisoformat(
                            data['lembrete_proxima_visita'].replace('Z', '+00:00')
                        )
                    else:
                        lembrete_proxima_visita = data['lembrete_proxima_visita']
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar lembrete_proxima_visita: {e}")

            # Processar checklist_data - COMPATÍVEL COM ARRAY OU STRING
            checklist_data = data.get('checklist_data')
            if checklist_data is not None:
                if isinstance(checklist_data, str):
                    # Já é string JSON - validar
                    try:
                        import json
                        json.loads(checklist_data)  # Validar
                        print(f"✅ AutoSave: checklist_data (string) salvo")
                    except:
                        checklist_data = None
                        print(f"⚠️ AutoSave: checklist_data inválido, definido como None")
                elif isinstance(checklist_data, (dict, list)):
                    # Converter para JSON string
                    import json
                    checklist_data = json.dumps(checklist_data)
                    print(f"✅ AutoSave: checklist_data (array) convertido e salvo")
                else:
                    checklist_data = None
            else:
                checklist_data = None


            # Processar acompanhantes - COMPATÍVEL COM ARRAY OU STRING
            acompanhantes = data.get('acompanhantes')
            if acompanhantes is not None:
                if isinstance(acompanhantes, str):
                    # Parsear string JSON para array
                    try:
                        import json
                        acompanhantes = json.loads(acompanhantes)
                        if not isinstance(acompanhantes, list):
                            acompanhantes = []
                    except:
                        acompanhantes = []
                elif isinstance(acompanhantes, list):
                    # Já é array
                    pass
                else:
                    acompanhantes = []

                print(f"✅ AutoSave: {len(acompanhantes)} acompanhantes salvos")
            else:
                acompanhantes = []

            # Criar novo relatório
            novo_relatorio = Relatorio(
                numero=numero_formatado,
                numero_projeto=proximo_numero,
                titulo=data.get('titulo', 'Relatório de visita'),
                descricao=data.get('descricao'),
                projeto_id=data['projeto_id'],
                visita_id=data.get('visita_id'),
                autor_id=current_user.id,
                criado_por=current_user.id,
                atualizado_por=current_user.id,

                # Campos de AutoSave
                categoria=data.get('categoria'),
                local=data.get('local'),
                observacoes_finais=data.get('observacoes_finais'),
                lembrete_proxima_visita=lembrete_proxima_visita,

                # Data/hora
                data_relatorio=datetime.utcnow(),

                # Status
                status=data.get('status', 'em_andamento'),

                # Outros campos - SALVAR CORRETAMENTE
                conteudo=data.get('conteudo'),
                checklist_data=checklist_data,
                acompanhantes=acompanhantes
            )

            db.session.add(novo_relatorio)
            db.session.flush()  # Obter ID sem commit completo
            relatorio_id = novo_relatorio.id

            print(f"✅ AutoSave: Novo relatório criado com ID {relatorio_id}")
            print(f"   - Checklist: {checklist_data[:100] if checklist_data else 'None'}...")
            print(f"   - Acompanhantes: {acompanhantes}")
            logger.info(f"✅ AutoSave: Novo relatório criado com ID {relatorio_id}")

        # 2️⃣ ATUALIZAR RELATÓRIO EXISTENTE
        else:
            relatorio = Relatorio.query.get(relatorio_id)

            if not relatorio:
                return jsonify({
                    'success': False,
                    'error': 'Relatório não encontrado'
                }), 404

            # Atualizar campos texto/data
            campos_atualizaveis = [
                'titulo', 'descricao', 'categoria', 'local',
                'observacoes_finais', 'conteudo', 'status',
                'observacoes', 'endereco'
            ]

            for campo in campos_atualizaveis:
                if campo in data:
                    setattr(relatorio, campo, data[campo])

            # Atualizar coordenadas GPS se fornecidas
            if 'latitude' in data:
                relatorio.latitude = data['latitude']
            if 'longitude' in data:
                relatorio.longitude = data['longitude']

            # Atualizar data do relatório se fornecida
            if 'data_relatorio' in data and data['data_relatorio']:
                try:
                    if isinstance(data['data_relatorio'], str):
                        relatorio.data_relatorio = datetime.fromisoformat(
                            data['data_relatorio'].replace('Z', '+00:00')
                        )
                    else:
                        relatorio.data_relatorio = data['data_relatorio']
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar data_relatorio: {e}")

            # Atualizar lembrete_proxima_visita
            if 'lembrete_proxima_visita' in data:
                if data['lembrete_proxima_visita']:
                    try:
                        if isinstance(data['lembrete_proxima_visita'], str):
                            relatorio.lembrete_proxima_visita = datetime.fromisoformat(
                                data['lembrete_proxima_visita'].replace('Z', '+00:00')
                            )
                        else:
                            relatorio.lembrete_proxima_visita = data['lembrete_proxima_visita']
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Erro ao processar lembrete_proxima_visita: {e}")
                else:
                    relatorio.lembrete_proxima_visita = None

            # Atualizar checklist_data - COMPATÍVEL COM ARRAY OU STRING
            if 'checklist_data' in data:
                checklist_data = data['checklist_data']
                if checklist_data is not None:
                    if isinstance(checklist_data, str):
                        # Já é string JSON - validar
                        try:
                            import json
                            json.loads(checklist_data)  # Validar
                            relatorio.checklist_data = checklist_data
                            print(f"✅ AutoSave: checklist_data (string) salvo")
                        except:
                            relatorio.checklist_data = None
                            print(f"⚠️ AutoSave: checklist_data inválido, definido como None")
                    elif isinstance(checklist_data, (dict, list)):
                        # Converter para JSON string
                        import json
                        relatorio.checklist_data = json.dumps(checklist_data)
                        print(f"✅ AutoSave: checklist_data (array) convertido e salvo")
                    else:
                        relatorio.checklist_data = None
                else:
                    relatorio.checklist_data = None

            # Atualizar acompanhantes - COMPATÍVEL COM ARRAY OU STRING
            if 'acompanhantes' in data:
                acompanhantes = data['acompanhantes']
                if acompanhantes is not None:
                    if isinstance(acompanhantes, str):
                        # Parsear string JSON para array
                        try:
                            import json
                            acompanhantes = json.loads(acompanhantes)
                            if not isinstance(acompanhantes, list):
                                acompanhantes = []
                        except:
                            acompanhantes = []
                    elif isinstance(acompanhantes, list):
                        # Já é array
                        pass
                    else:
                        acompanhantes = []

                    relatorio.acompanhantes = acompanhantes
                    print(f"✅ AutoSave: {len(acompanhantes)} acompanhantes salvos")
                else:
                    relatorio.acompanhantes = []

            # Atualizar metadados de auditoria
            relatorio.atualizado_por = current_user.id
            relatorio.updated_at = datetime.utcnow()

            print(f"✅ AutoSave: Relatório {relatorio_id} atualizado")
            logger.info(f"✅ AutoSave: Relatório {relatorio_id} atualizado")

        # 3️⃣ SINCRONIZAR IMAGENS
        imagens_resultado = []

        if 'fotos' in data and data['fotos']:
            fotos_data = data['fotos']

            print(f"📸 AutoSave: Processando {len(fotos_data)} imagens")
            logger.info(f"📸 AutoSave: Processando {len(fotos_data)} imagens")

            for idx, foto_info in enumerate(fotos_data):
                print(f"📸 Imagem {idx}: {foto_info}")
                logger.info(f"📸 Imagem {idx}: {foto_info}")
                # Deletar imagem marcada para remoção
                if foto_info.get('deletar'):
                    foto_id = foto_info.get('id')
                    if foto_id:
                        foto = FotoRelatorio.query.get(foto_id)
                        if foto and foto.relatorio_id == relatorio_id:
                            # Remover arquivo físico se existir
                            if foto.filename:
                                filepath = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
                                try:
                                    if os.path.exists(filepath):
                                        os.remove(filepath)
                                        logger.info(f"AutoSave: Arquivo removido: {filepath}")
                                except Exception as file_error:
                                    logger.error(f"Erro ao remover arquivo: {file_error}")

                            db.session.delete(foto)
                            logger.info(f"AutoSave: Imagem {foto_id} marcada para exclusão")
                    continue

                # Adicionar nova imagem (sem id ou id=null)
                if not foto_info.get('id'):
                    # Processar temp_id (imagem do upload temporário)
                    if foto_info.get('temp_id'):
                        temp_id = foto_info['temp_id']

                        # 🔧 CORREÇÃO: Buscar arquivo temporário dinamicamente (qualquer extensão)
                        temp_filepath = None
                        extension = 'jpg'  # padrão

                        # Buscar arquivo que começa com temp_id na pasta temporária
                        import glob
                        temp_pattern = os.path.join(TEMP_UPLOAD_FOLDER, f"{temp_id}.*")
                        matching_files = glob.glob(temp_pattern)

                        if matching_files:
                            temp_filepath = matching_files[0]
                            # Extrair extensão do arquivo encontrado
                            extension = temp_filepath.rsplit('.', 1)[1].lower() if '.' in temp_filepath else 'jpg'
                            logger.info(f"📸 AutoSave: Arquivo temporário encontrado: {temp_filepath}")
                        else:
                            logger.error(f"❌ AutoSave: Nenhum arquivo temporário encontrado com padrão: {temp_pattern}")
                            logger.error(f"   Arquivos na pasta temp: {os.listdir(TEMP_UPLOAD_FOLDER)[:10]}")
                            continue

                        # Verificar se arquivo temporário existe
                        if not os.path.exists(temp_filepath):
                            logger.error(f"AutoSave: Arquivo temporário não encontrado: {temp_filepath}")
                            continue

                        # Ler arquivo temporário como bytes para salvar no banco
                        try:
                            with open(temp_filepath, 'rb') as f:
                                image_bytes = f.read()

                            if not image_bytes:
                                logger.error(f"AutoSave: Arquivo temporário vazio: {temp_filepath}")
                                continue

                            logger.info(f"AutoSave: Arquivo temporário lido: {len(image_bytes)} bytes")
                        except Exception as read_error:
                            logger.error(f"Erro ao ler arquivo temporário: {read_error}")
                            continue

                        # Gerar nome definitivo (extension já foi extraída do arquivo temp)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
                        final_filename = f"relatorio_{relatorio_id}_{timestamp}_{temp_id}.{extension}"
                        final_filepath = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)

                        logger.info(f"📸 PROCESSANDO temp_id={temp_id}:")
                        logger.info(f"   - temp_filepath: {temp_filepath}")
                        logger.info(f"   - final_filepath: {final_filepath}")
                        logger.info(f"   - temp existe: {os.path.exists(temp_filepath)}")

                        # Copiar arquivo de temp para pasta definitiva (manter temp para retry se necessário)
                        try:
                            shutil.copy2(temp_filepath, final_filepath)
                            logger.info(f"✅ Arquivo copiado: {final_filename}")
                        except Exception as copy_error:
                            logger.error(f"❌ Erro ao copiar arquivo: {copy_error}")
                            continue

                        # Calcular hash da imagem para prevenir duplicatas
                        import hashlib
                        imagem_hash = hashlib.sha256(image_bytes).hexdigest()

                        # Criar registro no banco COM DADOS BINÁRIOS
                        nova_foto = FotoRelatorio(
                            relatorio_id=relatorio_id,
                            url=f"/uploads/{final_filename}",
                            filename=final_filename,
                            imagem=image_bytes,  # SALVAR BYTES NO BANCO
                            imagem_hash=imagem_hash,
                            imagem_size=len(image_bytes),
                            content_type=f"image/{extension}",
                            legenda=foto_info.get('caption') or foto_info.get('legenda') or '',
                            titulo=foto_info.get('titulo') or '',
                            tipo_servico=foto_info.get('tipo_servico') or foto_info.get('category') or 'Geral',
                            local=foto_info.get('local') or '',
                            ordem=foto_info.get('ordem', idx)
                        )
                        db.session.add(nova_foto)
                        db.session.flush()  # Para obter o ID

                        # Remover arquivo temporário após sucesso
                        try:
                            os.remove(temp_filepath)
                            logger.info(f"AutoSave: Arquivo temporário removido: {temp_filepath}")
                        except:
                            pass

                        imagens_resultado.append({
                            'id': nova_foto.id,
                            'url': nova_foto.url,
                            'filename': nova_foto.filename,
                            'legenda': nova_foto.legenda,
                            'ordem': nova_foto.ordem,
                            'temp_id': temp_id  # Retornar para frontend mapear
                        })
                        logger.info(f"✅ AutoSave: Imagem temp_id={temp_id} SALVA NO BANCO com id={nova_foto.id} ({len(image_bytes)} bytes)")

                    # Imagens já salvas no filesystem - ler arquivo e salvar bytes no banco
                    elif foto_info.get('url') or foto_info.get('filename'):
                        filename = foto_info.get('filename')
                        image_bytes = None

                        # Tentar ler arquivo do filesystem
                        if filename:
                            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            if os.path.exists(filepath):
                                try:
                                    with open(filepath, 'rb') as f:
                                        image_bytes = f.read()

                                    if not image_bytes:
                                        logger.error(f"AutoSave: Arquivo vazio no filesystem: {filename}")
                                        continue

                                    logger.info(f"AutoSave: Arquivo lido do filesystem: {filename} ({len(image_bytes)} bytes)")
                                except Exception as read_error:
                                    logger.error(f"Erro ao ler arquivo {filename}: {read_error}")
                                    continue
                            else:
                                logger.warning(f"AutoSave: Arquivo não encontrado no filesystem: {filepath}")
                                continue

                        # GARANTIR que a imagem tenha bytes válidos
                        if not image_bytes:
                            logger.error(f"AutoSave: Impossível salvar imagem sem bytes! filename={filename}")
                            continue

                        # Calcular hash da imagem
                        import hashlib
                        imagem_hash = hashlib.sha256(image_bytes).hexdigest()

                        nova_foto = FotoRelatorio(
                            relatorio_id=relatorio_id,
                            url=foto_info.get('url'),
                            filename=filename,
                            imagem=image_bytes,  # SALVAR BYTES NO BANCO
                            imagem_hash=imagem_hash,
                            imagem_size=len(image_bytes),
                            content_type=foto_info.get('content_type') or 'image/jpeg',
                            legenda=foto_info.get('legenda') or '',
                            titulo=foto_info.get('titulo') or '',
                            tipo_servico=foto_info.get('tipo_servico') or 'Geral',
                            local=foto_info.get('local') or '',
                            ordem=foto_info.get('ordem', 0)
                        )
                        db.session.add(nova_foto)
                        db.session.flush()  # Para obter o ID

                        imagens_resultado.append({
                            'id': nova_foto.id,
                            'url': nova_foto.url,
                            'legenda': nova_foto.legenda,
                            'ordem': nova_foto.ordem
                        })
                        logger.info(f"✅ AutoSave: Nova imagem SALVA NO BANCO - id={nova_foto.id} ({len(image_bytes)} bytes)")

                # Atualizar imagem existente
                else:
                    foto = FotoRelatorio.query.get(foto_info['id'])
                    if foto and foto.relatorio_id == relatorio_id:
                        # Atualizar metadados
                        if 'legenda' in foto_info:
                            foto.legenda = foto_info['legenda']
                        if 'titulo' in foto_info:
                            foto.titulo = foto_info['titulo']
                        if 'tipo_servico' in foto_info:
                            foto.tipo_servico = foto_info['tipo_servico']
                        if 'local' in foto_info:
                            foto.local = foto_info['local']
                        if 'ordem' in foto_info:
                            foto.ordem = foto_info['ordem']

                        imagens_resultado.append({
                            'id': foto.id,
                            'url': foto.url,
                            'legenda': foto.legenda,
                            'ordem': foto.ordem
                        })
                        logger.info(f"AutoSave: Metadados da imagem {foto.id} atualizados")

        # 4️⃣ COMMIT DA TRANSAÇÃO
        db.session.commit()
        print(f"✅ AutoSave registrado: {relatorio_id}")
        logger.info(f"✅ AutoSave: Commit realizado para relatório {relatorio_id}")

        # VALIDAÇÃO DETALHADA: Verificar quantas imagens foram realmente salvas no banco
        total_imagens_db = FotoRelatorio.query.filter_by(relatorio_id=relatorio_id).count()
        imagens_com_bytes = FotoRelatorio.query.filter(
            FotoRelatorio.relatorio_id == relatorio_id,
            FotoRelatorio.imagem.isnot(None)
        ).count()

        logger.info(f"📊 AutoSave VALIDAÇÃO FINAL:")
        logger.info(f"   - Total de imagens no banco: {total_imagens_db}")
        logger.info(f"   - Imagens COM bytes salvos: {imagens_com_bytes}")
        logger.info(f"   - Imagens SEM bytes: {total_imagens_db - imagens_com_bytes}")

        print(f"📊 Total de imagens no banco: {total_imagens_db}")
        print(f"📊 Imagens com bytes: {imagens_com_bytes}")

        if total_imagens_db != imagens_com_bytes:
            logger.error(f"⚠️ ATENÇÃO: {total_imagens_db - imagens_com_bytes} imagens foram salvas SEM bytes!")

        # Buscar estado final do relatório
        relatorio_final = Relatorio.query.get(relatorio_id)

        # Buscar todas as imagens salvas do relatório para retornar estado completo
        fotos_salvas = FotoRelatorio.query.filter_by(relatorio_id=relatorio_id).order_by(FotoRelatorio.ordem).all()

        imagens_response = []
        for foto in fotos_salvas:
            imagens_response.append({
                'id': foto.id,
                'temp_id': None,  # temp_id já foi convertido em id definitivo
                'url': foto.url or f"/uploads/{foto.filename}" if foto.filename else None,
                'filename': foto.filename,
                'legenda': foto.legenda or '',
                'titulo': foto.titulo or '',
                'tipo_servico': foto.tipo_servico or 'Geral',
                'local': foto.local or '',
                'ordem': foto.ordem or 0
            })

        logger.info(f"✅ AutoSave RESPOSTA: {len(imagens_response)} imagens retornadas")

        return jsonify({
            'success': True,
            'message': 'AutoSave executado com sucesso',
            'relatorio_id': relatorio_id,
            'relatorio': {
                'id': relatorio_final.id,
                'numero': relatorio_final.numero,
                'titulo': relatorio_final.titulo,
                'status': relatorio_final.status,
                'updated_at': relatorio_final.updated_at.isoformat() if relatorio_final.updated_at else None
            },
            'imagens': imagens_response  # Array sempre válido e completo
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        print(f"❌ Erro no autosave (integridade): {str(e)}")
        logger.error(f"Erro de integridade no AutoSave: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro de integridade no banco de dados',
            'details': str(e)
        }), 400

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro no autosave: {str(e)}")
        logger.error(f"Erro no AutoSave: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erro ao executar AutoSave',
            'details': str(e)
        }), 500

logger.info("✅ API de relatórios carregada com sucesso")