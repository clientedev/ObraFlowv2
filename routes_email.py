
"""
Rotas para sistema de configuração de e-mail
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import ConfiguracaoEmail, UserEmailConfig, User
from forms_email import ConfiguracaoEmailForm, UserEmailConfigForm
from app import app, db
from datetime import datetime

@app.route('/admin/configuracao-email')
@login_required
def configuracao_email_list():
    """Lista as configurações de e-mail"""
    if not (current_user.is_master or current_user.is_developer):
        flash('Acesso negado. Apenas administradores podem configurar e-mails.', 'error')
        return redirect(url_for('index'))
    
    configs = ConfiguracaoEmail.query.order_by(ConfiguracaoEmail.nome_configuracao).all()
    return render_template('admin/configuracao_email_list.html', configs=configs)

@app.route('/admin/configuracao-email/nova', methods=['GET', 'POST'])
@login_required
def configuracao_email_nova():
    """Criar nova configuração de e-mail"""
    if not (current_user.is_master or current_user.is_developer):
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    form = ConfiguracaoEmailForm()
    if form.validate_on_submit():
        try:
            # Se marcar como ativo, desativar outras configurações
            if form.ativo.data:
                ConfiguracaoEmail.query.filter_by(ativo=True).update({'ativo': False})
            
            config = ConfiguracaoEmail(
                nome_configuracao=form.nome_configuracao.data,
                servidor_smtp=form.servidor_smtp.data,
                porta_smtp=form.porta_smtp.data,
                use_tls=form.use_tls.data,
                use_ssl=form.use_ssl.data,
                email_remetente=form.email_remetente.data,
                nome_remetente=form.nome_remetente.data,
                template_assunto=form.template_assunto.data or "Relatório do Projeto {projeto_nome} - {data}",
                template_corpo=form.template_corpo.data or """<p>Prezado(a) {nome_cliente},</p><p>Segue em anexo o relatório da obra/projeto conforme visita realizada em {data_visita}.</p><p>Em caso de dúvidas, favor entrar em contato conosco.</p><p>Atenciosamente,<br>Equipe ELP Consultoria e Engenharia<br>Engenharia Civil & Fachadas</p>""",
                ativo=form.ativo.data
            )
            
            db.session.add(config)
            db.session.commit()
            flash('Configuração de e-mail criada com sucesso!', 'success')
            return redirect(url_for('configuracao_email_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar configuração: {str(e)}', 'error')
    
    return render_template('admin/configuracao_email_form.html', 
                         form=form, 
                         title='Nova Configuração de E-mail')

@app.route('/admin/configuracao-email/<int:config_id>/editar', methods=['GET', 'POST'])
@login_required
def configuracao_email_editar(config_id):
    """Editar configuração de e-mail existente"""
    if not (current_user.is_master or current_user.is_developer):
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    config = ConfiguracaoEmail.query.get_or_404(config_id)
    form = ConfiguracaoEmailForm(obj=config)
    
    if form.validate_on_submit():
        try:
            # Se marcar como ativo, desativar outras configurações
            if form.ativo.data and not config.ativo:
                ConfiguracaoEmail.query.filter_by(ativo=True).update({'ativo': False})
            
            config.nome_configuracao = form.nome_configuracao.data
            config.servidor_smtp = form.servidor_smtp.data
            config.porta_smtp = form.porta_smtp.data
            config.use_tls = form.use_tls.data
            config.use_ssl = form.use_ssl.data
            config.email_remetente = form.email_remetente.data
            config.nome_remetente = form.nome_remetente.data
            config.template_assunto = form.template_assunto.data
            config.template_corpo = form.template_corpo.data
            config.ativo = form.ativo.data
            
            db.session.commit()
            flash('Configuração de e-mail atualizada com sucesso!', 'success')
            return redirect(url_for('configuracao_email_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar configuração: {str(e)}', 'error')
    
    return render_template('admin/configuracao_email_form.html', 
                         form=form, 
                         config=config,
                         title='Editar Configuração de E-mail')

@app.route('/admin/configuracao-email/<int:config_id>/ativar', methods=['POST'])
@login_required
def configuracao_email_ativar(config_id):
    """Ativar uma configuração específica"""
    if not (current_user.is_master or current_user.is_developer):
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    
    try:
        # Desativar todas as configurações
        ConfiguracaoEmail.query.filter_by(ativo=True).update({'ativo': False})
        
        # Ativar a configuração específica
        config = ConfiguracaoEmail.query.get_or_404(config_id)
        config.ativo = True
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Configuração "{config.nome_configuracao}" ativada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/configuracao-email/<int:config_id>/testar', methods=['POST'])
@login_required
def configuracao_email_testar(config_id):
    """Testar configuração de e-mail"""
    if not (current_user.is_master or current_user.is_developer):
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    
    try:
        config = ConfiguracaoEmail.query.get_or_404(config_id)
        
        # Testar conexão SMTP
        import smtplib
        from email.mime.text import MIMEText
        
        server = smtplib.SMTP(config.servidor_smtp, config.porta_smtp)
        
        if config.use_tls:
            server.starttls()
        
        # Tentar autenticar (precisa da senha via variável de ambiente)
        import os
        password = os.environ.get('MAIL_PASSWORD')
        if not password:
            return jsonify({
                'success': False, 
                'error': 'Variável de ambiente MAIL_PASSWORD não configurada'
            }), 400
        
        server.login(config.email_remetente, password)
        
        # Enviar e-mail de teste
        msg = MIMEText('Este é um e-mail de teste da configuração ELP.')
        msg['Subject'] = 'Teste de Configuração - ELP Sistema'
        msg['From'] = f"{config.nome_remetente} <{config.email_remetente}>"
        msg['To'] = current_user.email
        
        server.send_message(msg)
        server.quit()
        
        return jsonify({
            'success': True, 
            'message': f'E-mail de teste enviado para {current_user.email}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Configurações de e-mail por usuário
@app.route('/admin/user-email-configs')
@login_required
def user_email_configs_list():
    """Lista configurações de e-mail por usuário"""
    if not (current_user.is_master or current_user.is_developer):
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    configs = UserEmailConfig.query.join(User).all()
    return render_template('admin/user_email_configs.html', configs=configs)

@app.route('/admin/user-email-config/nova', methods=['GET', 'POST'])
@login_required
def user_email_config_nova():
    """Criar nova configuração de e-mail por usuário"""
    if not (current_user.is_master or current_user.is_developer):
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    form = UserEmailConfigForm()
    form.user_id.choices = [(u.id, f"{u.nome_completo} ({u.username})") 
                           for u in User.query.filter_by(ativo=True).all()]
    
    if form.validate_on_submit():
        try:
            # Verificar se usuário já tem configuração
            existing = UserEmailConfig.query.filter_by(user_id=form.user_id.data).first()
            if existing:
                flash('Este usuário já possui uma configuração de e-mail.', 'error')
                return render_template('admin/user_email_config_form.html', form=form)
            
            config = UserEmailConfig(
                user_id=form.user_id.data,
                smtp_server=form.smtp_server.data,
                smtp_port=form.smtp_port.data,
                email_address=form.email_address.data,
                use_tls=form.use_tls.data,
                use_ssl=form.use_ssl.data
            )
            
            # Criptografar e salvar senha
            config.set_password(form.email_password.data)
            
            db.session.add(config)
            db.session.commit()
            
            flash('Configuração de e-mail do usuário criada com sucesso!', 'success')
            return redirect(url_for('user_email_configs_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar configuração: {str(e)}', 'error')
    
    return render_template('admin/user_email_config_form.html', form=form)

@app.route('/admin/user-email-config/<int:config_id>/editar', methods=['GET', 'POST'])
@login_required
def user_email_config_editar(config_id):
    """Editar configuração de e-mail do usuário"""
    if not (current_user.is_master or current_user.is_developer):
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    config = UserEmailConfig.query.get_or_404(config_id)
    form = UserEmailConfigForm(obj=config)
    form.user_id.choices = [(u.id, f"{u.nome_completo} ({u.username})") 
                           for u in User.query.filter_by(ativo=True).all()]
    
    if form.validate_on_submit():
        try:
            config.smtp_server = form.smtp_server.data
            config.smtp_port = form.smtp_port.data
            config.email_address = form.email_address.data
            config.use_tls = form.use_tls.data
            config.use_ssl = form.use_ssl.data
            config.updated_at = datetime.utcnow()
            
            # Atualizar senha apenas se foi fornecida
            if form.email_password.data:
                config.set_password(form.email_password.data)
            
            db.session.commit()
            flash('Configuração atualizada com sucesso!', 'success')
            return redirect(url_for('user_email_configs_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar configuração: {str(e)}', 'error')
    
    return render_template('admin/user_email_config_form.html', form=form, config=config)

@app.route('/admin/user-email-config/<int:config_id>/remover', methods=['POST'])
@login_required
def user_email_config_remover(config_id):
    """Remover configuração de e-mail do usuário"""
    if not (current_user.is_master or current_user.is_developer):
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    
    try:
        config = UserEmailConfig.query.get_or_404(config_id)
        user_nome = config.user.nome_completo
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Configuração de e-mail de {user_nome} removida com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
