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
    
    @property
    def contatos(self):
        """Retorna todos os contatos associados a este projeto"""
        return db.session.query(Contato).join(ContatoProjeto).filter(
            ContatoProjeto.projeto_id == self.id
        ).all()
    
    @property
    def emails_clientes(self):
        """Retorna todos os emails de clientes associados ao projeto"""
        emails = []
        contatos = db.session.query(Contato).join(ContatoProjeto).filter(
            ContatoProjeto.projeto_id == self.id,
            ContatoProjeto.tipo_relacionamento.in_(['Cliente', 'cliente', 'CLIENTE'])
        ).all()
        
        for contato in contatos:
            emails.extend(contato.emails_ativos)
        
        return list(set(emails))  # Remove duplicates
    
    @property
    def emails_receber_relatorios(self):
        """Retorna emails de contatos que devem receber relatórios"""
        emails = []
        contatos_projetos = db.session.query(ContatoProjeto).join(Contato).filter(
            ContatoProjeto.projeto_id == self.id,
            ContatoProjeto.receber_relatorios == True
        ).all()
        
        for cp in contatos_projetos:
            contato = Contato.query.get(cp.contato_id)
            if contato:
                emails.extend(contato.emails_ativos)
        
        return list(set(emails))  # Remove duplicates

class Contato(db.Model):
    __tablename__ = 'contatos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))  # Mantido por compatibilidade, será deprecated
    telefone = db.Column(db.String(20))
    empresa = db.Column(db.String(200))
    cargo = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def emails_ativos(self):
        """Retorna todos os emails ativos do contato"""
        emails_obj = ContatoEmail.query.filter_by(contato_id=self.id, ativo=True).all()
        return [email.email for email in emails_obj]
    
    @property
    def email_principal(self):
        """Retorna o email principal do contato"""
        principal_obj = ContatoEmail.query.filter_by(contato_id=self.id, ativo=True, principal=True).first()
        if principal_obj:
            return principal_obj.email
        # Fallback to legacy email field or first active email
        if self.email:
            return self.email
        first_email = ContatoEmail.query.filter_by(contato_id=self.id, ativo=True).first()
        return first_email.email if first_email else None
    
    @property
    def projetos(self):
        """Retorna todos os projetos associados a este contato"""
        from sqlalchemy import text
        return db.session.execute(
            text("""
                SELECT p.* FROM projetos p 
                JOIN contatos_projetos cp ON p.id = cp.projeto_id 
                WHERE cp.contato_id = :contato_id
            """), 
            {'contato_id': self.id}
        ).fetchall()

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
    def projeto(self):
        return Projeto.query.get(self.projeto_id)
    
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

class ChecklistTemplate(db.Model):
    __tablename__ = 'checklist_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    obrigatorio = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)

class ChecklistItem(db.Model):
    __tablename__ = 'checklist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('checklist_templates.id'), nullable=True)
    pergunta = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text)
    concluido = db.Column(db.Boolean, default=False)
    obrigatorio = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer, default=0)
    
    @property
    def visita(self):
        return Visita.query.get(self.visita_id)

class ComunicacaoVisita(db.Model):
    __tablename__ = 'comunicacoes_visitas'
    
    id = db.Column(db.Integer, primary_key=True)
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), default='Comunicacao')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def visita(self):
        return Visita.query.get(self.visita_id)
    
    @property
    def usuario(self):
        return User.query.get(self.usuario_id)
    
    @property
    def fotos(self):
        return FotoRelatorio.query.filter_by(relatorio_id=self.id).order_by(FotoRelatorio.ordem).all()

class FotoRelatorio(db.Model):
    __tablename__ = 'fotos_relatorio'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filename_original = db.Column(db.String(255))
    filename_anotada = db.Column(db.String(255))
    titulo = db.Column(db.String(500))
    legenda = db.Column(db.String(500))
    descricao = db.Column(db.Text)
    tipo_servico = db.Column(db.String(100))
    anotacoes_dados = db.Column(db.Text)
    ordem = db.Column(db.Integer, default=1)
    coordenadas_anotacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EnvioRelatorio(db.Model):
    __tablename__ = 'envios_relatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=False)
    email_destinatario = db.Column(db.String(120), nullable=False)
    nome_destinatario = db.Column(db.String(200))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status_entrega = db.Column(db.String(50), default='Enviado')
    tentativas = db.Column(db.Integer, default=1)
    erro_envio = db.Column(db.Text)

class ContatoEmail(db.Model):
    __tablename__ = 'contatos_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    contato_id = db.Column(db.Integer, db.ForeignKey('contatos.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    principal = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint for email per contact
    __table_args__ = (db.UniqueConstraint('contato_id', 'email', name='_contato_email_uc'),)

# Add relationship to Contato after ContatoEmail is defined
Contato.emails = db.relationship('ContatoEmail', backref='contato', lazy='dynamic', cascade='all, delete-orphan')

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
    observacoes = db.Column(db.Text)
    total = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='Pendente')
    aprovado_por = db.Column(db.Integer, db.ForeignKey('users.id'))
    data_aprovacao = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)