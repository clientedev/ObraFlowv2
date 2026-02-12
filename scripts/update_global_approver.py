import os
import sys

# CONFIGURAR VARIAVEL DE AMBIENTE ANTES DE IMPORTAR APP
# Isso garante que o app.py pegue o valor correto
os.environ['DATABASE_URL'] = "postgresql://postgres:KgyYkEmMztCNMSPHVbOpWLTiKZFXYwpB@switchback.proxy.rlwy.net:17107/railway"
print(f"ℹ️ Configurado DATABASE_URL: {os.environ['DATABASE_URL']}")

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, AprovadorPadrao

def update_global_approver():
    with app.app_context():
        try:
            print("🚀 Iniciando atualização do Aprovador Global...")
            print(f"📡 Conectado a: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # 1. Buscar usuário admin (ID 1)
            admin_user = db.session.get(User, 1)
            
            if not admin_user:
                print("❌ ERRO: Usuário com ID 1 não encontrado!")
                return

            print(f"✅ Usuário encontrado: {admin_user.nome_completo} (ID: {admin_user.id})")

            # 2. Desativar outros aprovadores globais
            outros_globais = AprovadorPadrao.query.filter(
                AprovadorPadrao.is_global == True,
                AprovadorPadrao.aprovador_id != admin_user.id,
                AprovadorPadrao.ativo == True
            ).all()

            if outros_globais:
                for aprovador in outros_globais:
                    aprovador.ativo = False
                    print(f"⚠️ Desativado aprovador global anterior: ID {aprovador.aprovador_id}")
            else:
                print("ℹ️ Nenhum outro aprovador global ativo encontrado.")

            # 3. Verificar/Criar aprovador global admin
            aprovador_admin = AprovadorPadrao.query.filter_by(
                is_global=True,
                aprovador_id=admin_user.id
            ).first()

            if aprovador_admin:
                if not aprovador_admin.ativo:
                    aprovador_admin.ativo = True
                    print("✅ Reativado registro de aprovador global para admin.")
                else:
                    print("ℹ️ Admin já é aprovador global ativo.")
            else:
                novo_aprovador = AprovadorPadrao(
                    is_global=True,
                    projeto_id=None,
                    aprovador_id=admin_user.id,
                    ativo=True,
                    prioridade=1,
                    observacoes="Definido via script como Aprovador Global Padrão",
                    criado_por=admin_user.id 
                )
                db.session.add(novo_aprovador)
                print("✅ Criado novo registro de aprovador global para admin.")

            # 4. Commit das alterações
            db.session.commit()
            print("\n🎉 Atualização concluída com sucesso!")
            
            # 5. Verificação Final (Nova Query)
            atual_global = AprovadorPadrao.query.filter_by(is_global=True, ativo=True).first()
            if atual_global and atual_global.aprovador_id == 1:
                print(f"🔍 VERIFICAÇÃO: Aprovador Global Atual é ID {atual_global.aprovador_id} (Correto)")
            else:
                print(f"❌ VERIFICAÇÃO FALHOU: Aprovador Global Atual é ID {atual_global.aprovador_id if atual_global else 'Nenhum'}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    update_global_approver()
