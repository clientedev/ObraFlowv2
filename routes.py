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
def index():
    # Dashboard statistics
    total_projetos = Projeto.query.count()
    projetos_ativos = Projeto.query.filter_by(status='Ativo').count()
    visitas_pendentes = Visita.query.filter_by(status='Agendada').count()
    relatorios_rascunho = Relatorio.query.filter_by(status='Rascunho').count()
    
    # Recent activities
    recent_visitas = Visita.query.order_by(Visita.created_at.desc()).limit(5).all()
    recent_relatorios = Relatorio.query.order_by(Relatorio.created_at.desc()).limit(5).all()
    
    # Se não estiver logado, redirecionar para login
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
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
    if request.method == 'POST':
        # Processar dados do formulário diretamente
        titulo = request.form.get('titulo')
        projeto_id = request.form.get('projeto_id')
        conteudo = request.form.get('conteudo', '')
        aprovador_nome = request.form.get('aprovador_nome', '')
        data_relatorio_str = request.form.get('data_relatorio')
        
        # Validações básicas
        if not titulo or not projeto_id:
            flash('Título e Projeto são obrigatórios.', 'error')
            return redirect(url_for('create_report'))
        
        try:
            projeto_id = int(projeto_id)
            # Convert date string to datetime object
            if data_relatorio_str:
                data_relatorio = datetime.strptime(data_relatorio_str, '%Y-%m-%d')
            else:
                data_relatorio = datetime.now()
        except (ValueError, TypeError):
            flash('Dados inválidos no formulário.', 'error')
            return redirect(url_for('create_report'))
        try:
            # Create report with explicit values
            from models import Relatorio
            relatorio = Relatorio()
            relatorio.numero = generate_report_number()
            relatorio.titulo = titulo
            relatorio.projeto_id = projeto_id
            relatorio.autor_id = current_user.id
            # Process checklist data if provided
            checklist_data = request.form.get('checklist_data')
            checklist_text = ""
            if checklist_data:
                try:
                    import json
                    checklist_items = json.loads(checklist_data)
                    checklist_text = "CHECKLIST DA OBRA:\n\n"
                    for item_data in checklist_items:
                        status = "✓" if item_data.get('completed') else "○"
                        checklist_text += f"{status} {item_data.get('item', '')}\n"
                        if item_data.get('observations'):
                            checklist_text += f"   Observações: {item_data.get('observations')}\n"
                        checklist_text += "\n"
                except Exception as e:
                    print(f"Error parsing checklist data: {e}")
            
            # Process location data with address conversion
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            location_text = ""
            if latitude and longitude:
                from utils import format_coordinates_display
                location_display = format_coordinates_display(latitude, longitude)
                location_text = f"\n\nLOCALIZAÇÃO DO RELATÓRIO:\n{location_display}\nCoordenadas GPS capturadas durante a visita."
            
            # Combine content with checklist and location
            final_content = ""
            if conteudo:
                final_content += conteudo
            if checklist_text:
                if final_content:
                    final_content += "\n\n" + checklist_text
                else:
                    final_content = checklist_text
            if location_text:
                final_content += location_text
            
            relatorio.conteudo = final_content
            relatorio.data_relatorio = data_relatorio
            relatorio.status = 'Aguardando Aprovação'
            relatorio.created_at = datetime.utcnow()
            
            # Set approver if provided
            aprovador_id = request.form.get('aprovador_id')
            if aprovador_id:
                try:
                    relatorio.aprovador_id = int(aprovador_id)
                    # Get approver name for compatibility
                    aprovador = User.query.get(int(aprovador_id))
                    if aprovador:
                        relatorio.aprovador_nome = aprovador.nome_completo
                except (ValueError, TypeError):
                    pass
            
            db.session.add(relatorio)
            db.session.flush()  # Get the ID
            
            # Handle photo uploads if any
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            photo_count = 0
            
            # Process photos from sessionStorage (via form data)
            photos_data = request.form.get('photos_data')
            if photos_data:
                try:
                    import json
                    photos_list = json.loads(photos_data)
                    for i, photo_data in enumerate(photos_list):
                        # Processo simplificado - apenas salvar referência
                        foto = FotoRelatorio()
                        foto.relatorio_id = relatorio.id
                        foto.filename = f"sessao_foto_{i+1}.jpg"
                        foto.legenda = photo_data.get('caption', f'Foto {i+1}')
                        foto.tipo_servico = photo_data.get('category', 'Geral')
                        foto.ordem = i + 1
                        
                        db.session.add(foto)
                        photo_count += 1
                except Exception as e:
                    pass  # Ignore session storage errors
            
            # Process photos from JavaScript form data
            for i in range(5):  # Support up to 5 photos
                # Check for edited photos
                edited_photo_key = f'edited_photo_{i}'
                if edited_photo_key in request.form:
                    try:
                        # Decode base64 image
                        import base64
                        from io import BytesIO
                        from PIL import Image
                        
                        edited_data = request.form[edited_photo_key]
                        # Remove data:image/jpeg;base64, prefix
                        if ',' in edited_data:
                            edited_data = edited_data.split(',')[1]
                        
                        image_data = base64.b64decode(edited_data)
                        image = Image.open(BytesIO(image_data))
                        
                        # Save edited image
                        filename = f"{uuid.uuid4().hex}_edited.jpg"
                        filepath = os.path.join(upload_folder, filename)
                        image.save(filepath, 'JPEG', quality=85)
                        
                        # Get metadata
                        photo_caption = request.form.get(f'photo_caption_{i}', f'Foto {photo_count + 1}')
                        photo_category = request.form.get(f'photo_category_{i}', 'Geral')
                        
                        # Create photo record
                        foto = FotoRelatorio()
                        foto.relatorio_id = relatorio.id
                        foto.filename = filename
                        foto.legenda = photo_caption or f'Foto {photo_count + 1}'
                        foto.tipo_servico = photo_category or 'Geral'
                        foto.ordem = photo_count + 1
                        
                        db.session.add(foto)
                        photo_count += 1
                        print(f"Foto editada {photo_count} salva: {filename}")
                    except Exception as e:
                        print(f"Erro ao processar foto editada {i}: {e}")
                        continue
            
            db.session.commit()
            
            flash(f'Relatório {relatorio.numero} criado com sucesso! {photo_count} fotos adicionadas. Status: Aguardando Aprovação.', 'success')
            return redirect(url_for('edit_report', id=relatorio.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro detalhado ao criar relatório: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Erro ao criar relatório: {str(e)}', 'error')
    
    projetos = Projeto.query.filter_by(status='Ativo').all()
    # Get admin users for approver selection
    admin_users = User.query.filter_by(is_master=True).all()
    return render_template('reports/form_complete.html', projetos=projetos, admin_users=admin_users, today=date.today().isoformat())

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

@app.route('/photo-editor', methods=['GET', 'POST'])
@login_required
def photo_editor():
    """Página do editor de fotos"""
    photo_id = request.args.get('photoId') or request.form.get('photoId')
    return render_template('reports/photo_editor.html', photo_id=photo_id)

@app.route('/reports/photos/<int:photo_id>/annotate', methods=['POST'])
@login_required
def annotate_photo(photo_id):
    """Salvar anotações em uma foto"""
    try:
        foto = FotoRelatorio.query.get_or_404(photo_id)
        data = request.get_json()
        
        if 'image_data' not in data:
            return jsonify({'success': False, 'error': 'Dados da imagem não encontrados'})
        
        # Process base64 image data
        image_data = data['image_data']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Save annotated image
        import base64
        image_binary = base64.b64decode(image_data)
        
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Generate new filename for annotated version
        filename_parts = foto.filename.rsplit('.', 1)
        annotated_filename = f"{filename_parts[0]}_annotated.{filename_parts[1] if len(filename_parts) > 1 else 'jpg'}"
        
        filepath = os.path.join(upload_folder, annotated_filename)
        with open(filepath, 'wb') as f:
            f.write(image_binary)
        
        # Update photo record
        foto.filename = annotated_filename
        foto.coordenadas_anotacao = data.get('annotations', '')
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reports/photos/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """Excluir uma foto"""
    try:
        foto = FotoRelatorio.query.get_or_404(photo_id)
        
        # Check permissions
        if not current_user.is_master and foto.relatorio.autor_id != current_user.id:
            return jsonify({'success': False, 'error': 'Permissão negada'})
        
        # Delete file
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        filepath = os.path.join(upload_folder, foto.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Delete record
        db.session.delete(foto)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reports/<int:id>/status', methods=['POST'])
@login_required
def update_report_status(id):
    """Atualizar status do relatório"""
    try:
        relatorio = Relatorio.query.get_or_404(id)
        data = request.get_json()
        
        # Check permissions
        if not current_user.is_master and relatorio.autor_id != current_user.id:
            return jsonify({'success': False, 'error': 'Permissão negada'})
        
        new_status = data.get('status')
        valid_statuses = ['Rascunho', 'Aguardando Aprovacao', 'Aprovado', 'Rejeitado']
        
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'error': 'Status inválido'})
        
        relatorio.status = new_status
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reports/<int:id>/approve')
@login_required
def approve_report(id):
    """Aprovar relatório - apenas usuários master"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem aprovar relatórios.', 'error')
        return redirect(url_for('reports'))
    
    relatorio = Relatorio.query.get_or_404(id)
    relatorio.status = 'Aprovado'
    relatorio.aprovado_por = current_user.id
    relatorio.data_aprovacao = datetime.utcnow()
    
    db.session.commit()
    flash(f'Relatório {relatorio.numero} aprovado com sucesso!', 'success')
    return redirect(url_for('reports'))

@app.route('/reports/<int:id>/reject')
@login_required
def reject_report(id):
    """Rejeitar relatório - apenas usuários master"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem rejeitar relatórios.', 'error')
        return redirect(url_for('reports'))
    
    relatorio = Relatorio.query.get_or_404(id)
    relatorio.status = 'Rejeitado'
    relatorio.aprovado_por = current_user.id
    relatorio.data_aprovacao = datetime.utcnow()
    
    db.session.commit()
    flash(f'Relatório {relatorio.numero} rejeitado.', 'warning')
    return redirect(url_for('reports'))

@app.route('/reports/pending')
@login_required
def pending_reports():
    """Painel de relatórios pendentes de aprovação - apenas usuários master"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem ver relatórios pendentes.', 'error')
        return redirect(url_for('reports'))
    
    page = request.args.get('page', 1, type=int)
    relatorios = Relatorio.query.filter_by(status='Aguardando Aprovação').order_by(Relatorio.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('reports/pending.html', relatorios=relatorios)

@app.route('/reports/<int:id>/delete')
@login_required
def delete_report(id):
    """Excluir relatório - apenas usuários master"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem excluir relatórios.', 'error')
        return redirect(url_for('reports'))
    
    relatorio = Relatorio.query.get_or_404(id)
    
    # Delete associated photos first
    fotos = FotoRelatorio.query.filter_by(relatorio_id=id).all()
    for foto in fotos:
        try:
            # Delete physical file
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            filepath = os.path.join(upload_folder, foto.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Erro ao deletar arquivo {foto.filename}: {e}")
        db.session.delete(foto)
    
    # Delete report
    numero = relatorio.numero
    db.session.delete(relatorio)
    db.session.commit()
    
    flash(f'Relatório {numero} excluído com sucesso.', 'success')
    return redirect(url_for('reports'))

@app.route('/reports/<int:id>/pdf')
@login_required
def generate_pdf_report(id):
    """Gerar PDF do relatório"""
    try:
        relatorio = Relatorio.query.get_or_404(id)
        fotos = FotoRelatorio.query.filter_by(relatorio_id=id).order_by(FotoRelatorio.ordem).all()
        
        from pdf_generator import ReportPDFGenerator
        generator = ReportPDFGenerator()
        
        # Generate PDF
        pdf_data = generator.generate_report_pdf(relatorio, fotos)
        
        # Create response
        from flask import Response
        filename = f"relatorio_{relatorio.numero.replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        response = Response(
            pdf_data,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Content-Type': 'application/pdf'
            }
        )
        
        return response
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('edit_report', id=id))

