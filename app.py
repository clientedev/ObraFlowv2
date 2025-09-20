import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
import time
import logging
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# create the app
app = Flask(__name__)
# Require SESSION_SECRET for production security
session_secret = os.environ.get("SESSION_SECRET")
if not session_secret:
    raise ValueError("SESSION_SECRET environment variable is required for production security")
app.secret_key = session_secret
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database, relative to the app instance folder
database_url = os.environ.get("DATABASE_URL", "sqlite:///construction_tracker.db")

# Handle Replit PostgreSQL environment
# Replit provides DATABASE_URL for PostgreSQL when database is provisioned
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    logging.info(f"✅ Using PostgreSQL database")
elif database_url.startswith("postgresql://"):
    logging.info(f"✅ Using PostgreSQL database")
else:
    # Fallback to SQLite for development or when PostgreSQL not available
    database_url = "sqlite:///construction_tracker.db"
    logging.info(f"📝 Using SQLite database: {database_url}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/reports', exist_ok=True)

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# CSRF Configuration - Enable for security
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_CHECK_DEFAULT'] = True  # Check CSRF by default for security
app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
try:
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    logging.info("✅ Flask extensions initialized successfully")
except Exception as e:
    logging.error(f"❌ Error initializing Flask extensions: {e}")
    raise

# Login manager configuration
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    try:
        return db.session.get(User, int(user_id))
    except Exception as e:
        app.logger.error(f"Error loading user {user_id}: {e}")
        return None

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def create_admin_user_safe():
    from models import User
    from werkzeug.security import generate_password_hash
    MAX_RETRIES = 5
    RETRY_DELAY = 5 # seconds

    for attempt in range(MAX_RETRIES):
        try:
            # Attempt to create admin user
            existing_admin = User.query.filter_by(is_master=True).first()
            if not existing_admin:
                admin_user = User(
                    username='admin',
                    email='admin@exemplo.com',
                    password_hash=generate_password_hash('admin123'),
                    nome_completo='Administrador do Sistema',
                    cargo='Administrador',
                    is_master=True,
                    ativo=True
                )
                db.session.add(admin_user)
                db.session.commit()
                logging.info("Admin user created successfully")
            else:
                logging.info("Admin user already exists.")
            break # Exit loop if successful
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed to create admin user: {e}")
            if attempt < MAX_RETRIES - 1:
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error("Max retries reached. Could not create admin user.")

def create_default_checklists():
    from models import ChecklistPadrao, User

    # Definir os 6 itens de checklist padrão
    checklist_padrao = [
        ("Verificar condições de segurança no local", 1),
        ("Conferir progresso da obra conforme cronograma", 2),
        ("Inspecionar qualidade dos materiais utilizados", 3),
        ("Avaliar execução conforme projeto técnico", 4),
        ("Registrar problemas ou não conformidades encontradas", 5),
        ("Verificar limpeza e organização do canteiro", 6)
    ]

    try:
        # Verificar se já existem itens
        count = ChecklistPadrao.query.filter_by(ativo=True).count()
        if count >= 6:
            logging.info(f"✅ Checklist padrão já existe: {count} itens encontrados")
            return

        # Buscar usuário admin para ser o criador
        admin_user = User.query.filter_by(is_master=True).first()
        if not admin_user:
            logging.error("❌ Admin user não encontrado - não é possível criar checklist")
            return

        # Criar itens que não existem
        itens_criados = 0
        for texto, ordem in checklist_padrao:
            # Verificar se já existe
            existe = ChecklistPadrao.query.filter_by(texto=texto, ordem=ordem).first()
            if not existe:
                novo_item = ChecklistPadrao(
                    texto=texto,
                    ordem=ordem,
                    ativo=True
                )
                db.session.add(novo_item)
                itens_criados += 1

        if itens_criados > 0:
            db.session.commit()
            total_final = ChecklistPadrao.query.filter_by(ativo=True).count()
            logging.info(f"✅ CHECKLIST CRIADO: {itens_criados} novos itens | Total: {total_final}")
        else:
            logging.info("✅ Todos os itens de checklist já existem")

    except Exception as e:
        logging.error(f"❌ Erro ao criar checklist padrão: {e}")
        db.session.rollback()

def create_default_legendas():
    """Criar legendas padrão no Railway PostgreSQL"""
    try:
        from models import LegendaPredefinida, User

        # Forçar rollback de transações pendentes
        try:
            db.session.rollback()
        except Exception:
            pass

        # Verificar se já existem legendas
        try:
            count = LegendaPredefinida.query.filter_by(ativo=True).count()
            if count >= 42:
                logging.info(f"✅ Legendas já existem: {count} encontradas")
                return
        except Exception as count_error:
            logging.warning(f"⚠️ Erro ao contar legendas: {count_error}")
            # Continuar mesmo assim

        # Buscar usuário admin
        admin_user = User.query.filter_by(is_master=True).first()
        if not admin_user:
            logging.error("❌ Admin user não encontrado - criando legendas sem criador")
            # Criar um usuário temporário se necessário
            temp_admin = User(
                username='temp_admin',
                email='temp@example.com',
                password_hash='temp',
                nome_completo='Admin Temporário',
                is_master=True
            )
            db.session.add(temp_admin)
            db.session.flush()
            admin_user = temp_admin

        # Definir legendas padrão
        legendas_padrao = [
            # Acabamentos (16 legendas)
            ("Emboço bem-acabado", "Acabamentos"),
            ("Emboço mal-acabado", "Acabamentos"),
            ("Friso com profundidade irregular", "Acabamentos"),
            ("Friso torto", "Acabamentos"),
            ("Lixamento com falhas, necessário correção", "Acabamentos"),
            ("Lixamento corretamente executado", "Acabamentos"),
            ("Lixamento executado sem preenchimento de chupetas", "Acabamentos"),
            ("Lixamento executado sem preenchimento do encunhamento", "Acabamentos"),
            ("Necessário preenchimento das juntas dos blocos", "Acabamentos"),
            ("Necessário retirada de etiquetas", "Acabamentos"),
            ("Necessário retirada de madeiras encrustadas no concreto", "Acabamentos"),
            ("Necessário retirada de pregos", "Acabamentos"),
            ("Necessário retirada de pó de serra incrustado no concreto", "Acabamentos"),
            ("Necessário retirada do excesso de massa da junta dos blocos", "Acabamentos"),
            ("Pendente lixamento das requadrações superiores dos caixilhos", "Acabamentos"),
            ("Pingadeira mal-acabada", "Acabamentos"),

            # Estrutural (18 legendas)
            ("Caída invertida", "Estrutural"),
            ("Chupeta na laje", "Estrutural"),
            ("Chupeta no pilar", "Estrutural"),
            ("Chupeta na viga", "Estrutural"),
            ("Encunhamento mal-acabado", "Estrutural"),
            ("Encunhamento mal-executado", "Estrutural"),
            ("Estrutura bem-acabada", "Estrutural"),
            ("Estrutura executada conforme projeto", "Estrutural"),
            ("Falha de concretagem", "Estrutural"),
            ("Formação de ninho de concretagem", "Estrutural"),
            ("Grampo de ligação não executado conforme projeto", "Estrutural"),
            ("Laje executada conforme projeto", "Estrutural"),
            ("Necessário retirada de pontas de ferro", "Estrutural"),
            ("Pilar executado conforme projeto", "Estrutural"),
            ("Presença de madeira encrustada no concreto", "Estrutural"),
            ("Segregação de agregados", "Estrutural"),
            ("Viga executada conforme projeto", "Estrutural"),
            ("Viga executada fora dos padrões", "Estrutural"),

            # Geral (6 legendas)
            ("Executado conforme projeto", "Geral"),
            ("Estrutura com bom acabamento", "Geral"),
            ("Não evidenciado chapisco colante antes do emboço sobre aba", "Geral"),
            ("Não evidenciado chapisco colante antes do emboço sobre mureta", "Geral"),
            ("Uso de talisca de madeira - necessário retirada", "Geral"),
            ("Uso incorreto de chapisco colante em pó", "Geral"),

            # Segurança (2 legendas)
            ("Pendente corte dos ganchos", "Segurança"),
            ("Pendente tratamento dos ganchos com tinta anti-corrosiva", "Segurança")
        ]

        # Criar legendas em lotes
        legendas_criadas = 0
        batch_size = 10

        for i in range(0, len(legendas_padrao), batch_size):
            batch = legendas_padrao[i:i + batch_size]

            for ordem, (texto, categoria) in enumerate(batch, start=i+1):
                try:
                    # Verificar se já existe (busca por texto exato)
                    existe = LegendaPredefinida.query.filter(
                        LegendaPredefinida.texto == texto,
                        LegendaPredefinida.categoria == categoria,
                        LegendaPredefinida.ativo == True
                    ).first()

                    if not existe:
                        nova_legenda = LegendaPredefinida(
                            texto=texto,
                            categoria=categoria,
                            numero_ordem=ordem,
                            ativo=True,
                            criado_por=admin_user.id
                        )
                        db.session.add(nova_legenda)
                        legendas_criadas += 1

                except Exception as create_error:
                    logging.warning(f"⚠️ Erro ao criar legenda '{texto}': {create_error}")
                    continue

            # Commit em lotes
            try:
                db.session.commit()
                logging.info(f"✅ Batch {i//batch_size + 1}: {len(batch)} legendas processadas")
            except Exception as commit_error:
                logging.error(f"❌ Erro ao salvar batch: {commit_error}")
                db.session.rollback()
                continue

        # Verificação final
        try:
            total_final = LegendaPredefinida.query.filter_by(ativo=True).count()
            logging.info(f"✅ LEGENDAS FINALIZADAS: {legendas_criadas} criadas | Total: {total_final}")
        except Exception as final_count_error:
            logging.warning(f"⚠️ Erro na contagem final: {final_count_error}")

    except Exception as e:
        logging.exception(f"❌ Erro crítico ao criar legendas padrão: {str(e)}")
        try:
            db.session.rollback()
        except Exception:
            pass


# Initialize database in a separate function for Railway optimization
def init_database():
    """Initialize database tables and default data"""
    try:
        with app.app_context():
            # Make sure to import the models here or their tables won't be created
            import models  # noqa: F401

            # Quick database setup for Railway
            db.create_all()
            logging.info("Database tables created successfully.")

            # Create default admin user if none exists
            create_admin_user_safe()

            # Create default checklists if they don't exist
            create_default_checklists()

            # Create default legendas if they don't exist
            create_default_legendas()
    except Exception as e:
        logging.error(f"Database initialization error: {e}")

# Initialize database for Railway deployment
if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("DATABASE_URL"):
    # Direct initialization for Railway (more reliable than threading)
    logging.info("🚂 Railway environment detected - initializing database")
    init_database()
else:
    # Direct initialization for local development
    logging.info("💻 Local environment detected - initializing database")
    init_database()