import os
import uuid
from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import RelatorioExpress, FotoRelatorioExpress
from forms_express_new import RelatorioExpressForm, FotoExpressForm, EditarFotoExpressForm, EnvioEmailExpressForm
from pdf_generator_express_new import gerar_pdf_relatorio_express_novo, gerar_numero_relatorio_express
from google_drive_backup import backup_to_drive
from email_service import email_service
import json

# Rota principal do Relatório Express
@app.route('/relatorio-express', methods=['GET', 'POST'])
@login_required
def relatorio_express_novo():
    """Criar novo relatório express independente"""
    form = RelatorioExpressForm()
    
    if form.validate_on_submit():
        try:
            # Gerar número único
            numero = gerar_numero_relatorio_express()
            
            # Criar relatório express
            relatorio_express = RelatorioExpress(
                numero=numero,
                nome_empresa=form.nome_empresa.data,
                nome_obra=form.nome_obra.data,
                endereco_obra=form.endereco_obra.data,
                observacoes=form.observacoes.data,
                itens_observados=form.itens_observados.data,
                preenchido_por=form.preenchido_por.data,
                liberado_por=form.liberado_por.data,
                responsavel_obra=form.responsavel_obra.data,
                data_relatorio=form.data_relatorio.data,
                autor_id=current_user.id
            )
            
            db.session.add(relatorio_express)
            db.session.commit()
            
            flash('Relatório Express criado com sucesso! Agora você pode adicionar fotos.', 'success')
            return redirect(url_for('relatorio_express_detalhes', relatorio_id=relatorio_express.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar relatório express: {str(e)}', 'error')
    
    return render_template('express/novo_completo.html', form=form)

@app.route('/relatorio-express/<int:relatorio_id>')
@login_required
def relatorio_express_detalhes(relatorio_id):
    """Ver detalhes do relatório express"""
    relatorio = RelatorioExpress.query.get_or_404(relatorio_id)
    
    # Verificar acesso (apenas o autor ou usuários master)
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    fotos = FotoRelatorioExpress.query.filter_by(
        relatorio_express_id=relatorio_id
    ).order_by(FotoRelatorioExpress.ordem).all()
    
    foto_form = FotoExpressForm()
    
    return render_template('express/detalhes_completo.html', 
                         relatorio=relatorio, 
                         fotos=fotos, 
                         foto_form=foto_form)

@app.route('/relatorio-express/<int:relatorio_id>/adicionar-foto', methods=['POST'])
@login_required
def relatorio_express_adicionar_foto(relatorio_id):
    """Adicionar foto ao relatório express"""
    relatorio = RelatorioExpress.query.get_or_404(relatorio_id)
    
    # Verificar acesso
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    form = FotoExpressForm()
    
    if form.validate_on_submit():
        try:
            # Upload da foto
            foto_file = form.foto.data
            if foto_file:
                # Gerar nome único
                filename = str(uuid.uuid4()) + '_' + secure_filename(foto_file.filename)
                upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                foto_path = os.path.join(upload_folder, filename)
                foto_file.save(foto_path)
                
                # Determinar próxima ordem
                ultima_foto = FotoRelatorioExpress.query.filter_by(
                    relatorio_express_id=relatorio_id
                ).order_by(FotoRelatorioExpress.ordem.desc()).first()
                
                nova_ordem = (ultima_foto.ordem + 1) if ultima_foto else 1
                
                # Criar registro da foto
                foto = FotoRelatorioExpress(
                    relatorio_express_id=relatorio_id,
                    filename=filename,
                    filename_original=foto_file.filename,
                    legenda=form.legenda.data,
                    categoria=form.categoria.data,
                    ordem=nova_ordem
                )
                
                db.session.add(foto)
                db.session.commit()
                
                flash('Foto adicionada com sucesso!', 'success')
                return redirect(url_for('relatorio_express_detalhes', relatorio_id=relatorio_id))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar foto: {str(e)}', 'error')
    
    # Se chegou aqui, houve erro no formulário
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Erro no campo {field}: {error}', 'error')
    
    return redirect(url_for('relatorio_express_detalhes', relatorio_id=relatorio_id))

@app.route('/relatorio-express/<int:relatorio_id>/remover-foto/<int:foto_id>', methods=['DELETE'])
@login_required
def relatorio_express_remover_foto(relatorio_id, foto_id):
    """Remover foto do relatório express"""
    relatorio = RelatorioExpress.query.get_or_404(relatorio_id)
    foto = FotoRelatorioExpress.query.get_or_404(foto_id)
    
    # Verificar acesso
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    # Verificar se a foto pertence ao relatório
    if foto.relatorio_express_id != relatorio_id:
        return jsonify({'success': False, 'message': 'Foto não pertence a este relatório'})
    
    try:
        # Remover arquivo físico
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        foto_path = os.path.join(upload_folder, foto.filename)
        if os.path.exists(foto_path):
            os.remove(foto_path)
        
        # Remover do banco
        db.session.delete(foto)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Foto removida com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao remover foto: {str(e)}'})

@app.route('/relatorio-express/<int:relatorio_id>/gerar-pdf')
@login_required
def relatorio_express_gerar_pdf(relatorio_id):
    """Gerar PDF do relatório express"""
    relatorio = RelatorioExpress.query.get_or_404(relatorio_id)
    
    # Verificar acesso
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Gerar PDF
        pdf_path = gerar_pdf_relatorio_express_novo(relatorio_id)
        
        if pdf_path and os.path.exists(pdf_path):
            # Atualizar status e caminho do PDF no banco
            relatorio.status = 'Finalizado'
            relatorio.pdf_path = pdf_path
            db.session.commit()
            
            # Preparar dados para backup automático
            backup_data = {
                'id': relatorio.id,
                'numero': relatorio.numero,
                'pdf_path': pdf_path,
                'images': []
            }
            
            # Adicionar fotos ao backup
            fotos = FotoRelatorioExpress.query.filter_by(relatorio_express_id=relatorio_id).all()
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            
            for foto in fotos:
                foto_path = os.path.join(upload_folder, foto.filename)
                if os.path.exists(foto_path):
                    backup_data['images'].append({
                        'path': foto_path,
                        'filename': foto.filename,
                        'legenda': foto.legenda
                    })
            
            # Executar backup no Google Drive
            backup_result = backup_to_drive(backup_data, f"Express_{relatorio.nome_empresa}")
            
            if backup_result.get('success'):
                flash('PDF gerado e backup realizado com sucesso!', 'success')
            else:
                flash('PDF gerado com sucesso! (Erro no backup para Google Drive)', 'warning')
            
            return send_file(pdf_path, as_attachment=True, 
                           download_name=f'{relatorio.numero}_{relatorio.nome_empresa}.pdf')
        else:
            flash('Erro ao gerar PDF', 'error')
            return redirect(url_for('relatorio_express_detalhes', relatorio_id=relatorio_id))
            
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('relatorio_express_detalhes', relatorio_id=relatorio_id))

@app.route('/relatorio-express/<int:relatorio_id>/enviar-email', methods=['GET', 'POST'])
@login_required
def relatorio_express_enviar_email(relatorio_id):
    """Enviar relatório express por email"""
    relatorio = RelatorioExpress.query.get_or_404(relatorio_id)
    
    # Verificar acesso
    if not current_user.is_master and relatorio.autor_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    form = EnvioEmailExpressForm()
    
    if form.validate_on_submit():
        try:
            # Gerar PDF se não existir
            if not relatorio.pdf_path or not os.path.exists(relatorio.pdf_path):
                pdf_path = gerar_pdf_relatorio_express_novo(relatorio_id)
                relatorio.pdf_path = pdf_path
                db.session.commit()
            
            # Preparar emails dos destinatários
            emails_raw = form.emails_destinatarios.data
            emails_list = [email.strip() for email in emails_raw.split(',') if email.strip()]
            
            # Preparar assunto
            assunto = form.assunto.data
            if not assunto:
                assunto = f"Relatório Express - {relatorio.nome_obra} - {relatorio.data_relatorio.strftime('%d/%m/%Y')}"
            
            # Preparar mensagem
            mensagem_personalizada = form.mensagem.data or ""
            
            mensagem_padrao = f"""
            <p>Prezado(a) Cliente,</p>
            
            <p>Segue em anexo o relatório da obra/projeto <strong>{relatorio.nome_obra}</strong> 
            da empresa <strong>{relatorio.nome_empresa}</strong>, conforme visita realizada em {relatorio.data_relatorio.strftime('%d/%m/%Y')}.</p>
            
            {f'<p>{mensagem_personalizada}</p>' if mensagem_personalizada else ''}
            
            <p>Em caso de dúvidas, favor entrar em contato conosco.</p>
            
            <p>Atenciosamente,<br>
            Equipe ELP Consultoria e Engenharia<br>
            Engenharia Civil & Fachadas</p>
            """
            
            # Enviar email
            success = email_service.send_report_email(
                destinatarios=emails_list,
                assunto=assunto,
                corpo_html=mensagem_padrao,
                pdf_path=relatorio.pdf_path,
                nome_anexo=f'{relatorio.numero}_{relatorio.nome_empresa}.pdf'
            )
            
            if success:
                flash('Relatório enviado por email com sucesso!', 'success')
                return redirect(url_for('relatorio_express_detalhes', relatorio_id=relatorio_id))
            else:
                flash('Erro ao enviar email. Verifique as configurações de email.', 'error')
                
        except Exception as e:
            flash(f'Erro ao enviar email: {str(e)}', 'error')
    
    return render_template('express/enviar_email_completo.html', 
                         relatorio=relatorio, 
                         form=form)

@app.route('/relatorios-express')
@login_required
def listar_relatorios_express():
    """Listar todos os relatórios express"""
    if current_user.is_master:
        relatorios = RelatorioExpress.query.order_by(RelatorioExpress.data_criacao.desc()).all()
    else:
        relatorios = RelatorioExpress.query.filter_by(
            autor_id=current_user.id
        ).order_by(RelatorioExpress.data_criacao.desc()).all()
    
    return render_template('express/lista_completa.html', relatorios=relatorios)