from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db
import os
from cryptography.fernet import Fernet

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
    is_developer = db.Column(db.Boolean, default=False)  # Novo tipo de usuário
    primeiro_login = db.Column(db.Boolean, default=True)  # Campo para controlar primeiro login
    ativo = db.Column(db.Boolean, default=True)
    cor_agenda = db.Column(db.String(7), default="#0EA5E9")  # Cor HEX para agenda - Item 29
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_aprovador(self):
        """Propriedade para verificar se usuário é aprovador - conforme especificação do documento"""
        try:
            if self.is_master:
                return True
                
            # Importar aqui para evitar circular import
            from routes import current_user_is_aprovador
            return current_user_is_aprovador()
        except Exception:
            return False

class UserEmailConfig(db.Model):
    """Configuração de e-mail por usuário para envio de relatórios"""
    __tablename__ = 'user_email_config'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    smtp_server = db.Column(db.String(255), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=False, default=587)
    email_address = db.Column(db.String(255), nullable=False)
    email_password = db.Column(db.Text, nullable=False)  # Base64 encoded password
    use_tls = db.Column(db.Boolean, nullable=False, default=True)
    use_ssl = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_test_status = db.Column(db.String(20), default='pending')  # 'pending', 'success', 'error'
    last_test_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='email_config')
    
    def set_password(self, password):
        """Encrypt password using Fernet encryption"""
        key = self._get_encryption_key()
        f = Fernet(key)
        encrypted_password = f.encrypt(password.encode())
        self.email_password = encrypted_password.decode()
    
    def get_password(self):
        """Decrypt password using Fernet encryption"""
        key = self._get_encryption_key()
        f = Fernet(key)
        decrypted_password = f.decrypt(self.email_password.encode())
        return decrypted_password.decode()
    
    def _get_encryption_key(self):
        """Get encryption key for password encryption - REQUIRED environment variable"""
        key = os.environ.get('EMAIL_PASSWORD_ENCRYPTION_KEY')
        if not key:
            raise ValueError(
                "EMAIL_PASSWORD_ENCRYPTION_KEY environment variable is required for user email password encryption. "
                "Generate a key using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        return key.encode() if isinstance(key, str) else key
    
    def __repr__(self):
        return f'<UserEmailConfig {self.email_address} for user {self.user_id}>'

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
    construtora = db.Column(db.String(200), nullable=False)  # Nome da construtora
    nome_funcionario = db.Column(db.String(200), nullable=False)  # Nome do funcionário responsável
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_principal = db.Column(db.String(255), nullable=False)  # E-mail principal obrigatório
    data_inicio = db.Column(db.Date)
    data_previsao_fim = db.Column(db.Date)
    status = db.Column(db.String(50), default='Ativo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def responsavel(self):
        return db.session.get(User, self.responsavel_id)

class CategoriaObra(db.Model):
    """Modelo para categorias customizáveis por obra/projeto - Item 16"""
    __tablename__ = 'categorias_obra'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id', ondelete='CASCADE'), nullable=False)
    nome_categoria = db.Column(db.String(100), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Projeto
    projeto = db.relationship('Projeto', backref=db.backref('categorias', lazy='dynamic', order_by='CategoriaObra.ordem'))
    
    # Evitar duplicação de nomes dentro da mesma obra
    __table_args__ = (
        db.UniqueConstraint('projeto_id', 'nome_categoria', name='uq_categoria_por_projeto'),
    )
    
    def to_dict(self):
        """Serializa a categoria para dicionário JSON-compatível"""
        return {
            "id": self.id,
            "nome": self.nome_categoria,
            "ordem": self.ordem,
            "status": "Cadastrada",
            "project_id": self.projeto_id
        }
    
    def __repr__(self):
        return f'<CategoriaObra {self.nome_categoria} - Projeto {self.projeto_id}>'

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

class EmailCliente(db.Model):
    __tablename__ = 'emails_clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    email = db.Column(db.String(255), nullable=True)  # Permite NULL para contatos sem email
    nome_contato = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(100))
    empresa = db.Column(db.String(200))
    telefone = db.Column(db.String(20))  # Campo telefone adicionado
    receber_notificacoes = db.Column(db.Boolean, default=True)
    receber_relatorios = db.Column(db.Boolean, default=True)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Projeto
    projeto = db.relationship('Projeto', backref='emails_clientes')
    
    # Validação única para email + projeto (apenas quando email não é nulo)
    __table_args__ = (db.UniqueConstraint('projeto_id', 'email', name='unique_email_por_projeto'),)

class FuncionarioProjeto(db.Model):
    __tablename__ = 'funcionarios_projetos'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    nome_funcionario = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(100))
    empresa = db.Column(db.String(200))
    is_responsavel_principal = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    projeto = db.relationship('Projeto', backref='funcionarios_projetos')
    funcionario = db.relationship('User', backref='projetos_funcionario')
    
    # Validação única para funcionário + projeto (somente quando user_id não for nulo)
    __table_args__ = (db.UniqueConstraint('projeto_id', 'user_id', name='unique_funcionario_por_projeto'),)

class Visita(db.Model):
    __tablename__ = 'visitas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=True)  # Agora pode ser NULL para 'Outros'
    projeto_outros = db.Column(db.String(300), nullable=True)  # Nome do projeto quando é 'Outros'
    responsavel_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)  # Renomeado de data_agendada
    data_fim = db.Column(db.DateTime, nullable=False)  # Nova: data e hora de fim
    data_realizada = db.Column(db.DateTime, nullable=True)
    observacoes = db.Column(db.Text)  # Renomeado de objetivo, agora opcional
    atividades_realizadas = db.Column(db.Text)
    status = db.Column(db.String(50), default='Agendada')
    endereco_gps = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_pessoal = db.Column(db.Boolean, default=False)  # Flag para compromissos pessoais - Item 31
    criado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Usuário criador - Item 31
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def projeto(self):
        if self.projeto_id:
            return db.session.get(Projeto, self.projeto_id)
        return None
    
    @property
    def projeto_nome(self):
        """Retorna o nome do projeto ou o valor de 'outros'"""
        if self.projeto_id and self.projeto:
            return f"{self.projeto.numero} - {self.projeto.nome}"
        elif self.projeto_outros:
            return self.projeto_outros
        return "Outros"
    
    @property 
    def responsavel(self):
        return db.session.get(User, self.responsavel_id)
    
    @property
    def data_agendada(self):
        """Propriedade para compatibilidade - retorna data_inicio"""
        return self.data_inicio
    
    @property
    def objetivo(self):
        """Propriedade para compatibilidade - retorna observacoes"""
        return self.observacoes

