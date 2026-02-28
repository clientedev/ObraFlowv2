"""
OFFLINE PWA API ROUTES
Endpoints dedicados para suporte offline do módulo Obras e Relatórios.
O Service Worker usa estes endpoints para popular o cache e sincronizar dados.
"""
import hashlib
import json
from datetime import datetime
from flask import jsonify, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import app, db, csrf
from models import Projeto, Relatorio, LegendaPredefinida, ChecklistPadrao, FotoRelatorio


# ============================================================
# /api/offline/version — hash de versão para invalidar cache
# ============================================================
@app.route('/api/offline/version')
def offline_version():
    """
    Retorna um hash de versão baseado no timestamp do relatório
    mais recentemente modificado. Usado pelo SW para saber se o cache
    precisa ser atualizado.
    """
    try:
        last_report = Relatorio.query.order_by(Relatorio.updated_at.desc()).first()

        version_source = ""
        if last_report and last_report.updated_at:
            version_source += last_report.updated_at.isoformat()

        if not version_source:
            version_source = "initial"

        version_hash = hashlib.md5(version_source.encode()).hexdigest()[:12]

        response = jsonify({
            'version': version_hash,
            'timestamp': datetime.utcnow().isoformat()
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    except Exception as e:
        app.logger.error(f"❌ offline_version error: {e}")
        return jsonify({'version': 'error', 'error': str(e)}), 500


# ============================================================
# /api/offline/pages — lista de URLs para pre-cache pós-login
# ============================================================
@app.route('/api/offline/pages')
@login_required
def offline_pages():
    """
    Retorna a lista dinâmica de URLs que o Service Worker deve
    pre-cachear para o usuário autenticado.
    Inclui todas as páginas de obras ativas e suas sub-rotas de relatórios.
    """
    try:
        urls = [
            # Módulo de projetos (obras)
            '/projects',
        ]

        # Obras ativas do usuário (status 'Ativo' com A maiúsculo)
        projetos = Projeto.query.filter(
            Projeto.status.in_(['Ativo', 'ativo', 'Em Andamento'])
        ).order_by(Projeto.nome).all()
        for projeto in projetos:
            urls.append(f'/projects/{projeto.id}')
            urls.append(f'/projects/{projeto.id}/reports')
            urls.append(f'/projects/{projeto.id}/checklist')

        # Módulo de relatórios
        urls.append('/reports')
        urls.append('/reports/new')

        # Relatórios recentes (últimos 30 por usuário)
        relatorios = Relatorio.query.order_by(
            Relatorio.created_at.desc()
        ).limit(30).all()
        for rel in relatorios:
            urls.append(f'/reports/{rel.id}/view')
            if rel.status not in ('Aprovado',):
                urls.append(f'/reports/{rel.id}/edit')

        response = jsonify({
            'success': True,
            'urls': urls,
            'total': len(urls)
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    except Exception as e:
        app.logger.error(f"❌ offline_pages error: {e}")
        return jsonify({'success': False, 'error': str(e), 'urls': []}), 500


# ============================================================
# /api/offline/sync-data — snapshot completo dos dados para IndexedDB
# ============================================================
@app.route('/api/offline/sync-data')
@login_required
def offline_sync_data():
    """
    Retorna snapshot JSON completo para popular o IndexedDB offline:
    - Lista de obras ativas
    - Relatórios recentes
    - Legendas predefinidas
    - Checklist padrão
    """
    try:
        # --- Projetos ativos ---
        projetos = Projeto.query.filter(
            Projeto.status.in_(['Ativo', 'ativo', 'Em Andamento'])
        ).order_by(Projeto.nome).all()
        projetos_data = []

        from models import FuncionarioProjeto, EmailCliente, CategoriaObra

        for p in projetos:
            # 1. Obter próximo número do relatório para calcular localmente ou enviar valor inicial
            numeracao_inicial = p.numeracao_inicial or 1
            max_numero_existente = db.session.query(
                db.func.max(Relatorio.numero_projeto)
            ).filter_by(projeto_id=p.id).scalar()
            
            proximo_numero_projeto = numeracao_inicial
            if max_numero_existente is not None:
                proximo_numero_projeto = max(numeracao_inicial - 1, max_numero_existente) + 1
            
            next_numero = f"REL-{proximo_numero_projeto:04d}"
            
            # 2. Obter categorias adicionais do projeto
            categorias = CategoriaObra.query.filter_by(projeto_id=p.id).order_by(CategoriaObra.ordem).all()
            categorias_data = [{'id': c.id, 'nome_categoria': c.nome_categoria} for c in categorias]

            # 3. Obter relatórios e identificar o lembrete anterior (último relatório com lembrete)
            ultimo_relatorio_com_lembrete = Relatorio.query.filter(
                Relatorio.projeto_id == p.id,
                Relatorio.lembrete_proxima_visita != None,
                Relatorio.lembrete_proxima_visita != ''
            ).order_by(Relatorio.numero_projeto.desc()).first()
            
            lembrete_anterior = None
            if ultimo_relatorio_com_lembrete:
                lembrete_anterior = {
                    'texto': ultimo_relatorio_com_lembrete.lembrete_proxima_visita,
                    'numero': ultimo_relatorio_com_lembrete.numero,
                    'origem_id': ultimo_relatorio_com_lembrete.id
                }

            # 4. Obter funcionários
            funcionarios_antigos = FuncionarioProjeto.query.filter_by(projeto_id=p.id, ativo=True).all()
            emails_clientes = EmailCliente.query.filter_by(projeto_id=p.id, ativo=True).all()
            
            funcionarios_data = []
            for func in funcionarios_antigos:
                funcionarios_data.append({
                    'id': f"fp_{func.id}",
                    'nome_funcionario': func.nome_funcionario or '',
                    'cargo': func.cargo or '',
                    'empresa': func.empresa or '',
                    'is_responsavel_principal': func.is_responsavel_principal or False
                })
            for email in emails_clientes:
                funcionarios_data.append({
                    'id': f"ec_{email.id}",
                    'nome_funcionario': email.nome_contato or '',
                    'cargo': email.cargo or '',
                    'empresa': email.empresa or '',
                    'is_responsavel_principal': False
                })
                
            # 5. E-mails do cliente (seleção separada se necessário, mas já consolida na lista de emails normais)
            emails_data = []
            for email in emails_clientes:
                emails_data.append({
                    'id': email.id,
                    'email': email.email or '',
                    'nome_contato': email.nome_contato or '',
                    'cargo': email.cargo or ''
                })

            # 6. Checklist específico do projeto
            from models import ProjetoChecklist
            checklist_projeto = ProjetoChecklist.query.filter_by(projeto_id=p.id).order_by(ProjetoChecklist.ordem).all()
            checklist_projeto_data = []
            for cl in checklist_projeto:
                checklist_projeto_data.append({
                    'id': cl.id,
                    'texto': cl.texto,
                    'etapa': cl.etapa or '',
                    'ordem': cl.ordem or 0,
                    # We do not preload status or checked_in_this_report because offline creation evaluates checklists from zero.
                })

            projetos_data.append({
                'id': p.id,
                'nome': p.nome,
                'numero': p.numero,
                'status': p.status,
                'endereco': p.endereco,
                'construtora': p.construtora,
                'tipo_obra': p.tipo_obra,
                'nome_funcionario': p.nome_funcionario,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'categorias': categorias_data,
                'funcionarios': funcionarios_data,
                'emails': emails_data,
                'next_numero': next_numero,
                'numero_projeto': proximo_numero_projeto,
                'lembrete_anterior': lembrete_anterior,
                'checklist_projeto': checklist_projeto_data,
                # Dados técnicos
                'technical_info': {
                    'elementos_construtivos_base': p.elementos_construtivos_base or '',
                    'especificacao_chapisco_colante': p.especificacao_chapisco_colante or '',
                    'especificacao_chapisco_alvenaria': p.especificacao_chapisco_alvenaria or '',
                    'especificacao_argamassa_emboco': p.especificacao_argamassa_emboco or '',
                    'forma_aplicacao_argamassa': p.forma_aplicacao_argamassa or '',
                    'acabamentos_revestimento': p.acabamentos_revestimento or '',
                    'acabamento_peitoris': p.acabamento_peitoris or '',
                    'acabamento_muretas': p.acabamento_muretas or '',
                    'definicao_frisos_cor': p.definicao_frisos_cor or '',
                    'definicao_face_inferior_abas': p.definicao_face_inferior_abas or '',
                    'observacoes_projeto_fachada': p.observacoes_projeto_fachada or '',
                    'outras_observacoes': p.outras_observacoes or ''
                }
            })
        relatorios = Relatorio.query.order_by(
            Relatorio.created_at.desc()
        ).limit(50).all()
        relatorios_data = []
        for r in relatorios:
            relatorios_data.append({
                'id': r.id,
                'numero': r.numero if hasattr(r, 'numero') else None,
                'titulo': r.titulo,
                'status': r.status,
                'projeto_id': r.projeto_id,
                'autor_id': r.autor_id,
                'created_at': r.created_at.isoformat() if r.created_at else None,
                'updated_at': r.updated_at.isoformat() if r.updated_at else None,
            })

        # --- Legendas ---
        legendas = LegendaPredefinida.query.filter_by(ativo=True).order_by(
            LegendaPredefinida.categoria.asc(), LegendaPredefinida.id.asc()
        ).all()
        legendas_data = [
            {'id': l.id, 'texto': l.texto, 'categoria': l.categoria}
            for l in legendas
        ]

        # --- Checklist padrão ---
        checklist = ChecklistPadrao.query.filter_by(ativo=True).order_by(
            ChecklistPadrao.ordem
        ).all()
        checklist_data = [
            {'id': c.id, 'texto': c.texto, 'ordem': c.ordem}
            for c in checklist
        ]

        # --- Info do usuário atual ---
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'nome_completo': current_user.nome_completo,
            'cargo': current_user.cargo if hasattr(current_user, 'cargo') else None,
            'is_master': current_user.is_master,
        }

        response = jsonify({
            'success': True,
            'synced_at': datetime.utcnow().isoformat(),
            'user': user_data,
            'projetos': projetos_data,
            'relatorios': relatorios_data,
            'legendas': legendas_data,
            'checklist': checklist_data,
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    except Exception as e:
        app.logger.error(f"❌ offline_sync_data error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# /api/offline/save-report — recebe relatório criado offline
# ============================================================
@app.route('/api/offline/save-report', methods=['POST'])
@login_required
@csrf.exempt
def offline_save_report():
    """
    Recebe payload JSON de um relatório criado offline e salva no banco.
    Chamado pelo Service Worker durante sincronização em background.
    Isento de CSRF (autenticação via cookie de sessão é suficiente).
    Retorna o ID real do relatório criado para que o SW possa atualizar cache.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Payload JSON inválido'}), 400

        offline_id = data.get('offline_id')  # ID temporário gerado no dispositivo
        projeto_id = data.get('projeto_id')
        titulo = data.get('titulo', 'Relatório Offline')
        numero = data.get('numero')
        status = data.get('status', 'Rascunho')
        observacoes = data.get('observacoes_finais', '')
        checklist_data = data.get('checklist_data', [])
        acompanhantes = data.get('acompanhantes', [])
        fotos = data.get('fotos', [])
        tech_info = data.get('technical_info', {})
        data_relatorio_str = data.get('data_relatorio', '')
        lembrete = data.get('lembrete_proxima_visita', '')
        categoria = data.get('categoria', '')
        local = data.get('local', '')
        descricao = data.get('descricao', '')
        conteudo = data.get('conteudo', '')

        app.logger.info(
            f"📥 Salvando relatório offline: offline_id={offline_id}, "
            f"projeto_id={projeto_id}, autor={current_user.username}"
        )

        # Verificar se projeto existe
        projeto = None
        if projeto_id:
            projeto = Projeto.query.get(projeto_id)
            if not projeto:
                return jsonify({'success': False, 'error': f'Projeto {projeto_id} não encontrado'}), 404

        # Gerar número do relatório
        try:
            ultimo_relatorio = Relatorio.query.filter_by(
                projeto_id=projeto_id
            ).order_by(Relatorio.numero_projeto.desc()).first()
            if ultimo_relatorio and ultimo_relatorio.numero_projeto:
                proximo_numero = ultimo_relatorio.numero_projeto + 1
            else:
                proximo_numero = projeto.numeracao_inicial if getattr(projeto, 'numeracao_inicial', None) else 1
            numero_formatado = numero or f"{projeto.numero}-R{proximo_numero:03d}"
        except Exception:
            proximo_numero = 1
            numero_formatado = f"OFF-{int(datetime.utcnow().timestamp())}"

        # Parse Data Report
        data_relatorio_val = datetime.utcnow()
        if data_relatorio_str:
            try:
                date_str = str(data_relatorio_str).strip()
                if len(date_str) == 10:
                    from datetime import date as _dr_date
                    _dr_d = _dr_date.fromisoformat(date_str)
                    data_relatorio_val = datetime(_dr_d.year, _dr_d.month, _dr_d.day, 12, 0, 0)
                else:
                    data_relatorio_val = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except Exception as e:
                app.logger.warning(f"Erro ao processar data_relatorio (offline): {e}")

        # Parse Lembrete
        lembrete_val = None
        if lembrete:
            try:
                if isinstance(lembrete, str):
                    lembrete_val = datetime.fromisoformat(lembrete.replace('Z', '+00:00'))
                else:
                    lembrete_val = lembrete
            except (ValueError, TypeError) as e:
                app.logger.warning(f"Erro ao processar lembrete_proxima_visita (offline): {e}")

        # Criar relatório
        novo_relatorio = Relatorio(
            numero=numero_formatado,
            numero_projeto=proximo_numero if 'numero_projeto' in dir(Relatorio) else None,
            titulo=titulo,
            projeto_id=projeto_id,
            autor_id=current_user.id,
            criado_por=current_user.id if 'criado_por' in dir(Relatorio) else None,
            atualizado_por=current_user.id if 'atualizado_por' in dir(Relatorio) else None,
            status=status,
            categoria=categoria,
            local=local,
            descricao=descricao,
            conteudo=conteudo,
            observacoes_finais=observacoes if hasattr(Relatorio, 'observacoes_finais') else "",
            lembrete_proxima_visita=lembrete_val if hasattr(Relatorio, 'lembrete_proxima_visita') else None,
            data_relatorio=data_relatorio_val if hasattr(Relatorio, 'data_relatorio') else datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Tratar Technical Info
        if tech_info:
            for field, value in tech_info.items():
                if hasattr(novo_relatorio, field):
                    setattr(novo_relatorio, field, value)

        # Tratar Checklist
        if checklist_data:
            if isinstance(checklist_data, (dict, list)):
                import json
                novo_relatorio.checklist_data = json.dumps(checklist_data)
            else:
                novo_relatorio.checklist_data = None

        # Tratar Acompanhantes
        if acompanhantes:
            if isinstance(acompanhantes, str):
                try:
                    import json
                    acomp_list = json.loads(acompanhantes)
                    novo_relatorio.acompanhantes = acomp_list if isinstance(acomp_list, list) else []
                except:
                    novo_relatorio.acompanhantes = []
            elif isinstance(acompanhantes, list):
                novo_relatorio.acompanhantes = acompanhantes

        db.session.add(novo_relatorio)
        db.session.flush()
        relatorio_id = novo_relatorio.id

        # Atualizar ChecklistObra 
        if checklist_data and projeto_id:
            try:
                import json as _json
                from models import ChecklistObra
                cl_items = checklist_data
                if isinstance(cl_items, str):
                    cl_items = _json.loads(cl_items)
                
                if isinstance(cl_items, list):
                    for ci in cl_items:
                        item_id = ci.get('id')
                        is_checked = bool(ci.get('concluido') or ci.get('completado'))
                        if item_id and is_checked:
                            obra_item = ChecklistObra.query.get(item_id)
                            if obra_item and getattr(obra_item, 'projeto_id', None) == projeto_id:
                                if getattr(obra_item, 'concluido', False) == False:
                                    obra_item.concluido = True
                                    obra_item.concluido_relatorio_id = relatorio_id
                                    # Handle timezone-aware or naive datetime depending on model
                                    obra_item.concluido_em = datetime.utcnow()
            except Exception as e:
                app.logger.warning(f"Offline ChecklistObra failed: {e}")

        # Salvar as Fotos com Base64
        if fotos:
            import os, base64, hashlib
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Obter ordem máxima atual (agora vazia)
            max_ordem = -1
            
            for idx, foto in enumerate(fotos):
                b64_data = foto.get('base64')
                if not b64_data:
                    continue
                
                try:
                    # Parse Base64 string ex: "data:image/jpeg;base64,...""
                    if ',' in b64_data:
                        header, base64_str = b64_data.split(',', 1)
                        # Extract extension
                        ext = 'jpg'
                        if 'image/png' in header: ext = 'png'
                        elif 'image/webp' in header: ext = 'webp'
                    else:
                        base64_str = b64_data
                        ext = 'jpg'
                        
                    image_bytes = base64.b64decode(base64_str)
                    imagem_hash = hashlib.sha256(image_bytes).hexdigest()
                    
                    # Prevent duplicates
                    foto_existente = FotoRelatorio.query.filter_by(
                        relatorio_id=relatorio_id,
                        imagem_hash=imagem_hash
                    ).first()
                    
                    if not foto_existente:
                        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S%f')
                        final_filename = f"relatorio_{relatorio_id}_{timestamp}_offline_{idx}.{ext}"
                        final_filepath = os.path.join(upload_folder, final_filename)
                        
                        with open(final_filepath, 'wb') as f:
                            f.write(image_bytes)
                            
                        nova_foto = FotoRelatorio(
                            relatorio_id=relatorio_id,
                            url=f"/uploads/{final_filename}",
                            filename=final_filename,
                            imagem=image_bytes if hasattr(FotoRelatorio, 'imagem') else None,
                            imagem_hash=imagem_hash if hasattr(FotoRelatorio, 'imagem_hash') else None,
                            imagem_size=len(image_bytes) if hasattr(FotoRelatorio, 'imagem_size') else None,
                            content_type=f"image/{ext}" if hasattr(FotoRelatorio, 'content_type') else None,
                            legenda=foto.get('caption', ''),
                            tipo_servico=foto.get('category', ''),
                            local=foto.get('local', ''),
                            ordem=foto.get('ordem', max_ordem + idx + 1)
                        )
                        db.session.add(nova_foto)
                except Exception as e:
                    app.logger.warning(f"Failed to process offline photo: {e}")

        db.session.commit()

        app.logger.info(
            f"✅ Relatório offline salvo completamente: id={relatorio_id}, "
            f"offline_id={offline_id}"
        )

        return jsonify({
            'success': True,
            'relatorio_id': relatorio_id,
            'offline_id': offline_id,
            'numero': numero_formatado,
            'message': 'Relatório sincronizado com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"❌ offline_save_report error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'offline_id': data.get('offline_id') if request.is_json else None
        }), 500
