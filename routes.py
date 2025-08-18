import os
import uuid
from datetime import datetime, date
from urllib.parse import urlparse
from flask import render_template, redirect, url_for, flash, request, current_app, send_from_directory, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Message

from app import app, db, mail
from models import User, Projeto, Contato, ContatoProjeto, Visita, Relatorio, FotoRelatorio, Reembolso, EnvioRelatorio
from forms import LoginForm, RegisterForm, UserForm, ProjetoForm, VisitaForm
from utils import generate_project_number, generate_report_number, generate_visit_number, send_report_email, calculate_reimbursement_total
from pdf_generator import generate_visit_report_pdf

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.ativo and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem cadastrar novos usuários.', 'error')
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Nome de usuário já existe.', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado.', 'error')
            return render_template('auth/register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            nome_completo=form.nome_completo.data,
            cargo=form.cargo.data,
            telefone=form.telefone.data,
            password_hash=generate_password_hash(form.password.data),
            is_master=form.is_master.data
        )
        
        db.session.add(user)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('users_list'))
    
    return render_template('auth/register.html', form=form)

# Main routes
@app.route('/')
@login_required
def index():
    # Dashboard statistics
    total_projetos = Projeto.query.count()
    projetos_ativos = Projeto.query.filter_by(status='Ativo').count()
    visitas_pendentes = Visita.query.filter_by(status='Agendada').count()
    relatorios_rascunho = Relatorio.query.filter_by(status='Rascunho').count()
    
    # Recent activities
    recent_visitas = Visita.query.order_by(Visita.created_at.desc()).limit(5).all()
    recent_relatorios = Relatorio.query.order_by(Relatorio.created_at.desc()).limit(5).all()
    
    return render_template('index.html',
                         total_projetos=total_projetos,
                         projetos_ativos=projetos_ativos,
                         visitas_pendentes=visitas_pendentes,
                         relatorios_rascunho=relatorios_rascunho,
                         recent_visitas=recent_visitas,
                         recent_relatorios=recent_relatorios)

# User management routes
@app.route('/users')
@login_required
def users_list():
    if not current_user.is_master:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('users/list.html', users=users)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    if not current_user.is_master:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        # Check for username conflicts
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user and existing_user.id != user.id:
            flash('Nome de usuário já existe.', 'error')
            return render_template('users/form.html', form=form, user=user)
        
        # Check for email conflicts
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email and existing_email.id != user.id:
            flash('Email já cadastrado.', 'error')
            return render_template('users/form.html', form=form, user=user)
        
        user.username = form.username.data
        user.email = form.email.data
        user.nome_completo = form.nome_completo.data
        user.cargo = form.cargo.data
        user.telefone = form.telefone.data
        user.is_master = form.is_master.data
        user.ativo = form.ativo.data
        
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('users_list'))
    
    return render_template('users/form.html', form=form, user=user)

# Project management routes
@app.route('/projects')
@login_required
def projects_list():
    projects = Projeto.query.all()
    return render_template('projects/list.html', projects=projects)