class VisitaParticipante(db.Model):
    """Modelo para armazenar múltiplos participantes de uma visita"""
    __tablename__ = 'visita_participantes'
    
    id = db.Column(db.Integer, primary_key=True)
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    confirmado = db.Column(db.Boolean, default=False)  # Se o participante confirmou presença
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    visita = db.relationship('Visita', backref=db.backref('participantes', lazy='dynamic'))
    user = db.relationship('User', backref='visitas_participante')
    
    # Evitar duplicatas
    __table_args__ = (db.UniqueConstraint('visita_id', 'user_id', name='unique_visita_participante'),)

class Relatorio(db.Model):
    __tablename__ = 'relatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)  # Unique per project, not globally
    numero_projeto = db.Column(db.Integer, nullable=True)  # Project-specific sequential numbering
    titulo = db.Column(db.String(300), nullable=False, default='Relatório de visita')
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=True)
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    aprovador_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    data_relatorio = db.Column(db.DateTime, default=datetime.utcnow)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    conteudo = db.Column(db.Text)
    checklist_data = db.Column(db.Text)  # JSON string for checklist data
    status = db.Column(db.String(50), default='preenchimento')
    comentario_aprovacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint: numero must be unique within each project
    __table_args__ = (db.UniqueConstraint('projeto_id', 'numero', name='uq_relatorios_projeto_numero'),)
    
    # Relacionamentos SQLAlchemy otimizados (evitam queries adicionais)
    autor = db.relationship('User', foreign_keys=[autor_id], backref='relatorios_criados', lazy='select')
    aprovador = db.relationship('User', foreign_keys=[aprovador_id], backref='relatorios_aprovados', lazy='select')  
    projeto = db.relationship('Projeto', foreign_keys=[projeto_id], backref='relatorios', lazy='select')
    
    # Manter properties para compatibilidade (caso sejam usadas em outros lugares)
    @property
    def autor_legacy(self):
        return db.session.get(User, self.autor_id)
    
    @property
    def aprovador_legacy(self):
        return db.session.get(User, self.aprovador_id) if self.aprovador_id else None

    @property
    def projeto_legacy(self):
        return db.session.get(Projeto, self.projeto_id)

    @property
    def visita(self):
        return db.session.get(Visita, self.visita_id) if self.visita_id else None
    

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
        return db.session.get(Visita, self.visita_id)

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
        return db.session.get(Visita, self.visita_id)
    
    @property
    def usuario(self):
        return db.session.get(User, self.usuario_id)
    
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
    local = db.Column(db.String(300))
    anotacoes_dados = db.Column(db.JSON)
    ordem = db.Column(db.Integer, default=1)
    coordenadas_anotacao = db.Column(db.JSON)
    imagem = db.Column(db.LargeBinary, nullable=True)
    imagem_hash = db.Column(db.String(64), nullable=True)
    content_type = db.Column(db.String(100), nullable=True)
    imagem_size = db.Column(db.Integer, nullable=True)
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

