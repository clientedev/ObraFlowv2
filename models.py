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
    is_developer = db.Column(db.Boolean, default=False)  # Novo tipo de usuário
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
    email_principal = db.Column(db.String(255), nullable=False)  # E-mail principal obrigatório
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

class EmailCliente(db.Model):
    __tablename__ = 'emails_clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    nome_contato = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(100))
    empresa = db.Column(db.String(200))
    is_principal = db.Column(db.Boolean, default=False)  # Indica se é o e-mail principal
    receber_notificacoes = db.Column(db.Boolean, default=True)
    receber_relatorios = db.Column(db.Boolean, default=True)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Projeto
    projeto = db.relationship('Projeto', backref='emails_clientes')
    
    # Validação única para email + projeto
    __table_args__ = (db.UniqueConstraint('projeto_id', 'email', name='unique_email_por_projeto'),)

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

class RelatorioExpress(db.Model):
    __tablename__ = 'relatorios_express'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    observacoes = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    projeto = db.relationship('Projeto', backref='relatorios_express')
    autor = db.relationship('User', backref='relatorios_express_criados')
    
    def __repr__(self):
        return f'<RelatorioExpress {self.numero}>'

class FotoRelatorioExpress(db.Model):
    __tablename__ = 'fotos_relatorios_express'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_express_id = db.Column(db.Integer, db.ForeignKey('relatorios_express.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    legenda = db.Column(db.String(500), nullable=False)
    ordem = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    relatorio_express = db.relationship('RelatorioExpress', backref='fotos')
    
    def __repr__(self):
        return f'<FotoRelatorioExpress {self.filename}>'

class RelatorioExpressStandalone(db.Model):
    """Relatório Express independente - sem vínculo com projeto/empresa"""
    __tablename__ = 'relatorios_express_standalone'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    
    # Dados da empresa (não cadastrada, apenas para este relatório)
    empresa_nome = db.Column(db.String(200), nullable=False)
    empresa_endereco = db.Column(db.Text)
    empresa_contato = db.Column(db.String(100))
    empresa_telefone = db.Column(db.String(20))
    empresa_email = db.Column(db.String(120))
    empresa_logo_filename = db.Column(db.String(255))  # Logo upload opcional
    
    # Dados do relatório
    titulo_relatorio = db.Column(db.String(200), nullable=False)
    local_inspecao = db.Column(db.Text)
    data_inspecao = db.Column(db.Date, nullable=False)
    observacoes_gerais = db.Column(db.Text)
    itens_observados = db.Column(db.Text)  # JSON com lista de itens
    
    # Metadados
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='rascunho')  # rascunho, finalizado
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_finalizacao = db.Column(db.DateTime)
    
    # Relacionamentos
    autor = db.relationship('User', backref='relatorios_express_standalone')
    
    def __repr__(self):
        return f'<RelatorioExpressStandalone {self.numero}>'

class FotoRelatorioExpressStandalone(db.Model):
    """Fotos do Relatório Express Standalone"""
    __tablename__ = 'fotos_relatorios_express_standalone'
    
    id = db.Column(db.Integer, primary_key=True)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios_express_standalone.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    legenda = db.Column(db.String(500), nullable=False)
    categoria = db.Column(db.String(100), default='Geral')
    ordem = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    relatorio = db.relationship('RelatorioExpressStandalone', backref='fotos')
    
    def __repr__(self):
        return f'<FotoRelatorioExpressStandalone {self.filename}>'