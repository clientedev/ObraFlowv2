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

class ContatoProjeto(db.Model):
    __tablename__ = 'contatos_projetos'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    contato_id = db.Column(db.Integer, db.ForeignKey('contatos.id'), nullable=False)
    tipo_relacionamento = db.Column(db.String(100))
    is_aprovador = db.Column(db.Boolean, default=False)
    receber_relatorios = db.Column(db.Boolean, default=False)

class Visita(db.Model):
    __tablename__ = 'visitas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_agendada = db.Column(db.DateTime, nullable=False)
    data_realizada = db.Column(db.DateTime, nullable=True)
    objetivo = db.Column(db.Text)
    atividades_realizadas = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(50), default='Agendada')
    endereco_gps = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def responsavel(self):
        return User.query.get(self.responsavel_id)

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
    checklist_data = db.Column(db.Text)  # JSON string for checklist data
    status = db.Column(db.String(50), default='Rascunho')
    comentario_aprovacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def autor(self):
        return User.query.get(self.autor_id)
    
    @property
    def aprovador(self):
        return User.query.get(self.aprovador_id) if self.aprovador_id else None

    @property
    def projeto(self):
        return Projeto.query.get(self.projeto_id)

    @property
    def visita(self):
        return Visita.query.get(self.visita_id) if self.visita_id else None
    
    @property
    def fotos(self):
        return FotoRelatorio.query.filter_by(relatorio_id=self.id).order_by(FotoRelatorio.ordem).all()

class FotoRelatorio(db.Model):
    __tablename__ = 'fotos_relatorio'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filename_anotada = db.Column(db.String(255), nullable=True)
    legenda = db.Column(db.String(500), nullable=False)
    descricao = db.Column(db.Text)
    tipo_servico = db.Column(db.String(100))
    ordem = db.Column(db.Integer, default=1)
    coordenadas_anotacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)