"""
Rotas para Relatório Express
Funcionalidade independente com obra criada junto do relatório
Status: Em preenchimento → Aguardando Aprovação → Aprovado / Rejeitado
"""
import os
import json
import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import RelatorioExpress, FotoRelatorioExpress, User

logger = logging.getLogger(__name__)

def generate_express_number():
    """Gera o próximo número para Relatório Express"""
    last_report = RelatorioExpress.query.order_by(RelatorioExpress.id.desc()).first()
    if last_report:
        try:
            num = int(last_report.numero.replace('EXP-', ''))
            return f"EXP-{str(num + 1).zfill(4)}"
        except:
            pass
    return "EXP-0001"


@app.route('/relatorios-express')
@login_required
def express_reports_list():
    """Lista todos os Relatórios Express com filtros"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        status_filter = request.args.get('status', '')
        search_query = request.args.get('q', '')
        
        query = RelatorioExpress.query
        
        if status_filter:
            if status_filter == 'Em preenchimento':
                query = query.filter(RelatorioExpress.status == 'Em preenchimento')
            elif status_filter == 'Aguardando Aprovação':
                query = query.filter(RelatorioExpress.status == 'Aguardando Aprovação')
            elif status_filter == 'Aprovado':
                query = query.filter(RelatorioExpress.status == 'Aprovado')
            elif status_filter == 'Rejeitado':
                query = query.filter(RelatorioExpress.status == 'Rejeitado')
        
        if search_query:
            query = query.filter(
                db.or_(
                    RelatorioExpress.numero.ilike(f'%{search_query}%'),
                    RelatorioExpress.titulo.ilike(f'%{search_query}%'),
                    RelatorioExpress.obra_nome.ilike(f'%{search_query}%'),
                    RelatorioExpress.obra_construtora.ilike(f'%{search_query}%')
                )
            )
        
        relatorios = query.order_by(RelatorioExpress.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('reports/express_list.html',
            relatorios=relatorios,
            status_filter=status_filter,
            search_query=search_query
        )
    except Exception as e:
        logger.error(f"Erro ao listar Relatórios Express: {e}")
        flash('Erro ao carregar lista de relatórios.', 'error')
        return redirect(url_for('index'))


@app.route('/relatorio-express/novo')
@login_required
def new_express_report():
    """Formulário para criar novo Relatório Express"""
    try:
        next_numero = generate_express_number()
        today = datetime.now().strftime('%Y-%m-%d')
        
        report_data = {
            'id': None,
            'numero': next_numero,
            'titulo': 'Relatório Express de Visita',
            'status': 'preenchimento',
            'obra_nome': '',
            'obra_endereco': '',
            'obra_tipo': '',
            'obra_construtora': '',
            'obra_responsavel': '',
            'obra_email': '',
            'obra_telefone': '',
            'acompanhantes': [],
            'imagens': []
        }
        
        return render_template('reports/express_form.html',
            report_data=report_data,
            edit_mode=False,
            existing_report=None,
            next_numero=next_numero,
            today=today
        )
    except Exception as e:
        logger.error(f"Erro ao carregar formulário Express: {e}")
        flash('Erro ao carregar formulário.', 'error')
        return redirect(url_for('express_reports_list'))


@app.route('/relatorio-express/criar', methods=['POST'])
@login_required
def create_express_report():
    """Cria novo Relatório Express"""
    try:
        action = request.form.get('action', 'save_draft')
        
        obra_nome = request.form.get('obra_nome', '').strip()
        if not obra_nome:
            flash('O nome da obra é obrigatório.', 'error')
            return redirect(url_for('new_express_report'))
        
        numero = request.form.get('numero') or generate_express_number()
        
        existing = RelatorioExpress.query.filter_by(numero=numero).first()
        if existing:
            numero = generate_express_number()
        
        relatorio = RelatorioExpress(
            numero=numero,
            titulo=request.form.get('titulo', 'Relatório Express de Visita'),
            obra_nome=obra_nome,
            obra_endereco=request.form.get('obra_endereco', ''),
            obra_tipo=request.form.get('obra_tipo', ''),
            obra_construtora=request.form.get('obra_construtora', ''),
            obra_responsavel=request.form.get('obra_responsavel', ''),
            obra_email=request.form.get('obra_email', ''),
            obra_telefone=request.form.get('obra_telefone', ''),
            autor_id=current_user.id,
            criado_por=current_user.id,
            conteudo=request.form.get('conteudo', ''),
            observacoes_finais=request.form.get('lembrete_proxima_visita', ''),
            status='Em preenchimento'
        )
        
        data_relatorio = request.form.get('data_relatorio')
        if data_relatorio:
            try:
                relatorio.data_relatorio = datetime.strptime(data_relatorio, '%Y-%m-%d')
            except:
                relatorio.data_relatorio = datetime.now()
        
        acompanhantes_str = request.form.get('acompanhantes', '[]')
        try:
            relatorio.acompanhantes = json.loads(acompanhantes_str) if acompanhantes_str else []
        except:
            relatorio.acompanhantes = []
        
        checklist_data = []
        for key, value in request.form.items():
            if key.startswith('obs_'):
                item_name = key.replace('obs_', '')
                checked = request.form.get(item_name) == 'on'
                if value.strip() or checked:
                    checklist_data.append({
                        'item': item_name,
                        'checked': checked,
                        'observacao': value.strip()
                    })
        relatorio.checklist_data = json.dumps(checklist_data)
        
        if action == 'submit_approval':
            relatorio.status = 'Aguardando Aprovação'
        
        db.session.add(relatorio)
        db.session.commit()
        
        if action == 'submit_approval':
            flash(f'Relatório Express {numero} enviado para aprovação!', 'success')
        else:
            flash(f'Relatório Express {numero} salvo com sucesso!', 'success')
        
        return redirect(url_for('express_reports_list'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar Relatório Express: {e}")
        flash('Erro ao criar relatório. Tente novamente.', 'error')
        return redirect(url_for('new_express_report'))


@app.route('/relatorio-express/<int:report_id>/editar')
@login_required
def edit_express_report(report_id):
    """Edita um Relatório Express existente"""
    try:
        relatorio = RelatorioExpress.query.get_or_404(report_id)
        
        if relatorio.status == 'Aprovado' and not current_user.is_master:
            flash('Relatórios aprovados não podem ser editados.', 'warning')
            return redirect(url_for('view_express_report', report_id=report_id))
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        report_data = {
            'id': relatorio.id,
            'numero': relatorio.numero,
            'titulo': relatorio.titulo,
            'status': relatorio.status,
            'obra_nome': relatorio.obra_nome,
            'obra_endereco': relatorio.obra_endereco,
            'obra_tipo': relatorio.obra_tipo,
            'obra_construtora': relatorio.obra_construtora,
            'obra_responsavel': relatorio.obra_responsavel,
            'obra_email': relatorio.obra_email,
            'obra_telefone': relatorio.obra_telefone,
            'conteudo': relatorio.conteudo,
            'acompanhantes': relatorio.acompanhantes or [],
            'imagens': []
        }
        
        fotos = FotoRelatorioExpress.query.filter_by(
            relatorio_express_id=report_id
        ).order_by(FotoRelatorioExpress.ordem).all()
        
        for foto in fotos:
            report_data['imagens'].append({
                'id': foto.id,
                'url': foto.url,
                'legenda': foto.legenda,
                'ordem': foto.ordem
            })
        
        return render_template('reports/express_form.html',
            report_data=report_data,
            edit_mode=True,
            existing_report=relatorio,
            next_numero=relatorio.numero,
            today=today
        )
    except Exception as e:
        logger.error(f"Erro ao editar Relatório Express: {e}")
        flash('Erro ao carregar relatório para edição.', 'error')
        return redirect(url_for('express_reports_list'))


@app.route('/relatorio-express/<int:report_id>/atualizar', methods=['POST'])
@login_required
def update_express_report(report_id):
    """Atualiza um Relatório Express existente"""
    try:
        relatorio = RelatorioExpress.query.get_or_404(report_id)
        
        if relatorio.status == 'Aprovado' and not current_user.is_master:
            flash('Relatórios aprovados não podem ser editados.', 'warning')
            return redirect(url_for('view_express_report', report_id=report_id))
        
        action = request.form.get('action', 'save_draft')
        
        relatorio.titulo = request.form.get('titulo', relatorio.titulo)
        relatorio.obra_nome = request.form.get('obra_nome', relatorio.obra_nome)
        relatorio.obra_endereco = request.form.get('obra_endereco', '')
        relatorio.obra_tipo = request.form.get('obra_tipo', '')
        relatorio.obra_construtora = request.form.get('obra_construtora', '')
        relatorio.obra_responsavel = request.form.get('obra_responsavel', '')
        relatorio.obra_email = request.form.get('obra_email', '')
        relatorio.obra_telefone = request.form.get('obra_telefone', '')
        relatorio.conteudo = request.form.get('conteudo', '')
        relatorio.observacoes_finais = request.form.get('lembrete_proxima_visita', '')
        relatorio.atualizado_por = current_user.id
        
        acompanhantes_str = request.form.get('acompanhantes', '[]')
        try:
            relatorio.acompanhantes = json.loads(acompanhantes_str) if acompanhantes_str else []
        except:
            pass
        
        checklist_data = []
        for key, value in request.form.items():
            if key.startswith('obs_'):
                item_name = key.replace('obs_', '')
                checked = request.form.get(item_name) == 'on'
                if value.strip() or checked:
                    checklist_data.append({
                        'item': item_name,
                        'checked': checked,
                        'observacao': value.strip()
                    })
        relatorio.checklist_data = json.dumps(checklist_data)
        
        if action == 'submit_approval':
            relatorio.status = 'Aguardando Aprovação'
            flash(f'Relatório Express {relatorio.numero} enviado para aprovação!', 'success')
        else:
            flash(f'Relatório Express {relatorio.numero} atualizado!', 'success')
        
        db.session.commit()
        return redirect(url_for('express_reports_list'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar Relatório Express: {e}")
        flash('Erro ao atualizar relatório.', 'error')
        return redirect(url_for('edit_express_report', report_id=report_id))


@app.route('/relatorio-express/<int:report_id>')
@login_required
def view_express_report(report_id):
    """Visualiza um Relatório Express"""
    try:
        relatorio = RelatorioExpress.query.get_or_404(report_id)
        
        fotos = FotoRelatorioExpress.query.filter_by(
            relatorio_express_id=report_id
        ).order_by(FotoRelatorioExpress.ordem).all()
        
        return render_template('reports/express_view.html',
            relatorio=relatorio,
            fotos=fotos
        )
    except Exception as e:
        logger.error(f"Erro ao visualizar Relatório Express: {e}")
        flash('Erro ao carregar relatório.', 'error')
        return redirect(url_for('express_reports_list'))


@app.route('/relatorio-express/<int:report_id>/aprovar', methods=['POST'])
@login_required
def approve_express_report(report_id):
    """Aprova um Relatório Express"""
    try:
        relatorio = RelatorioExpress.query.get_or_404(report_id)
        
        if relatorio.status != 'Aguardando Aprovação':
            flash('Este relatório não está aguardando aprovação.', 'warning')
            return redirect(url_for('express_reports_list'))
        
        relatorio.status = 'Aprovado'
        relatorio.aprovador_id = current_user.id
        relatorio.data_aprovacao = datetime.now()
        
        db.session.commit()
        flash(f'Relatório Express {relatorio.numero} aprovado com sucesso!', 'success')
        return redirect(url_for('express_reports_list'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao aprovar Relatório Express: {e}")
        flash('Erro ao aprovar relatório.', 'error')
        return redirect(url_for('express_reports_list'))


@app.route('/relatorio-express/<int:report_id>/rejeitar', methods=['POST'])
@login_required
def reject_express_report(report_id):
    """Rejeita um Relatório Express"""
    try:
        relatorio = RelatorioExpress.query.get_or_404(report_id)
        
        if relatorio.status != 'Aguardando Aprovação':
            flash('Este relatório não está aguardando aprovação.', 'warning')
            return redirect(url_for('express_reports_list'))
        
        comentario = request.form.get('comentario_rejeicao', '')
        
        relatorio.status = 'Rejeitado'
        relatorio.aprovador_id = current_user.id
        relatorio.comentario_aprovacao = comentario
        
        db.session.commit()
        flash(f'Relatório Express {relatorio.numero} rejeitado.', 'info')
        return redirect(url_for('express_reports_list'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao rejeitar Relatório Express: {e}")
        flash('Erro ao rejeitar relatório.', 'error')
        return redirect(url_for('express_reports_list'))


@app.route('/relatorio-express/<int:report_id>/excluir', methods=['POST'])
@login_required
def delete_express_report(report_id):
    """Exclui um Relatório Express"""
    try:
        relatorio = RelatorioExpress.query.get_or_404(report_id)
        
        if relatorio.status == 'Aprovado' and not current_user.is_master:
            flash('Relatórios aprovados não podem ser excluídos.', 'warning')
            return redirect(url_for('express_reports_list'))
        
        FotoRelatorioExpress.query.filter_by(relatorio_express_id=report_id).delete()
        
        db.session.delete(relatorio)
        db.session.commit()
        
        flash(f'Relatório Express {relatorio.numero} excluído.', 'success')
        return redirect(url_for('express_reports_list'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir Relatório Express: {e}")
        flash('Erro ao excluir relatório.', 'error')
        return redirect(url_for('express_reports_list'))


@app.route('/api/relatorios-express/autosave', methods=['POST'])
@login_required
def autosave_express_report_api():
    """API completa para autosave do Relatório Express - cria ou atualiza"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Nenhum dado fornecido'}), 400
        
        relatorio_id = data.get('id')
        logger.info(f"📦 Express AutoSave - ID: {relatorio_id}, dados recebidos")
        
        if not relatorio_id:
            obra_nome = data.get('obra_nome', '').strip()
            if not obra_nome:
                return jsonify({'success': False, 'error': 'Nome da obra é obrigatório'}), 400
            
            numero = data.get('numero') or generate_express_number()
            existing = RelatorioExpress.query.filter_by(numero=numero).first()
            if existing:
                numero = generate_express_number()
            
            acompanhantes = data.get('acompanhantes', [])
            if isinstance(acompanhantes, str):
                try:
                    acompanhantes = json.loads(acompanhantes)
                except:
                    acompanhantes = []
            
            checklist_data = data.get('checklist_data')
            if checklist_data and not isinstance(checklist_data, str):
                checklist_data = json.dumps(checklist_data)
            
            relatorio = RelatorioExpress(
                numero=numero,
                titulo=data.get('titulo', 'Relatório Express de Visita'),
                obra_nome=obra_nome,
                obra_endereco=data.get('obra_endereco', ''),
                obra_tipo=data.get('obra_tipo', ''),
                obra_construtora=data.get('obra_construtora', ''),
                obra_responsavel=data.get('obra_responsavel', ''),
                obra_email=data.get('obra_email', ''),
                obra_telefone=data.get('obra_telefone', ''),
                autor_id=current_user.id,
                criado_por=current_user.id,
                conteudo=data.get('conteudo', ''),
                observacoes_finais=data.get('observacoes_finais', ''),
                checklist_data=checklist_data,
                acompanhantes=acompanhantes,
                status='Em preenchimento'
            )
            
            if data.get('data_relatorio'):
                try:
                    relatorio.data_relatorio = datetime.strptime(data['data_relatorio'], '%Y-%m-%d')
                except:
                    relatorio.data_relatorio = datetime.now()
            
            db.session.add(relatorio)
            db.session.flush()
            relatorio_id = relatorio.id
            logger.info(f"✅ Express AutoSave: Novo relatório criado com ID {relatorio_id}")
        else:
            relatorio = RelatorioExpress.query.get(relatorio_id)
            if not relatorio:
                return jsonify({'success': False, 'error': 'Relatório não encontrado'}), 404
            
            campos = ['titulo', 'obra_nome', 'obra_endereco', 'obra_tipo', 'obra_construtora',
                      'obra_responsavel', 'obra_email', 'obra_telefone', 'conteudo', 'observacoes_finais']
            for campo in campos:
                if campo in data:
                    setattr(relatorio, campo, data[campo])
            
            if 'acompanhantes' in data:
                acompanhantes = data['acompanhantes']
                if isinstance(acompanhantes, str):
                    try:
                        acompanhantes = json.loads(acompanhantes)
                    except:
                        acompanhantes = []
                relatorio.acompanhantes = acompanhantes
            
            if 'checklist_data' in data:
                checklist_data = data['checklist_data']
                if checklist_data and not isinstance(checklist_data, str):
                    checklist_data = json.dumps(checklist_data)
                relatorio.checklist_data = checklist_data
            
            relatorio.atualizado_por = current_user.id
            relatorio.updated_at = datetime.now()
            logger.info(f"✅ Express AutoSave: Relatório {relatorio_id} atualizado")
        
        imagens_resultado = []
        if 'fotos' in data and data['fotos']:
            TEMP_UPLOAD_FOLDER = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'temp')
            import glob as globlib
            import hashlib
            
            for foto_info in data['fotos']:
                if foto_info.get('deletar'):
                    foto_id = foto_info.get('id')
                    if foto_id:
                        foto = FotoRelatorioExpress.query.get(foto_id)
                        if foto and foto.relatorio_express_id == relatorio_id:
                            db.session.delete(foto)
                            logger.info(f"📸 Express AutoSave: Foto {foto_id} removida")
                    continue
                
                if not foto_info.get('id') and foto_info.get('temp_id'):
                    temp_id = foto_info['temp_id']
                    temp_pattern = os.path.join(TEMP_UPLOAD_FOLDER, f"{temp_id}.*")
                    matching_files = globlib.glob(temp_pattern)
                    
                    if matching_files:
                        temp_filepath = matching_files[0]
                        extension = temp_filepath.rsplit('.', 1)[1].lower() if '.' in temp_filepath else 'jpg'
                        
                        with open(temp_filepath, 'rb') as f:
                            imagem_data = f.read()
                        
                        imagem_hash = hashlib.sha256(imagem_data).hexdigest()
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
                        filename = f"express_{relatorio_id}_{timestamp}.{extension}"
                        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
                        filepath = os.path.join(upload_folder, filename)
                        
                        import shutil
                        shutil.copy(temp_filepath, filepath)
                        
                        max_ordem = db.session.query(db.func.max(FotoRelatorioExpress.ordem)).filter_by(
                            relatorio_express_id=relatorio_id
                        ).scalar() or 0
                        
                        nova_foto = FotoRelatorioExpress(
                            relatorio_express_id=relatorio_id,
                            filename=filename,
                            url=f"/uploads/{filename}",
                            legenda=foto_info.get('caption', ''),
                            local=foto_info.get('local', ''),
                            ordem=max_ordem + 1,
                            imagem=imagem_data,
                            imagem_hash=imagem_hash,
                            content_type=f"image/{extension}",
                            imagem_size=len(imagem_data)
                        )
                        db.session.add(nova_foto)
                        db.session.flush()
                        
                        imagens_resultado.append({
                            'id': nova_foto.id,
                            'temp_id': temp_id,
                            'url': nova_foto.url,
                            'legenda': nova_foto.legenda
                        })
                        
                        try:
                            os.remove(temp_filepath)
                        except:
                            pass
                        
                        logger.info(f"📸 Express AutoSave: Nova foto salva ID {nova_foto.id}")
                
                elif foto_info.get('id'):
                    foto_id = foto_info['id']
                    foto = FotoRelatorioExpress.query.get(foto_id)
                    if foto and foto.relatorio_express_id == relatorio_id:
                        if 'caption' in foto_info:
                            foto.legenda = foto_info['caption']
                        if 'local' in foto_info:
                            foto.local = foto_info['local']
                        if 'ordem' in foto_info:
                            foto.ordem = foto_info['ordem']
                        
                        imagens_resultado.append({
                            'id': foto.id,
                            'url': foto.url,
                            'legenda': foto.legenda
                        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Salvo automaticamente',
            'relatorio_id': relatorio_id,
            'imagens': imagens_resultado,
            'saved_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro no Express AutoSave: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/relatorios-express/<int:report_id>/submit-approval', methods=['POST'])
@login_required
def submit_express_for_approval(report_id):
    """Envia Relatório Express para aprovação via API"""
    try:
        relatorio = RelatorioExpress.query.get_or_404(report_id)
        
        if relatorio.status == 'Aprovado':
            return jsonify({'success': False, 'error': 'Relatório já está aprovado'}), 400
        
        relatorio.status = 'Aguardando Aprovação'
        relatorio.atualizado_por = current_user.id
        relatorio.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Relatório {relatorio.numero} enviado para aprovação',
            'status': relatorio.status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao enviar Express para aprovação: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


logger.info("✅ Rotas de Relatório Express carregadas com sucesso")