@app.route('/api/nearby-projects')
@login_required
def get_nearby_projects():
    """Get projects near user location"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 50, type=float)  # radius in km
        
        if not lat or not lon:
            return jsonify({'success': False, 'error': 'Coordenadas não fornecidas'})
        
        # Get all projects with coordinates
        projects = Projeto.query.filter(
            Projeto.latitude.isnot(None),
            Projeto.longitude.isnot(None)
        ).all()
        
        nearby_projects = []
        for project in projects:
            if project.latitude and project.longitude:
                # Calculate distance using Haversine formula
                distance = calculate_distance(lat, lon, project.latitude, project.longitude)
                if distance <= radius:
                    nearby_projects.append({
                        'id': project.id,
                        'nome': project.nome,
                        'endereco': project.endereco,
                        'status': project.status,
                        'tipo_obra': project.tipo_obra,
                        'distance': round(distance, 2),
                        'latitude': project.latitude,
                        'longitude': project.longitude
                    })
        
        # Sort by distance
        nearby_projects.sort(key=lambda x: x['distance'])
        
        return jsonify({'success': True, 'projects': nearby_projects})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    import math
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return r * c

@app.route('/api/save-annotated-photo', methods=['POST'])
@login_required  
def save_annotated_photo():
    """API para salvar foto anotada (legacy)"""
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
                
                # Create photo record with minimal fields
                foto = FotoRelatorio()
                foto.relatorio_id = relatorio.id
                foto.filename = filename
                foto.legenda = f'Foto {uploaded_count + 1}'
                foto.ordem = uploaded_count + 1
                
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
            
            # Create photo record with minimal fields
            foto_relatorio = FotoRelatorio()
            foto_relatorio.relatorio_id = report_id
            foto_relatorio.filename = unique_filename
            foto_relatorio.titulo = form.titulo.data if hasattr(form, 'titulo') else ""
            foto_relatorio.descricao = form.descricao.data if hasattr(form, 'descricao') else ""
            foto_relatorio.tipo_servico = form.tipo_servico.data if hasattr(form, 'tipo_servico') else "Geral"
            foto_relatorio.ordem = FotoRelatorio.query.filter_by(relatorio_id=report_id).count() + 1
            
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
                envio = EnvioRelatorio()
                envio.relatorio_id = report_id
                envio.email_destinatario = contato_projeto.contato.email
                envio.nome_destinatario = contato_projeto.contato.nome
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
    return render_template('reimbursements/list.html', reembolsos=reembolsos)

@app.route('/reimbursements/request', methods=['GET', 'POST'])
@login_required
def request_reimbursement():
    """Solicitar novo reembolso"""
    if request.method == 'POST':
        try:
            # Create reimbursement record
            reembolso = Reembolso()
            reembolso.usuario_id = current_user.id
            reembolso.projeto_id = int(request.form.get('projeto_id'))
            reembolso.periodo = request.form.get('periodo', '')
            reembolso.motivo = request.form.get('motivo', '')
            
            # Parse numeric values
            distancia = float(request.form.get('distancia_km', 0))
            valor_km = float(request.form.get('valor_km', 0.75))
            alimentacao = float(request.form.get('alimentacao', 0))
            hospedagem = float(request.form.get('hospedagem', 0))
            outros_gastos = float(request.form.get('outros_gastos', 0))
            
            reembolso.quilometragem = distancia
            reembolso.valor_km = valor_km
            reembolso.alimentacao = alimentacao
            reembolso.hospedagem = hospedagem
            reembolso.outros_gastos = outros_gastos
            reembolso.descricao_outros = request.form.get('descricao_outros', '')
            
            # Calculate total
            total_combustivel = distancia * valor_km
            reembolso.total = total_combustivel + alimentacao + hospedagem + outros_gastos
            
            reembolso.status = 'Aguardando Aprovação'
            reembolso.created_at = datetime.utcnow()
            
            db.session.add(reembolso)
            db.session.flush()  # Get the ID
            
            # Handle file uploads (comprovantes)
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            comprovantes_count = 0
            comprovantes_info = []
            
            for i in range(4):  # Support up to 4 receipts
                comprovante_key = f'comprovante_{i}'
                desc_key = f'desc_comprovante_{i}'
                
                if comprovante_key in request.files:
                    file = request.files[comprovante_key]
                    if file and file.filename:
                        try:
                            filename = secure_filename(f"reembolso_{reembolso.id}_{uuid.uuid4().hex}_{file.filename}")
                            filepath = os.path.join(upload_folder, filename)
                            file.save(filepath)
                            
                            desc = request.form.get(desc_key, f'Comprovante {i+1}')
                            comprovantes_info.append({
                                'filename': filename,
                                'description': desc
                            })
                            comprovantes_count += 1
                        except Exception as e:
                            print(f"Erro ao salvar comprovante {i}: {e}")
            
            # Store comprovantes info as JSON in observacoes
            if comprovantes_info:
                import json
                reembolso.observacoes = json.dumps(comprovantes_info)
            
            db.session.commit()
            
            flash(f'Solicitação de reembolso criada com sucesso! {comprovantes_count} comprovantes anexados. Status: Aguardando Aprovação.', 'success')
            return redirect(url_for('reimbursements_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar solicitação: {str(e)}', 'error')
    
    projetos = Projeto.query.filter_by(status='Ativo').all()
    return render_template('reimbursements/request.html', projetos=projetos)

@app.route('/reimbursements/<int:id>/approve')
@login_required
def approve_reimbursement(id):
    """Aprovar solicitação de reembolso - apenas usuários master"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem aprovar reembolsos.', 'error')
        return redirect(url_for('reimbursements_list'))
    
    reembolso = Reembolso.query.get_or_404(id)
    reembolso.status = 'Aprovado'
    reembolso.aprovado_por = current_user.id
    reembolso.data_aprovacao = datetime.utcnow()
    
    db.session.commit()
    flash(f'Reembolso aprovado com sucesso! PDF disponível para download.', 'success')
    return redirect(url_for('reimbursements_admin'))