# Reports routes
@app.route('/reports')
@login_required
def reports():
    page = request.args.get('page', 1, type=int)
    relatorios = Relatorio.query.order_by(Relatorio.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('reports/list.html', relatorios=relatorios)

@app.route('/reports/new', methods=['GET', 'POST'])
@login_required
def create_report():
    from forms import RelatorioForm
    form = RelatorioForm()
    
    if form.validate_on_submit():
        try:
            # Create report
            relatorio = Relatorio(
                numero=generate_report_number(),
                titulo=form.titulo.data,
                projeto_id=form.projeto_id.data,
                visita_id=form.visita_id.data if form.visita_id.data else None,
                conteudo=form.conteudo.data,
                aprovador_nome=form.aprovador_nome.data,
                data_relatorio=form.data_relatorio.data,
                autor_id=current_user.id,
                status='Rascunho'
            )
            
            db.session.add(relatorio)
            db.session.flush()  # Get the ID
            
            # Handle photo uploads if any
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            photo_count = 0
            for key in request.files:
                if key.startswith('photo_'):
                    file = request.files[key]
                    if file and file.filename:
                        # Secure filename
                        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                        filepath = os.path.join(upload_folder, filename)
                        file.save(filepath)
                        
                        # Get photo metadata from form
                        photo_caption = request.form.get(f'photo_caption_{key}', f'Foto {photo_count + 1}')
                        photo_category = request.form.get(f'photo_category_{key}', 'Geral')
                        
                        # Create photo record
                        foto = FotoRelatorio(
                            relatorio_id=relatorio.id,
                            filename=filename,
                            legenda=photo_caption,
                            tipo_servico=photo_category,
                            ordem=photo_count + 1
                        )
                        
                        db.session.add(foto)
                        photo_count += 1
            
            db.session.commit()
            
            flash(f'Relatório {relatorio.numero} criado com sucesso!', 'success')
            return redirect(url_for('report_view', report_id=relatorio.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar relatório: {str(e)}', 'error')
    
    return render_template('reports/form.html', form=form)

@app.route('/reports/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(id):
    relatorio = Relatorio.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        flash('Acesso negado. Você só pode editar seus próprios relatórios.', 'error')
        return redirect(url_for('reports'))
    
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            
            if action == 'update':
                relatorio.titulo = request.form.get('titulo', '').strip()
                relatorio.conteudo = request.form.get('conteudo', '').strip()
                relatorio.projeto_id = request.form.get('projeto_id', type=int)
                relatorio.visita_id = request.form.get('visita_id', type=int) if request.form.get('visita_id') else None
                
                db.session.commit()
                flash('Relatório atualizado com sucesso!', 'success')
                
            elif action == 'submit_approval':
                if relatorio.status == 'Rascunho':
                    relatorio.status = 'Aguardando Aprovacao'
                    db.session.commit()
                    flash('Relatório enviado para aprovação!', 'success')
                else:
                    flash('Relatório já foi enviado para aprovação.', 'warning')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar relatório: {str(e)}', 'error')
    
    # Get projects and visits for form
    projetos = Projeto.query.filter_by(status='Ativo').all()
    visitas = Visita.query.filter_by(status='Realizada').all()
    fotos = FotoRelatorio.query.filter_by(relatorio_id=relatorio.id).order_by(FotoRelatorio.ordem).all()
    
    return render_template('reports/edit.html', relatorio=relatorio, projetos=projetos, 
                         visitas=visitas, fotos=fotos)

# Photo annotation system routes
@app.route('/photo-annotation')
@login_required
def photo_annotation():
    photo_path = request.args.get('photo')
    report_id = request.args.get('report_id')
    photo_id = request.args.get('photo_id')
    
    if not photo_path:
        flash('Foto não especificada.', 'error')
        return redirect(url_for('reports'))
    
    return render_template('reports/photo_annotation.html')

@app.route('/photo-editor')
@login_required
def photo_editor():
    """Página do editor de fotos"""
    return render_template('reports/photo_editor.html')

@app.route('/api/save-annotated-photo', methods=['POST'])
@login_required  
def save_annotated_photo():
    """API para salvar foto anotada"""
    try:
        image_data = request.form.get('annotated_image_data')
        caption = request.form.get('caption', '')
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        annotations_data = request.form.get('annotations_data', '{}')
        
        # Para retornar via postMessage para a janela pai
        return f"""
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'photo-edited',
                    photoId: new URLSearchParams(window.location.search).get('photoId'),
                    imageData: '{image_data}',
                    caption: '{caption}',
                    category: '{category}',
                    description: '{description}',
                    annotations: {annotations_data}
                }}, '*');
                window.close();
            }} else {{
                alert('Foto salva com sucesso!');
                window.history.back();
            }}
        </script>
        """
        
    except Exception as e:
        return f"""
        <script>
            alert('Erro ao salvar foto: {str(e)}');
            window.history.back();
        </script>
        """

@app.route('/reports/<int:id>/photos/upload', methods=['POST'])
@login_required
def upload_report_photos(id):
    relatorio = Relatorio.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    
    try:
        files = request.files.getlist('photos')
        uploaded_count = 0
        
        for file in files:
            if file.filename and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Generate unique filename
                filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Save file
                file.save(filepath)
                
                # Create photo record
                foto = FotoRelatorio(
                    relatorio_id=relatorio.id,
                    filename=filename,
                    legenda=f'Foto {len(relatorio.fotos) + uploaded_count + 1}',
                    ordem=len(relatorio.fotos) + uploaded_count + 1
                )
                
                db.session.add(foto)
                uploaded_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{uploaded_count} foto(s) enviada(s) com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/reports/<int:id>/generate-pdf')
@login_required
def generate_report_pdf(id):
    relatorio = Relatorio.query.get_or_404(id)
    
    try:
        from pdf_generator import ReportPDFGenerator
        
        # Generate PDF
        pdf_generator = ReportPDFGenerator()
        output_path = os.path.join('static', 'reports', f'relatorio_{relatorio.numero}.pdf')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        pdf_path = pdf_generator.generate_visit_report_pdf(relatorio, output_path)
        
        return send_from_directory(
            os.path.dirname(output_path),
            os.path.basename(output_path),
            as_attachment=True,
            download_name=f'relatorio_{relatorio.numero}.pdf'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('edit_report', id=id))

@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def project_new():
    form = ProjetoForm()
    
    if form.validate_on_submit():
        projeto = Projeto()
        projeto.numero = generate_project_number()
        projeto.nome = form.nome.data
        projeto.descricao = form.descricao.data
        projeto.endereco = form.endereco.data
        projeto.latitude = float(form.latitude.data) if form.latitude.data else None
        projeto.longitude = float(form.longitude.data) if form.longitude.data else None
        projeto.tipo_obra = form.tipo_obra.data
        projeto.responsavel_id = form.responsavel_id.data
        projeto.data_inicio = form.data_inicio.data
        projeto.data_previsao_fim = form.data_previsao_fim.data
        projeto.status = form.status.data
        
        db.session.add(projeto)
        db.session.commit()
        flash('Projeto cadastrado com sucesso!', 'success')
        return redirect(url_for('projects_list'))
    
    return render_template('projects/form.html', form=form)

@app.route('/projects/<int:project_id>')
@login_required
def project_view(project_id):
    project = Projeto.query.get_or_404(project_id)
    contatos = ContatoProjeto.query.filter_by(projeto_id=project_id).all()
    visitas = Visita.query.filter_by(projeto_id=project_id).order_by(Visita.data_agendada.desc()).all()
    relatorios = Relatorio.query.filter_by(projeto_id=project_id).order_by(Relatorio.created_at.desc()).all()
    
    return render_template('projects/view.html', 
                         project=project, 
                         contatos=contatos, 
                         visitas=visitas, 
                         relatorios=relatorios)

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    project = Projeto.query.get_or_404(project_id)
    form = ProjetoForm(obj=project)
    
    if form.validate_on_submit():
        project.nome = form.nome.data
        project.descricao = form.descricao.data
        project.endereco = form.endereco.data
        project.latitude = float(form.latitude.data) if form.latitude.data else None
        project.longitude = float(form.longitude.data) if form.longitude.data else None
        project.tipo_obra = form.tipo_obra.data
        project.responsavel_id = form.responsavel_id.data
        project.data_inicio = form.data_inicio.data
        project.data_previsao_fim = form.data_previsao_fim.data
        project.status = form.status.data
        
        db.session.commit()
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('project_view', project_id=project.id))
    
    return render_template('projects/form.html', form=form, project=project)

# Contact management routes
@app.route('/contacts')
@login_required
def contacts_list():
    contacts = Contato.query.all()
    return render_template('contacts/list.html', contacts=contacts)

@app.route('/contacts/new', methods=['GET', 'POST'])
@login_required
def contact_new():
    form = ContatoForm()
    
    if form.validate_on_submit():
        contato = Contato(
            nome=form.nome.data,
            email=form.email.data,
            telefone=form.telefone.data,
            empresa=form.empresa.data,
            cargo=form.cargo.data,
            observacoes=form.observacoes.data
        )
        
        db.session.add(contato)
        db.session.commit()
        flash('Contato cadastrado com sucesso!', 'success')
        return redirect(url_for('contacts_list'))
    
    return render_template('contacts/form.html', form=form)

@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def contact_edit(contact_id):
    contact = Contato.query.get_or_404(contact_id)
    form = ContatoForm(obj=contact)
    
    if form.validate_on_submit():
        contact.nome = form.nome.data
        contact.email = form.email.data
        contact.telefone = form.telefone.data
        contact.empresa = form.empresa.data
        contact.cargo = form.cargo.data
        contact.observacoes = form.observacoes.data
        
        db.session.commit()
        flash('Contato atualizado com sucesso!', 'success')
        return redirect(url_for('contacts_list'))
    
    return render_template('contacts/form.html', form=form, contact=contact)

@app.route('/projects/<int:project_id>/contacts/add', methods=['GET', 'POST'])
@login_required
def project_add_contact(project_id):
    project = Projeto.query.get_or_404(project_id)
    form = ContatoProjetoForm()
    
    if form.validate_on_submit():
        # Check if contact is already linked to this project
        existing = ContatoProjeto.query.filter_by(
            projeto_id=project_id,
            contato_id=form.contato_id.data
        ).first()
        
        if existing:
            flash('Este contato já está vinculado ao projeto.', 'error')
            return render_template('contacts/form.html', form=form, project=project)
        
        contato_projeto = ContatoProjeto(
            projeto_id=project_id,
            contato_id=form.contato_id.data,
            tipo_relacionamento=form.tipo_relacionamento.data,
            is_aprovador=form.is_aprovador.data,
            receber_relatorios=form.receber_relatorios.data
        )
        
        db.session.add(contato_projeto)
        db.session.commit()
        flash('Contato vinculado ao projeto com sucesso!', 'success')
        return redirect(url_for('project_view', project_id=project_id))
    
    return render_template('contacts/form.html', form=form, project=project)

# Visit management routes
@app.route('/visits')
@login_required
def visits_list():
    visits = Visita.query.order_by(Visita.data_agendada.desc()).all()
    return render_template('visits/list.html', visits=visits)

@app.route('/visits/new', methods=['GET', 'POST'])
@login_required
def visit_new():
    form = VisitaForm()
    
    if form.validate_on_submit():
        visita = Visita(
            numero=generate_visit_number(),
            projeto_id=form.projeto_id.data,
            responsavel_id=current_user.id,
            data_agendada=form.data_agendada.data,
            objetivo=form.objetivo.data
        )
        
        db.session.add(visita)
        db.session.flush()  # Get the ID
        
        # Add default checklist items from templates
        templates = ChecklistTemplate.query.filter_by(ativo=True).order_by(ChecklistTemplate.ordem).all()
        for template in templates:
            checklist_item = ChecklistItem(
                visita_id=visita.id,
                template_id=template.id,
                pergunta=template.descricao,
                obrigatorio=template.obrigatorio,
                ordem=template.ordem
            )
            db.session.add(checklist_item)
        
        db.session.commit()
        flash('Visita agendada com sucesso!', 'success')
        return redirect(url_for('visits_list'))
    
    return render_template('visits/form.html', form=form)

@app.route('/visits/<int:visit_id>/realize', methods=['GET', 'POST'])
@login_required
def visit_realize(visit_id):
    visit = Visita.query.get_or_404(visit_id)
    
    if visit.status == 'Realizada':
        flash('Esta visita já foi realizada.', 'info')
        return redirect(url_for('visit_checklist', visit_id=visit_id))
    
    form = VisitaRealizadaForm()
    
    if form.validate_on_submit():
        visit.data_realizada = datetime.utcnow()
        visit.status = 'Realizada'
        visit.atividades_realizadas = form.atividades_realizadas.data
        visit.observacoes = form.observacoes.data
        
        if form.latitude.data and form.longitude.data:
            visit.latitude = float(form.latitude.data)
            visit.longitude = float(form.longitude.data)
            visit.endereco_gps = form.endereco_gps.data
        
        db.session.commit()
        flash('Visita registrada com sucesso!', 'success')
        return redirect(url_for('visit_checklist', visit_id=visit_id))
    
    return render_template('visits/form.html', form=form, visit=visit, action='realize')

@app.route('/visits/<int:visit_id>/checklist', methods=['GET', 'POST'])
@login_required
def visit_checklist(visit_id):
    visit = Visita.query.get_or_404(visit_id)
    checklist_items = ChecklistItem.query.filter_by(visita_id=visit_id).order_by(ChecklistItem.ordem).all()
    
    if request.method == 'POST':
        for item in checklist_items:
            resposta = request.form.get(f'resposta_{item.id}')
            concluido = f'concluido_{item.id}' in request.form
            
            item.resposta = resposta
            item.concluido = concluido
        
        db.session.commit()
        flash('Checklist atualizado com sucesso!', 'success')
        
        # Check if all mandatory items are completed
        mandatory_incomplete = ChecklistItem.query.filter_by(
            visita_id=visit_id,
            obrigatorio=True,
            concluido=False
        ).count()
        
        if mandatory_incomplete > 0:
            flash(f'Atenção: {mandatory_incomplete} itens obrigatórios ainda não foram concluídos.', 'warning')
    
    return render_template('visits/checklist.html', visit=visit, checklist_items=checklist_items)

# Report management routes - movido para routes_reports.py

# Rota removida - usando nova implementação em routes_reports.py

@app.route('/reports/<int:report_id>')
@login_required
def report_view(report_id):
    report = Relatorio.query.get_or_404(report_id)
    fotos = FotoRelatorio.query.filter_by(relatorio_id=report_id).order_by(FotoRelatorio.ordem).all()
    return render_template('reports/view.html', report=report, fotos=fotos)

@app.route('/reports/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
def report_edit(report_id):
    report = Relatorio.query.get_or_404(report_id)
    
    # Check permissions
    if report.status == 'Finalizado' and not current_user.is_master:
        flash('Apenas usuários master podem editar relatórios finalizados.', 'error')
        return redirect(url_for('report_view', report_id=report_id))
    
    form = RelatorioForm(obj=report)
    
    if form.validate_on_submit():
        report.titulo = form.titulo.data
        report.conteudo = form.conteudo.data
        report.aprovador_nome = form.aprovador_nome.data
        report.data_relatorio = form.data_relatorio.data
        
        db.session.commit()
        flash('Relatório atualizado com sucesso!', 'success')
        return redirect(url_for('report_view', report_id=report_id))
    
    return render_template('reports/form.html', form=form, report=report)

@app.route('/reports/<int:report_id>/photos/add', methods=['GET', 'POST'])
@login_required
def report_add_photo(report_id):
    report = Relatorio.query.get_or_404(report_id)
    form = FotoRelatorioForm()
    
    if form.validate_on_submit():
        foto = form.foto.data
        if foto:
            filename = secure_filename(foto.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            foto.save(foto_path)
            
            foto_relatorio = FotoRelatorio(
                relatorio_id=report_id,
                filename=unique_filename,
                titulo=form.titulo.data,
                descricao=form.descricao.data,
                tipo_servico=form.tipo_servico.data,
                ordem=FotoRelatorio.query.filter_by(relatorio_id=report_id).count() + 1
            )
            
            db.session.add(foto_relatorio)
            db.session.commit()
            flash('Foto adicionada com sucesso!', 'success')
            return redirect(url_for('report_view', report_id=report_id))
    
    return render_template('reports/form.html', form=form, report=report, action='add_photo')

@app.route('/reports/<int:report_id>/finalize', methods=['POST'])
@login_required
def report_finalize(report_id):
    report = Relatorio.query.get_or_404(report_id)
    
    if report.status == 'Finalizado':
        flash('Relatório já está finalizado.', 'info')
        return redirect(url_for('report_view', report_id=report_id))
    
    report.status = 'Finalizado'
    db.session.commit()
    
    flash('Relatório finalizado com sucesso!', 'success')
    return redirect(url_for('report_view', report_id=report_id))

@app.route('/reports/<int:report_id>/send', methods=['POST'])
@login_required
def report_send(report_id):
    report = Relatorio.query.get_or_404(report_id)
    
    if report.status != 'Finalizado':
        flash('Apenas relatórios finalizados podem ser enviados.', 'error')
        return redirect(url_for('report_view', report_id=report_id))
    
    # Get project contacts who should receive reports
    contatos_projeto = ContatoProjeto.query.filter_by(
        projeto_id=report.projeto_id,
        receber_relatorios=True
    ).all()
    
    if not contatos_projeto:
        flash('Nenhum contato configurado para receber relatórios neste projeto.', 'error')
        return redirect(url_for('report_view', report_id=report_id))
    
    emails_enviados = 0
    for contato_projeto in contatos_projeto:
        if contato_projeto.contato.email:
            try:
                send_report_email(report, contato_projeto.contato.email, contato_projeto.contato.nome)
                
                # Log the email sending
                envio = EnvioRelatorio(
                    relatorio_id=report_id,
                    email_destinatario=contato_projeto.contato.email,
                    nome_destinatario=contato_projeto.contato.nome
                )
                db.session.add(envio)
                emails_enviados += 1
            except Exception as e:
                flash(f'Erro ao enviar email para {contato_projeto.contato.email}: {str(e)}', 'error')
    
    if emails_enviados > 0:
        report.status = 'Enviado'
        report.data_envio = datetime.utcnow()
        db.session.commit()
        flash(f'Relatório enviado para {emails_enviados} destinatário(s)!', 'success')
    else:
        flash('Nenhum email foi enviado com sucesso.', 'error')
    
    return redirect(url_for('report_view', report_id=report_id))

# Reimbursement routes
@app.route('/reimbursements')
@login_required
def reimbursements_list():
    reembolsos = Reembolso.query.filter_by(usuario_id=current_user.id).order_by(Reembolso.created_at.desc()).all()
    return render_template('reimbursement/list.html', reembolsos=reembolsos)

@app.route('/reimbursements/new', methods=['GET', 'POST'])
@login_required
def reimbursement_new():
    form = ReembolsoForm()
    
    if form.validate_on_submit():
        reembolso = Reembolso(
            usuario_id=current_user.id,
            projeto_id=form.projeto_id.data or None,
            periodo_inicio=form.periodo_inicio.data,
            periodo_fim=form.periodo_fim.data,
            quilometragem=form.quilometragem.data or 0,
            valor_km=form.valor_km.data or 0,
            alimentacao=form.alimentacao.data or 0,
            hospedagem=form.hospedagem.data or 0,
            outros_gastos=form.outros_gastos.data or 0,
            descricao_outros=form.descricao_outros.data,
            observacoes=form.observacoes.data
        )
        
        reembolso.total = calculate_reimbursement_total(reembolso)
        
        db.session.add(reembolso)
        db.session.commit()
        flash('Solicitação de reembolso criada com sucesso!', 'success')
        return redirect(url_for('reimbursements_list'))
    
    return render_template('reimbursement/form.html', form=form)

# File serving (unique function)
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# GPS location endpoint
@app.route('/get_location', methods=['POST'])
@login_required
def get_location():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if latitude and longitude:
        # Here you could use a reverse geocoding service to get the address
        endereco = f"Lat: {latitude}, Lng: {longitude}"
        return jsonify({
            'success': True,
            'endereco': endereco
        })
    
    return jsonify({'success': False})

# Enhanced reporting features

@app.route('/reports/approval-dashboard')
@login_required
def reports_approval_dashboard():
    """Dashboard for report approvals - only for master users"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem acessar o painel de aprovação.', 'error')
        return redirect(url_for('index'))
    
    # Get reports awaiting approval
    relatorios = Relatorio.query.filter_by(status='Aguardando Aprovacao').order_by(Relatorio.created_at.desc()).all()
    
    return render_template('reports/approval_dashboard.html', relatorios=relatorios)

@app.route('/reports/<int:report_id>/approve', methods=['POST'])
@login_required
def report_approve(report_id):
    """Approve or reject a report"""
    if not current_user.is_master:
        return jsonify({'success': False, 'message': 'Acesso negado.'})
    
    relatorio = Relatorio.query.get_or_404(report_id)
    data = request.get_json()
    action = data.get('action')
    comment = data.get('comment', '')
    
    if action == 'approve':
        relatorio.status = 'Aprovado'
        flash_message = 'Relatório aprovado com sucesso.'
    elif action == 'reject':
        relatorio.status = 'Rejeitado'
        flash_message = 'Relatório rejeitado.'
    else:
        return jsonify({'success': False, 'message': 'Ação inválida.'})
    
    relatorio.aprovador_id = current_user.id
    relatorio.data_aprovacao = datetime.now()
    relatorio.comentario_aprovacao = comment
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': flash_message})

@app.route('/reports/<int:report_id>/generate-pdf')
@login_required
def report_generate_pdf(report_id):
    """Generate PDF for a report"""
    relatorio = Relatorio.query.get_or_404(report_id)
    
    # Check permissions
    if relatorio.autor_id != current_user.id and not current_user.is_master:
        flash('Acesso negado.', 'error')
        return redirect(url_for('reports'))
    
    try:
        pdf_path, filename = generate_visit_report_pdf(relatorio)
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            download_name=f"relatorio_{relatorio.numero}.pdf"
        )
    except Exception as e:
        current_app.logger.error(f"Error generating PDF: {str(e)}")
        flash('Erro ao gerar PDF do relatório.', 'error')
        return redirect(url_for('report_view', report_id=report_id))

@app.route('/reports/<int:report_id>/photo-editor')
@login_required
def report_photo_editor(report_id):
    """Photo editor for report photos"""
    relatorio = Relatorio.query.get_or_404(report_id)
    
    # Check permissions
    if relatorio.autor_id != current_user.id and not current_user.is_master:
        flash('Acesso negado.', 'error')
        return redirect(url_for('reports'))
    
    return render_template('reports/photo_editor.html', relatorio=relatorio)

@app.route('/reports/<int:report_id>/photos/annotate', methods=['POST'])
@login_required
def report_photo_annotate(report_id):
    """Save annotated photo"""
    relatorio = Relatorio.query.get_or_404(report_id)
    
    # Check permissions
    if relatorio.autor_id != current_user.id and not current_user.is_master:
        return jsonify({'success': False, 'message': 'Acesso negado.'})
    
    photo_id = request.form.get('photo_id')
    annotated_image = request.files.get('annotated_image')
    
    if not photo_id or not annotated_image:
        return jsonify({'success': False, 'message': 'Dados incompletos.'})
    
    foto = FotoRelatorio.query.get_or_404(photo_id)
    
    if foto.relatorio_id != relatorio.id:
        return jsonify({'success': False, 'message': 'Foto não pertence a este relatório.'})
    
    try:
        # Save annotated image
        filename = secure_filename(f"annotated_{foto.id}_{uuid.uuid4().hex}.png")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        annotated_image.save(file_path)
        
        # Update photo record
        foto.filename_anotada = filename
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Anotações salvas com sucesso.'})
        
    except Exception as e:
        app.logger.error(f"Error saving annotated photo: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao salvar anotações.'})

@app.route('/reports/<int:report_id>/submit-for-approval', methods=['POST'])
@login_required
def report_submit_for_approval(report_id):
    """Submit report for approval"""
    relatorio = Relatorio.query.get_or_404(report_id)
    
    # Check permissions
    if relatorio.autor_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('reports'))
    
    if relatorio.status != 'Rascunho':
        flash('Apenas relatórios em rascunho podem ser enviados para aprovação.', 'error')
        return redirect(url_for('report_view', report_id=report_id))
    
    relatorio.status = 'Aguardando Aprovacao'
    db.session.commit()
    
    flash('Relatório enviado para aprovação.', 'success')
    return redirect(url_for('report_view', report_id=report_id))

@app.route('/visits/<int:visit_id>/communication', methods=['GET', 'POST'])
@login_required
def visit_communication(visit_id):
    """Visit communication system"""
    visita = Visita.query.get_or_404(visit_id)
    
    if request.method == 'POST':
        mensagem = request.form.get('mensagem')
        tipo = request.form.get('tipo', 'Comunicacao')
        
        if mensagem:
            comunicacao = ComunicacaoVisita(
                visita_id=visit_id,
                usuario_id=current_user.id,
                mensagem=mensagem,
                tipo=tipo
            )
            db.session.add(comunicacao)
            db.session.commit()
            
            flash('Comunicação adicionada com sucesso.', 'success')
        
        return redirect(url_for('visit_communication', visit_id=visit_id))
    
    # Get all communications for this visit
    comunicacoes = ComunicacaoVisita.query.filter_by(visita_id=visit_id).order_by(ComunicacaoVisita.created_at.desc()).all()
    
    return render_template('visits/communication.html', visita=visita, comunicacoes=comunicacoes)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
