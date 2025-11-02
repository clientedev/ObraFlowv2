"""
API REST para gerenciamento de relatórios com salvamento automático
Implementação conforme especificação técnica profissional
"""
import os
import logging
import uuid
import shutil
from datetime import datetime
from flask import jsonify, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app import app, db
from models import Relatorio, FotoRelatorio, Projeto, User
import traceback # Import traceback for detailed error logging

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
@login_required
def api_upload_temp():
    """
    POST /api/uploads/temp

    Upload rápido de imagem para storage temporário.
    Retorna temp_id para posterior associação ao relatório via autosave.

    Conforme especificação técnica do AutoSave.

    Returns:
        JSON: {temp_id, path, filename, size, mime_type}
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
                'mime_type': file.content_type or 'image/jpeg'
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
            checklist_data=data.get('checklist_data')
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
def api_buscar_relatorio(relatorio_id):
    """
    GET /api/relatorios/<id>

    Retorna todos os campos do relatório e as imagens associadas em formato estruturado.
    """
    try:
        relatorio = Relatorio.query.get(relatorio_id)

        if not relatorio:
            return jsonify({
                'success': False,
                'error': 'Relatório não encontrado'
            }), 404

        # Buscar imagens associadas
        imagens = FotoRelatorio.query.filter_by(
            relatorio_id=relatorio_id
        ).order_by(FotoRelatorio.ordem).all()

        imagens_data = [{
            'id': img.id,
            'url': img.url or f"/uploads/{img.filename}" if img.filename else None,
            'legenda': img.legenda,
            'ordem': img.ordem,
            'titulo': img.titulo,
            'tipo_servico': img.tipo_servico,
            'local': img.local,
            'created_at': img.created_at.isoformat() if img.created_at else None
        } for img in imagens]

        return jsonify({
            'success': True,
            'relatorio': {
                'id': relatorio.id,
                'numero': relatorio.numero,
                'numero_projeto': relatorio.numero_projeto,
                'titulo': relatorio.titulo,
                'descricao': relatorio.descricao,
                'projeto_id': relatorio.projeto_id,
                'visita_id': relatorio.visita_id,
                'autor_id': relatorio.autor_id,
                'aprovador_id': relatorio.aprovador_id,

                # Novos campos
                'categoria': relatorio.categoria,
                'local': relatorio.local,
                'lembrete_proxima_visita': relatorio.lembrete_proxima_visita.isoformat() if relatorio.lembrete_proxima_visita else None,
                'observacoes_finais': relatorio.observacoes_finais,

                # Status e datas
                'status': relatorio.status,
                'data_relatorio': relatorio.data_relatorio.isoformat() if relatorio.data_relatorio else None,
                'data_aprovacao': relatorio.data_aprovacao.isoformat() if relatorio.data_aprovacao else None,
                'created_at': relatorio.created_at.isoformat() if relatorio.created_at else None,
                'updated_at': relatorio.updated_at.isoformat() if relatorio.updated_at else None,

                # Outros campos
                'conteudo': relatorio.conteudo,
                'checklist_data': relatorio.checklist_data,
                'comentario_aprovacao': relatorio.comentario_aprovacao,
                'acompanhantes': relatorio.acompanhantes,

                # Imagens
                'imagens': imagens_data
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar relatório {relatorio_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar relatório',
            'details': str(e)
        }), 500

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

    AutoSave completo do relatório - Implementação conforme especificação técnica.

    Funcionalidades:
    - Cria relatório automaticamente se não existir (sem projeto_id obrigatório no primeiro save)
    - Atualiza todos os campos do relatório existente
    - Sincroniza imagens: adiciona, atualiza metadados e remove
    - Atualiza campo updated_at automaticamente
    - Resiliente a falhas de conexão

    Payload esperado (JSON):
    {
        "id": null ou int,  # null para criar novo, int para atualizar
        "projeto_id": int,  # Obrigatório para criação
        "titulo": str,
        "numero": str,
        "categoria": str,
        "local": str,
        "observacoes_finais": str,
        "lembrete_proxima_visita": str (ISO datetime),
        "conteudo": str,
        "status": str,
        "checklist_data": dict/list,
        "acompanhantes": list,
        "fotos": [
            {
                "id": null ou int,  # null=nova, int=existente
                "deletar": bool,    # true para marcar para exclusão
                "url": str,
                "filename": str,
                "legenda": str,
                "categoria": str,
                "local": str,
                "titulo": str,
                "tipo_servico": str,
                "ordem": int
            }
        ]
    }
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

            # Processar checklist_data
            checklist_data = data.get('checklist_data')
            if checklist_data and not isinstance(checklist_data, str):
                import json
                checklist_data = json.dumps(checklist_data)

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

                # Outros campos
                conteudo=data.get('conteudo'),
                checklist_data=checklist_data,
                acompanhantes=data.get('acompanhantes')
            )

            db.session.add(novo_relatorio)
            db.session.flush()  # Obter ID sem commit completo
            relatorio_id = novo_relatorio.id

            print(f"✅ AutoSave: Novo relatório criado com ID {relatorio_id}")
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

            # Atualizar checklist_data
            if 'checklist_data' in data:
                checklist_data = data['checklist_data']
                if checklist_data and not isinstance(checklist_data, str):
                    import json
                    checklist_data = json.dumps(checklist_data)
                relatorio.checklist_data = checklist_data

            # Atualizar acompanhantes
            if 'acompanhantes' in data:
                relatorio.acompanhantes = data['acompanhantes']

            # Atualizar metadados de auditoria
            relatorio.atualizado_por = current_user.id
            relatorio.updated_at = datetime.utcnow()

            print(f"✅ AutoSave: Relatório {relatorio_id} atualizado")
            logger.info(f"✅ AutoSave: Relatório {relatorio_id} atualizado")

        # 3️⃣ SINCRONIZAR IMAGENS
        imagens_resultado = []

        if 'fotos' in data and data['fotos']:
            fotos_data = data['fotos']

            for foto_info in fotos_data:
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
                        temp_filename = f"{temp_id}.{foto_info.get('extension', 'jpg')}"
                        temp_filepath = os.path.join(TEMP_UPLOAD_FOLDER, temp_filename)

                        # Verificar se arquivo temporário existe
                        if not os.path.exists(temp_filepath):
                            logger.error(f"AutoSave: Arquivo temporário não encontrado: {temp_filepath}")
                            continue

                        # Gerar nome definitivo
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
                        extension = foto_info.get('extension', 'jpg')
                        final_filename = f"relatorio_{relatorio_id}_{timestamp}_{temp_id}.{extension}"
                        final_filepath = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)

                        # Mover arquivo de temp para pasta definitiva
                        try:
                            shutil.move(temp_filepath, final_filepath)
                            logger.info(f"AutoSave: Arquivo movido de temp para definitivo: {final_filename}")
                        except Exception as move_error:
                            logger.error(f"Erro ao mover arquivo temporário: {move_error}")
                            continue

                        # Criar registro no banco
                        nova_foto = FotoRelatorio(
                            relatorio_id=relatorio_id,
                            url=f"/uploads/{final_filename}",
                            filename=final_filename,
                            legenda=foto_info.get('legenda'),
                            titulo=foto_info.get('titulo'),
                            tipo_servico=foto_info.get('tipo_servico'),
                            local=foto_info.get('local'),
                            ordem=foto_info.get('ordem', 0)
                        )
                        db.session.add(nova_foto)
                        db.session.flush()  # Para obter o ID

                        imagens_resultado.append({
                            'id': nova_foto.id,
                            'url': nova_foto.url,
                            'filename': nova_foto.filename,
                            'legenda': nova_foto.legenda,
                            'ordem': nova_foto.ordem,
                            'temp_id': temp_id  # Retornar para frontend mapear
                        })
                        logger.info(f"AutoSave: Imagem temp_id={temp_id} persistida com id={nova_foto.id}")

                    # Imagens já salvas no filesystem - apenas criar registro
                    elif foto_info.get('url') or foto_info.get('filename'):
                        nova_foto = FotoRelatorio(
                            relatorio_id=relatorio_id,
                            url=foto_info.get('url'),
                            filename=foto_info.get('filename'),
                            legenda=foto_info.get('legenda'),
                            titulo=foto_info.get('titulo'),
                            tipo_servico=foto_info.get('tipo_servico'),
                            local=foto_info.get('local'),
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
                        logger.info(f"AutoSave: Nova imagem adicionada ao relatório {relatorio_id}")

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

        # Buscar estado final do relatório
        relatorio_final = Relatorio.query.get(relatorio_id)

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
            'imagens': imagens_resultado
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