@app.route('/reimbursements/<int:id>/reject')
@login_required
def reject_reimbursement(id):
    """Rejeitar solicitação de reembolso - apenas usuários master"""
    if not current_user.is_master:
        flash('Acesso negado. Apenas usuários master podem rejeitar reembolsos.', 'error')
        return redirect(url_for('reimbursements_list'))
    
    reembolso = Reembolso.query.get_or_404(id)
    reembolso.status = 'Rejeitado'
    reembolso.aprovado_por = current_user.id
    reembolso.data_aprovacao = datetime.utcnow()
    
    db.session.commit()
    flash(f'Reembolso rejeitado.', 'warning')
    return redirect(url_for('reimbursements_admin'))

@app.route('/reimbursements/admin')
@login_required
def reimbursements_admin():
    """Painel administrativo de reembolsos - apenas usuários master"""
    if not current_user.is_master:
        flash('Acesso negado.', 'error')
        return redirect(url_for('reimbursements_list'))
    
    reembolsos = Reembolso.query.order_by(Reembolso.created_at.desc()).all()
    return render_template('reimbursements/admin.html', reembolsos=reembolsos)

@app.route('/reimbursements/<int:id>/pdf')
@login_required
def generate_reimbursement_pdf(id):
    """Gerar PDF do reembolso aprovado"""
    reembolso = Reembolso.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_master and reembolso.usuario_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('reimbursements_list'))
    
    if reembolso.status != 'Aprovado':
        flash('PDF só pode ser gerado para reembolsos aprovados.', 'error')
        return redirect(url_for('reimbursements_list'))
    
    try:
        from pdf_generator import ReportPDFGenerator
        
        pdf_generator = ReportPDFGenerator()
        output_path = os.path.join('static', 'reimbursements', f'reembolso_{reembolso.id}.pdf')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        pdf_path = pdf_generator.generate_reimbursement_pdf(reembolso, output_path)
        
        return send_from_directory(
            os.path.dirname(output_path),
            os.path.basename(output_path),
            as_attachment=True,
            download_name=f'reembolso_{reembolso.id}_aprovado.pdf'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('reimbursements_list'))

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