class LegendaPredefinida(db.Model):
    __tablename__ = 'legendas_predefinidas'
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(500), nullable=False)
    categoria = db.Column(db.String(100), nullable=False, default='Geral')
    ativo = db.Column(db.Boolean, default=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    criador = db.relationship('User', backref='legendas_criadas')

class AprovadorPadrao(db.Model):
    """Configuração de aprovador padrão por projeto ou global"""
    __tablename__ = 'aprovadores_padrao'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=True)  # NULL = configuração global
    aprovador_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    prioridade = db.Column(db.Integer, default=1)  # 1 = mais alta prioridade
    observacoes = db.Column(db.Text)
    criado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    projeto = db.relationship('Projeto', backref='aprovadores_padrao')
    aprovador = db.relationship('User', foreign_keys=[aprovador_id], backref='aprovacoes_padrao')
    criador = db.relationship('User', foreign_keys=[criado_por], backref='configuracoes_aprovador_criadas')
    
    # Validação única: um aprovador por projeto (ou global se projeto_id for NULL)
    __table_args__ = (db.UniqueConstraint('projeto_id', 'aprovador_id', name='unique_aprovador_projeto'),)
    
    def __repr__(self):
        projeto_nome = self.projeto.nome if self.projeto else "Global"
        aprovador_nome = self.aprovador.nome_completo if self.aprovador else "N/A"
        return f'<AprovadorPadrao {projeto_nome} -> {aprovador_nome}>'

class ChecklistPadrao(db.Model):
    __tablename__ = 'checklist_padrao'
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(500), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChecklistPadrao {self.texto}>'

class LogEnvioEmail(db.Model):
    __tablename__ = 'log_envio_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destinatarios = db.Column(db.Text, nullable=False)  # JSON com lista de emails
    cc = db.Column(db.Text)  # JSON com lista de emails CC
    bcc = db.Column(db.Text)  # JSON com lista de emails BCC
    assunto = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 'enviado', 'falhou', 'pendente'
    erro_detalhes = db.Column(db.Text)  # Detalhes do erro se houver
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    projeto = db.relationship('Projeto', backref='logs_envio_email')
    relatorio = db.relationship('Relatorio', backref='logs_envio_email')
    usuario = db.relationship('User', backref='logs_envio_email')

