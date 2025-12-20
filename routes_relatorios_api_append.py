
# ===== ENDPOINT DE APROVAÇÃO PARA RELATÓRIOS NORMAIS =====
@app.route('/api/relatorios/<int:relatorio_id>/aprovar', methods=['POST'])
@login_required
def approve_relatorio(relatorio_id):
    """Aprova um relatório normal e envia emails para todos os destinatários"""
    try:
        relatorio = Relatorio.query.get(relatorio_id)
        if not relatorio:
            return jsonify({'success': False, 'error': 'Relatório não encontrado'}), 404
        
        # Verificar se é aprovador
        from models import AprovadorPadrao
        pode_aprovar = current_user.is_master or AprovadorPadrao.query.filter(
            db.or_(
                db.and_(AprovadorPadrao.projeto_id == relatorio.projeto_id, AprovadorPadrao.aprovador_id == current_user.id),
                db.and_(AprovadorPadrao.projeto_id.is_(None), AprovadorPadrao.aprovador_id == current_user.id)
            ),
            AprovadorPadrao.ativo == True
        ).first()
        
        if not pode_aprovar:
            return jsonify({'success': False, 'error': 'Sem permissão para aprovar'}), 403
        
        if relatorio.status != 'Aguardando Aprovação':
            return jsonify({'success': False, 'error': 'Relatório não aguarda aprovação'}), 400
        
        # Marcar como aprovado
        relatorio.status = 'Aprovado'
        relatorio.aprovador_id = current_user.id
        from datetime import datetime
        relatorio.data_aprovacao = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ Relatório {relatorio.numero} aprovado por {current_user.nome_completo}")
        
        # Gerar PDF
        pdf_path = None
        try:
            from pdf_generator import gerar_pdf_relatorio
            resultado_pdf = gerar_pdf_relatorio(relatorio_id, salvar_arquivo=True)
            if resultado_pdf.get('success'):
                pdf_path = resultado_pdf.get('path')
                logger.info(f"✅ PDF gerado: {pdf_path}")
        except Exception as pdf_err:
            logger.error(f"⚠️ Erro ao gerar PDF: {pdf_err}")
        
        # Enviar emails
        emails_enviados = 0
        mensagem_erro = None
        if pdf_path and os.path.exists(pdf_path):
            try:
                from email_service_unified import get_email_service
                email_service = get_email_service()
                resultado_email = email_service.send_approval_email(relatorio, pdf_path)
                emails_enviados = resultado_email.get('enviados', 0)
                if resultado_email.get('erros'):
                    mensagem_erro = '; '.join(resultado_email['erros'][:3])
                logger.info(f"📧 Emails enviados: {emails_enviados}")
            except Exception as email_err:
                logger.error(f"⚠️ Erro ao enviar emails: {email_err}")
                mensagem_erro = str(email_err)
        
        return jsonify({
            'success': True,
            'relatorio': relatorio.numero,
            'status': relatorio.status,
            'emails_enviados': emails_enviados,
            'erro_email': mensagem_erro
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro ao aprovar relatório: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
