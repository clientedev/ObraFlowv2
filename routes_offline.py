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
        for p in projetos:
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
            })

        # --- Relatórios (últimos 50) ---
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
        descricao = data.get('descricao', '')
        status = data.get('status', 'Rascunho')
        observacoes = data.get('observacoes', '')
        checklist_data = data.get('checklist', [])

        app.logger.info(
            f"📥 Salvando relatório offline: offline_id={offline_id}, "
            f"projeto_id={projeto_id}, autor={current_user.username}"
        )

        # Verificar se projeto existe
        if projeto_id:
            projeto = Projeto.query.get(projeto_id)
            if not projeto:
                projeto_id = None

        # Gerar número do relatório
        try:
            from utils import generate_report_number
            numero = generate_report_number()
        except Exception:
            numero = f"OFF-{int(datetime.utcnow().timestamp())}"

        # Criar relatório
        novo_relatorio = Relatorio(
            numero=numero,
            titulo=titulo,
            descricao=descricao if hasattr(Relatorio, 'descricao') else None,
            observacoes=observacoes if hasattr(Relatorio, 'observacoes') else None,
            status=status,
            projeto_id=projeto_id,
            autor_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Tentar set campos opcionais de forma segura
        optional_fields = ['titulo_obra', 'data_visita', 'clima', 'etapa_obra']
        for field in optional_fields:
            if field in data and hasattr(Relatorio, field):
                try:
                    setattr(novo_relatorio, field, data[field])
                except Exception:
                    pass

        db.session.add(novo_relatorio)
        db.session.flush()  # Obter ID sem commit

        relatorio_id = novo_relatorio.id

        # Salvar checklist se fornecido
        if checklist_data and hasattr(Relatorio, 'checklist_items'):
            # Serializar como JSON se o modelo suportar
            try:
                novo_relatorio.checklist_items = json.dumps(checklist_data)
            except Exception:
                pass

        db.session.commit()

        app.logger.info(
            f"✅ Relatório offline salvo: id={relatorio_id}, "
            f"offline_id={offline_id}"
        )

        return jsonify({
            'success': True,
            'relatorio_id': relatorio_id,
            'offline_id': offline_id,
            'numero': numero,
            'message': 'Relatório sincronizado com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"❌ offline_save_report error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'offline_id': data.get('offline_id') if data else None
        }), 500
