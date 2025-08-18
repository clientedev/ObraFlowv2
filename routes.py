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
from models import *
from forms import *
from utils import generate_project_number, generate_report_number, send_report_email, calculate_reimbursement_total

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

@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def project_new():
    form = ProjetoForm()
    
    if form.validate_on_submit():
        projeto = Projeto(
            numero=generate_project_number(),
            nome=form.nome.data,
            descricao=form.descricao.data,
            endereco=form.endereco.data,
            tipo_obra_id=form.tipo_obra_id.data,
            responsavel_id=form.responsavel_id.data,
            data_inicio=form.data_inicio.data,
            data_previsao_fim=form.data_previsao_fim.data,
            status=form.status.data
        )
        
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
        project.tipo_obra_id = form.tipo_obra_id.data
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
            projeto_id=form.projeto_id.data,
            usuario_id=current_user.id,
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

# Report management routes
@app.route('/reports')
@login_required
def reports_list():
    reports = Relatorio.query.order_by(Relatorio.created_at.desc()).all()
    return render_template('reports/list.html', reports=reports)

@app.route('/reports/new', methods=['GET', 'POST'])
@login_required
def report_new():
    form = RelatorioForm()
    
    # Set default values
    if not form.data_relatorio.data:
        form.data_relatorio.data = date.today()
    
    if form.validate_on_submit():
        relatorio = Relatorio(
            numero=generate_report_number(),
            projeto_id=request.form.get('projeto_id'),
            visita_id=request.form.get('visita_id') or None,
            autor_id=current_user.id,
            titulo=form.titulo.data,
            conteudo=form.conteudo.data,
            aprovador_nome=form.aprovador_nome.data,
            data_relatorio=form.data_relatorio.data
        )
        
        db.session.add(relatorio)
        db.session.commit()
        flash('Relatório criado com sucesso!', 'success')
        return redirect(url_for('report_view', report_id=relatorio.id))
    
    # Get projects and visits for selection
    projetos = Projeto.query.filter_by(status='Ativo').all()
    visitas = Visita.query.filter_by(status='Realizada').all()
    
    return render_template('reports/form.html', form=form, projetos=projetos, visitas=visitas)

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

# File serving
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

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
