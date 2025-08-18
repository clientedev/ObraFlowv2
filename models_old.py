from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nome_completo = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    is_master = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - removed conflicting backrefs

class TipoObra(db.Model):
    __tablename__ = 'tipos_obra'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)

class Projeto(db.Model):
    __tablename__ = 'projetos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    endereco = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    tipo_obra = db.Column(db.String(100), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_inicio = db.Column(db.Date)
    data_previsao_fim = db.Column(db.Date)
    status = db.Column(db.String(50), default='Ativo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contatos = db.relationship('ContatoProjeto', backref='projeto', lazy=True, cascade='all, delete-orphan')
    visitas = db.relationship('Visita', backref='projeto', lazy=True)
    
    relatorios = db.relationship('Relatorio', backref='projeto', lazy=True)
    
    @property
    def responsavel(self):
        return User.query.get(self.responsavel_id)

class Contato(db.Model):
    __tablename__ = 'contatos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    empresa = db.Column(db.String(200))
    cargo = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projetos = db.relationship('ContatoProjeto', backref='contato', lazy=True)



class ContatoProjeto(db.Model):
    __tablename__ = 'contatos_projetos'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    contato_id = db.Column(db.Integer, db.ForeignKey('contatos.id'), nullable=False)
    tipo_relacionamento = db.Column(db.String(100))  # Cliente, Aprovador, Fornecedor, etc.
    is_aprovador = db.Column(db.Boolean, default=False)
    receber_relatorios = db.Column(db.Boolean, default=False)

class Relatorio(db.Model):
    __tablename__ = 'relatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=True)
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    aprovador_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    data_relatorio = db.Column(db.DateTime, default=datetime.utcnow)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    conteudo = db.Column(db.Text)
    status = db.Column(db.String(50), default='Rascunho')  # Rascunho, Pendente, Aprovado, Rejeitado
    comentario_aprovacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fotos = db.relationship('FotoRelatorio', backref='relatorio', lazy=True, cascade='all, delete-orphan')
    
    @property
    def autor(self):
        return User.query.get(self.autor_id)
    
    @property
    def aprovador(self):
        return User.query.get(self.aprovador_id) if self.aprovador_id else None

class FotoRelatorio(db.Model):
    __tablename__ = 'fotos_relatorio'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Foto original
    filename_anotada = db.Column(db.String(255), nullable=True)  # Foto com anotações
    legenda = db.Column(db.String(500), nullable=False)
    descricao = db.Column(db.Text)
    tipo_servico = db.Column(db.String(100))
    ordem = db.Column(db.Integer, default=1)
    coordenadas_anotacao = db.Column(db.Text)  # JSON com coordenadas das anotações
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EnvioRelatorio(db.Model):
    __tablename__ = 'envios_relatorio'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=False)
    email_destinatario = db.Column(db.String(120), nullable=False)
    nome_destinatario = db.Column(db.String(200))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Enviado')

class Reembolso(db.Model):
    __tablename__ = 'reembolsos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'))
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fim = db.Column(db.Date, nullable=False)
    quilometragem = db.Column(db.Float, default=0)
    valor_km = db.Column(db.Float, default=0)
    alimentacao = db.Column(db.Float, default=0)
    hospedagem = db.Column(db.Float, default=0)
    outros_gastos = db.Column(db.Float, default=0)
    descricao_outros = db.Column(db.Text)
    total = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='Pendente')
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    usuario = db.relationship('User', backref='reembolsos')
    projeto = db.relationship('Projeto', backref='reembolsos')

# Initialize default data
def init_default_data():
    """Initialize default data for the application"""
    from app import app, db
    
    with app.app_context():
        # Create default construction types
        if not TipoObra.query.first():
            tipos_obra = [
                TipoObra(nome='Residencial', descricao='Construção de casas e edifícios residenciais'),
                TipoObra(nome='Comercial', descricao='Construção de prédios comerciais e empresariais'),
                TipoObra(nome='Industrial', descricao='Construção de fábricas e instalações industriais'),
                TipoObra(nome='Infraestrutura', descricao='Obras de infraestrutura urbana'),
                TipoObra(nome='Reforma', descricao='Reformas e modernizações'),
                TipoObra(nome='Demolição', descricao='Serviços de demolição'),
            ]
            
            for tipo in tipos_obra:
                db.session.add(tipo)
        
        # Create default checklist templates
        if not ChecklistTemplate.query.first():
            templates = [
                ChecklistTemplate(nome='Verificação de Segurança', descricao='Equipamentos de segurança estão sendo utilizados?', obrigatorio=True, ordem=1),
                ChecklistTemplate(nome='Andamento da Obra', descricao='Como está o progresso da obra?', obrigatorio=True, ordem=2),
                ChecklistTemplate(nome='Qualidade dos Materiais', descricao='Os materiais estão em conformidade?', obrigatorio=False, ordem=3),
                ChecklistTemplate(nome='Prazo de Entrega', descricao='A obra está dentro do cronograma?', obrigatorio=True, ordem=4),
                ChecklistTemplate(nome='Necessidades do Cliente', descricao='O cliente tem alguma solicitação específica?', obrigatorio=False, ordem=5),
                ChecklistTemplate(nome='Problemas Identificados', descricao='Foram identificados problemas que precisam de atenção?', obrigatorio=False, ordem=6),
            ]
            
            for template in templates:
                db.session.add(template)
        
        db.session.commit()