class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=False)
    usuario_origem_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usuario_destino_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    titulo = db.Column(db.String(300), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'enviado_para_aprovacao', 'aprovado', 'rejeitado'
    status = db.Column(db.String(50), default='nao_lida')  # 'lida', 'nao_lida'
    email_enviado = db.Column(db.Boolean, default=False)
    email_sucesso = db.Column(db.Boolean, nullable=True)
    email_erro = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lida_em = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    relatorio = db.relationship('Relatorio', backref='notificacoes')
    usuario_origem = db.relationship('User', foreign_keys=[usuario_origem_id], backref='notificacoes_enviadas')
    usuario_destino = db.relationship('User', foreign_keys=[usuario_destino_id], backref='notificacoes_recebidas')
    
    def __repr__(self):
        return f'<Notificacao {self.tipo} - Relatório {self.relatorio_id}>'

class ConfiguracaoEmail(db.Model):
    __tablename__ = 'configuracao_email'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_configuracao = db.Column(db.String(100), nullable=False, unique=True)
    servidor_smtp = db.Column(db.String(255), nullable=False)
    porta_smtp = db.Column(db.Integer, nullable=False)
    use_tls = db.Column(db.Boolean, default=True)
    use_ssl = db.Column(db.Boolean, default=False)
    email_remetente = db.Column(db.String(255), nullable=False)
    nome_remetente = db.Column(db.String(200), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Template padrão para e-mails
    template_assunto = db.Column(db.String(500), default="Relatório do Projeto {projeto_nome} - {data}")
    template_corpo = db.Column(db.Text, default="""<p>Prezado(a) {nome_cliente},</p>

<p>Segue em anexo o relatório da obra/projeto conforme visita realizada em {data_visita}.</p>

<p>Em caso de dúvidas, favor entrar em contato conosco.</p>

<p>Atenciosamente,<br>
Equipe ELP Consultoria e Engenharia<br>
Engenharia Civil & Fachadas</p>""")

# Relatório Express - Replicação exata do modelo padrão com dados da empresa
class RelatorioExpress(db.Model):
    __tablename__ = 'relatorios_express'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    
    # Dados da Empresa (substituem projeto_id)
    empresa_nome = db.Column(db.String(200), nullable=False)
    empresa_endereco = db.Column(db.Text)
    empresa_telefone = db.Column(db.String(20))
    empresa_email = db.Column(db.String(120))
    empresa_responsavel = db.Column(db.String(200))
    
    # Campos idênticos ao relatório padrão
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_visita = db.Column(db.Date, nullable=False)
    periodo_inicio = db.Column(db.Time)
    periodo_fim = db.Column(db.Time)
    condicoes_climaticas = db.Column(db.String(200))
    temperatura = db.Column(db.String(50))
    
    # Checklist e observações
    checklist_completo = db.Column(db.Text)  # JSON com itens do checklist (compatibilidade)
    checklist_dados = db.Column(db.Text)      # JSON com dados do checklist
    observacoes_gerais = db.Column(db.Text)
    pendencias = db.Column(db.Text)
    recomendacoes = db.Column(db.Text)
    
    # Status e controle
    status = db.Column(db.String(50), default='rascunho')  # rascunho, finalizado
    
    # Dados de localização
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    endereco_visita = db.Column(db.Text)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finalizado_at = db.Column(db.DateTime)
    
    # Relacionamentos
    autor = db.relationship('User', backref='relatorios_express_criados')
    
    @property
    def fotos(self):
        return FotoRelatorioExpress.query.filter_by(relatorio_express_id=self.id).order_by(FotoRelatorioExpress.ordem).all()
    
    @property
    def participantes(self):
        """Retorna lista de funcionários participantes do relatório express"""
        from models import User
        return User.query.join(RelatorioExpressParticipante).filter(
            RelatorioExpressParticipante.relatorio_express_id == self.id
        ).all()
    
    @property
    def titulo(self):
        """Gera título fixo do relatório express com numeração automática"""
        # Extrai o número sequencial do campo numero (ex: EXP-001 -> 001)
        numero_sequencial = self.numero.split('-')[-1] if '-' in self.numero else self.numero
        return f"Relatório Fotográfico - {numero_sequencial}"
    
    def __repr__(self):
        return f'<RelatorioExpress {self.numero}>'

class FotoRelatorioExpress(db.Model):
    __tablename__ = 'fotos_relatorios_express'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_express_id = db.Column(db.Integer, db.ForeignKey('relatorios_express.id'), nullable=False)
    
    # Campos idênticos ao FotoRelatorio
    filename = db.Column(db.String(255), nullable=False)
    filename_original = db.Column(db.String(255))
    filename_anotada = db.Column(db.String(255))
    titulo = db.Column(db.String(500))
    legenda = db.Column(db.String(500))
    descricao = db.Column(db.Text)
    tipo_servico = db.Column(db.String(100))
    local = db.Column(db.String(300))
    anotacoes_dados = db.Column(db.Text)
    ordem = db.Column(db.Integer, default=1)
    coordenadas_anotacao = db.Column(db.Text)
    imagem = db.Column(db.LargeBinary, nullable=True)  # Armazenamento da imagem no banco
    imagem_hash = db.Column(db.String(64), nullable=True)
    content_type = db.Column(db.String(100), nullable=True)
    imagem_size = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    relatorio_express = db.relationship('RelatorioExpress', backref='fotos_lista')
    
    def __repr__(self):
        return f'<FotoRelatorioExpress {self.filename}>'

class RelatorioExpressParticipante(db.Model):
    """Relacionamento entre relatórios express e funcionários participantes"""
    __tablename__ = 'relatorio_express_participantes'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_express_id = db.Column(db.Integer, db.ForeignKey('relatorios_express.id', ondelete='CASCADE'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    relatorio_express = db.relationship('RelatorioExpress', backref='participantes_lista')
    funcionario = db.relationship('User', backref='participacoes_express')
    
    def __repr__(self):
        return f'<RelatorioExpressParticipante {self.relatorio_express_id}-{self.funcionario_id}>'

class ChecklistObra(db.Model):
    """Checklist personalizado por projeto/obra"""
    __tablename__ = "checklist_obra"

    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id"), nullable=False)
    texto = db.Column(db.String(500), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    criado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    projeto = db.relationship("Projeto", backref="checklist_personalizado")
    criador = db.relationship("User", backref="checklists_criados")

    # Validação única para ordem dentro do projeto
    __table_args__ = (db.UniqueConstraint("projeto_id", "ordem", name="unique_ordem_por_projeto"),)

    def __repr__(self):
        return f"<ChecklistObra {self.projeto.nome}: {self.texto}>"

class ProjetoChecklistConfig(db.Model):
    """Configuração de checklist por projeto - usar padrão ou personalizado"""
    __tablename__ = "projeto_checklist_config"

    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey("projetos.id"), nullable=False, unique=True)
    tipo_checklist = db.Column(db.String(20), nullable=False, default="padrao")  # "padrao" ou "personalizado"
    criado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    projeto = db.relationship("Projeto", backref=db.backref("checklist_config", uselist=False))
    criador = db.relationship("User", backref="configs_checklist_criadas")

    def __repr__(self):
        return f"<ProjetoChecklistConfig {self.projeto.nome}: {self.tipo_checklist}>"