import os
import json
import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import Relatorio, FotoRelatorio, Projeto, Visita
from forms import ReportForm

# Configuração de upload - usando a configuração do app
UPLOAD_FOLDER = 'uploads'

@app.route('/reports/create', methods=['GET', 'POST'])
@login_required
def report_create():
    form = ReportForm()
    
    if request.method == 'POST':
        try:
            # Processar dados do relatório
            relatorio = Relatorio(
                titulo=request.form.get('titulo'),
                conteudo=request.form.get('conteudo'),
                projeto_id=request.form.get('projeto_id'),
                autor_id=current_user.id,
                data_relatorio=datetime.now(),
                status='Rascunho'
            )
            
            # Gerar número do relatório
            from utils import generate_report_number
            relatorio.numero = generate_report_number()
            
            db.session.add(relatorio)
            db.session.flush()  # Para obter o ID
            
            # Processar checklist
            checklist_data = request.form.get('checklist_data')
            if checklist_data:
                try:
                    checklist = json.loads(checklist_data)
                    relatorio.checklist_data = json.dumps(checklist)
                except:
                    pass
            
            # Processar fotos
            photo_count = 0
            for key in request.files:
                if key.startswith('photo_'):
                    file = request.files[key]
                    if file and file.filename:
                        # Salvar arquivo
                        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(filepath)
                        
                        # Obter metadados da foto
                        photo_index = key.split('_')[1]
                        caption = request.form.get(f'photo_{photo_index}_caption', '')
                        service_type = request.form.get(f'photo_{photo_index}_service_type', '')
                        
                        # Criar registro da foto
                        foto = FotoRelatorio(
                            relatorio_id=relatorio.id,
                            filename=filename,
                            legenda=caption or f'Foto {photo_count + 1}',
                            tipo_servico=service_type,
                            ordem=photo_count + 1
                        )
                        
                        db.session.add(foto)
                        photo_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Relatório criado com sucesso!',
                'redirect': url_for('reports_list')
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Erro ao criar relatório: {str(e)}'
            })
    
    # Use template simples enquanto criamos o complexo
    return render_template('reports/form.html', form=form)

@app.route('/reports')
@login_required
def reports_list():
    if current_user.is_master:
        reports = Relatorio.query.order_by(Relatorio.created_at.desc()).all()
    else:
        reports = Relatorio.query.filter_by(autor_id=current_user.id).order_by(Relatorio.created_at.desc()).all()
    
    return render_template('reports/list.html', reports=reports)

@app.route('/reports/<int:id>')
@login_required
def report_detail(id):
    relatorio = Relatorio.query.get_or_404(id)
    
    # Verificar permissões
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('reports_list'))
    
    return render_template('reports/detail.html', relatorio=relatorio)