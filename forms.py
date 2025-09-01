import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, DateField, FloatField, IntegerField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from wtforms.widgets import TextArea
from models import User, TipoObra, Contato

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')

class RegisterForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=200)])
    cargo = StringField('Cargo', validators=[Length(max=100)])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    is_master = BooleanField('Usuário Master')

class UserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=200)])
    cargo = StringField('Cargo', validators=[Length(max=100)])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    is_master = BooleanField('Usuário Master')
    ativo = BooleanField('Ativo', default=True)
    password = PasswordField('Nova Senha (deixe em branco para manter atual)', validators=[Optional(), Length(min=6)])
    password2 = PasswordField('Confirmar Nova Senha', validators=[EqualTo('password')])

class ProjetoForm(FlaskForm):
    nome = StringField('Nome do Projeto', validators=[DataRequired(), Length(max=200)])
    descricao = TextAreaField('Descrição')
    endereco = TextAreaField('Endereço')
    latitude = HiddenField()
    longitude = HiddenField()
    tipo_obra = StringField('Tipo de Obra', validators=[DataRequired(), Length(max=100)])
    responsavel_id = SelectField('Responsável', coerce=int, validators=[DataRequired()])
    email_principal = StringField('E-mail Principal do Cliente', validators=[DataRequired(), Email(), Length(max=255)])
    data_inicio = DateField('Data de Início', validators=[Optional()])
    data_previsao_fim = DateField('Previsão de Término', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Ativo', 'Ativo'),
        ('Pausado', 'Pausado'),
        ('Concluído', 'Concluído'),
        ('Cancelado', 'Cancelado')
    ], default='Ativo')
    
    def __init__(self, *args, **kwargs):
        super(ProjetoForm, self).__init__(*args, **kwargs)
        self.responsavel_id.choices = [(u.id, u.nome_completo) for u in User.query.filter_by(ativo=True).all()]

class ContatoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[Optional(), Email()])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    empresa = StringField('Empresa', validators=[Length(max=200)])
    cargo = StringField('Cargo', validators=[Length(max=100)])
    observacoes = TextAreaField('Observações')

class ContatoProjetoForm(FlaskForm):
    contato_id = SelectField('Contato', coerce=int, validators=[DataRequired()])
    tipo_relacionamento = StringField('Tipo de Relacionamento', validators=[Length(max=100)])
    is_aprovador = BooleanField('É Aprovador')
    receber_relatorios = BooleanField('Receber Relatórios por Email')
    
    def __init__(self, *args, **kwargs):
        super(ContatoProjetoForm, self).__init__(*args, **kwargs)
        self.contato_id.choices = [(c.id, f"{c.nome} - {c.empresa or 'Sem empresa'}") for c in Contato.query.all()]

class EmailClienteForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email(), Length(max=255)])
    nome_contato = StringField('Nome do Contato', validators=[DataRequired(), Length(max=200)])
    cargo = StringField('Cargo', validators=[Length(max=100)])
    empresa = StringField('Empresa', validators=[Length(max=200)])
    is_principal = BooleanField('E-mail Principal')
    receber_notificacoes = BooleanField('Receber Notificações', default=True)
    receber_relatorios = BooleanField('Receber Relatórios', default=True)
    ativo = BooleanField('Ativo', default=True)

class VisitaForm(FlaskForm):
    projeto_id = SelectField('Projeto', coerce=int, validators=[DataRequired()])
    data_agendada = DateTimeField('Data e Hora Agendada', validators=[DataRequired()])
    objetivo = TextAreaField('Objetivo da Visita', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(VisitaForm, self).__init__(*args, **kwargs)
        from models import Projeto
        self.projeto_id.choices = [(p.id, f"{p.numero} - {p.nome}") for p in Projeto.query.filter_by(status='Ativo').all()]

class ReportForm(FlaskForm):
    titulo = StringField('Título do Relatório', validators=[DataRequired(), Length(max=200)])
    projeto_id = SelectField('Projeto', coerce=int, validators=[DataRequired()])
    conteudo = TextAreaField('Conteúdo do Relatório')
    
    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        from models import Projeto
        self.projeto_id.choices = [(p.id, f"{p.numero} - {p.nome}") for p in Projeto.query.filter_by(status='Ativo').all()]

class VisitaRealizadaForm(FlaskForm):
    atividades_realizadas = TextAreaField('Atividades Realizadas', validators=[DataRequired()])
    observacoes = TextAreaField('Observações')
    latitude = HiddenField()
    longitude = HiddenField()
    endereco_gps = StringField('Localização GPS', validators=[Optional()])

class ChecklistItemForm(FlaskForm):
    pergunta = TextAreaField('Pergunta', validators=[DataRequired()])
    resposta = TextAreaField('Resposta')
    concluido = BooleanField('Concluído')
    obrigatorio = BooleanField('Obrigatório')

def coerce_int_or_none(value):
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class RelatorioForm(FlaskForm):
    titulo = StringField('Título do Relatório', validators=[DataRequired(), Length(max=300)])
    projeto_id = SelectField('Projeto', coerce=int, validators=[DataRequired()])
    visita_id = SelectField('Visita (Opcional)', coerce=coerce_int_or_none, validators=[Optional()])
    conteudo = TextAreaField('Conteúdo', widget=TextArea())
    aprovador_nome = StringField('Nome do Aprovador', validators=[Length(max=200)])
    data_relatorio = DateField('Data do Relatório', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(RelatorioForm, self).__init__(*args, **kwargs)
        from models import Projeto, Visita
        self.projeto_id.choices = [(p.id, f"{p.numero} - {p.nome}") for p in Projeto.query.filter_by(status='Ativo').all()]
        self.visita_id.choices = [('', 'Selecione uma visita (opcional)')] + [(v.id, f"Visita {v.id} - {v.data_visita.strftime('%d/%m/%Y')}") for v in Visita.query.filter_by(status='Realizada').all()]

class FotoRelatorioForm(FlaskForm):
    foto = FileField('Foto', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens são permitidas!')
    ])
    titulo = StringField('Título da Foto', validators=[Length(max=200)])
    descricao = TextAreaField('Descrição')
    tipo_servico = StringField('Tipo de Serviço', validators=[Length(max=100)])

class ReembolsoForm(FlaskForm):
    projeto_id = SelectField('Projeto (Opcional)', coerce=int, validators=[Optional()])
    periodo_inicio = DateField('Período - Início', validators=[DataRequired()])
    periodo_fim = DateField('Período - Fim', validators=[DataRequired()])
    quilometragem = FloatField('Quilometragem', validators=[Optional(), NumberRange(min=0)])
    valor_km = FloatField('Valor por KM (R$)', validators=[Optional(), NumberRange(min=0)])
    alimentacao = FloatField('Alimentação (R$)', validators=[Optional(), NumberRange(min=0)])
    hospedagem = FloatField('Hospedagem (R$)', validators=[Optional(), NumberRange(min=0)])
    outros_gastos = FloatField('Outros Gastos (R$)', validators=[Optional(), NumberRange(min=0)])
    descricao_outros = TextAreaField('Descrição de Outros Gastos')
    observacoes = TextAreaField('Observações')
    
    def __init__(self, *args, **kwargs):
        super(ReembolsoForm, self).__init__(*args, **kwargs)
        from models import Projeto
        self.projeto_id.choices = [('', 'Selecione um projeto (opcional)')] + [(p.id, f"{p.numero} - {p.nome}") for p in Projeto.query.filter_by(status='Ativo').all()]

class TipoObraForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    descricao = TextAreaField('Descrição')
    ativo = BooleanField('Ativo', default=True)

class ChecklistTemplateForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=200)])
    descricao = TextAreaField('Descrição')
    obrigatorio = BooleanField('Obrigatório')
    ordem = IntegerField('Ordem', validators=[NumberRange(min=0)], default=0)
    ativo = BooleanField('Ativo', default=True)

class LegendaPredefinidaForm(FlaskForm):
    texto = TextAreaField('Texto da Legenda', validators=[DataRequired(), Length(max=500)], render_kw={'rows': 3})
    categoria = SelectField('Categoria', choices=[
        ('Geral', 'Geral'),
        ('Estrutural', 'Estrutural'),
        ('Hidráulica', 'Hidráulica'),
        ('Elétrica', 'Elétrica'),
        ('Acabamentos', 'Acabamentos'),
        ('Segurança', 'Segurança'),
        ('Fachada', 'Fachada'),
        ('Impermeabilização', 'Impermeabilização')
    ], default='Geral', validators=[DataRequired()])
    ativo = BooleanField('Ativo', default=True)

# Formulários para Relatório Express Standalone (sem projeto/empresa)
class RelatorioExpressStandaloneForm(FlaskForm):
    """Formulário completo para Relatório Express independente - Todos os campos do sistema principal"""
    
    # Dados da empresa
    empresa_nome = StringField('Nome da Empresa', validators=[DataRequired(), Length(max=200)])
    empresa_endereco = TextAreaField('Endereço da Empresa')
    empresa_contato = StringField('Pessoa de Contato', validators=[Length(max=100)])
    empresa_telefone = StringField('Telefone', validators=[Length(max=20)])
    empresa_email = StringField('E-mail', validators=[Optional(), Email(), Length(max=120)])
    empresa_cnpj = StringField('CNPJ', validators=[Length(max=20)])
    empresa_logo = FileField('Logo da Empresa', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas arquivos JPG, JPEG e PNG!')
    ])
    
    # Dados do projeto/local
    projeto_nome = StringField('Nome do Projeto', validators=[DataRequired(), Length(max=200)])
    projeto_endereco = TextAreaField('Endereço do Projeto', validators=[DataRequired()])
    projeto_tipo = SelectField('Tipo de Projeto', choices=[
        ('', 'Selecionar...'),
        ('Residencial', 'Residencial'),
        ('Comercial', 'Comercial'),
        ('Industrial', 'Industrial'),
        ('Institucional', 'Institucional'),
        ('Infraestrutura', 'Infraestrutura'),
        ('Reforma', 'Reforma'),
        ('Manutenção', 'Manutenção')
    ], default='')
    projeto_descricao = TextAreaField('Descrição do Projeto')
    data_inicio = DateField('Data de Início', validators=[Optional()])
    data_previsao_fim = DateField('Previsão de Término', validators=[Optional()])
    
    # Dados da visita
    data_visita = DateField('Data da Visita', validators=[DataRequired()], default=datetime.date.today)
    hora_inicio = StringField('Hora de Início', validators=[Optional()])
    hora_fim = StringField('Hora de Término', validators=[Optional()])
    clima = SelectField('Clima', choices=[
        ('', 'Selecionar...'),
        ('Ensolarado', 'Ensolarado'),
        ('Parcialmente nublado', 'Parcialmente nublado'),
        ('Nublado', 'Nublado'),
        ('Chuvoso', 'Chuvoso'),
        ('Garoa', 'Garoa')
    ], default='')
    temperatura = StringField('Temperatura', validators=[Length(max=20)])
    equipe_presentes = TextAreaField('Equipe Presente')
    objetivo_visita = TextAreaField('Objetivo da Visita', validators=[DataRequired()])
    
    # Conteúdo do relatório - todas as seções
    observacoes_preliminares = TextAreaField('Observações Preliminares')
    atividades_executadas = TextAreaField('Atividades Executadas', validators=[DataRequired()])
    materiais_utilizados = TextAreaField('Materiais Utilizados')
    equipamentos_utilizados = TextAreaField('Equipamentos Utilizados')
    problemas_identificados = TextAreaField('Problemas Identificados')
    solucoes_implementadas = TextAreaField('Soluções Implementadas')
    recomendacoes = TextAreaField('Recomendações', validators=[DataRequired()])
    proximos_passos = TextAreaField('Próximos Passos')
    observacoes_tecnicas = TextAreaField('Observações Técnicas')
    observacoes_seguranca = TextAreaField('Observações de Segurança')
    conclusoes = TextAreaField('Conclusões', validators=[DataRequired()])
    observacoes_finais = TextAreaField('Observações Finais')
    
    # Campos técnicos específicos
    normas_aplicaveis = TextAreaField('Normas Aplicáveis')
    especificacoes_tecnicas = TextAreaField('Especificações Técnicas')
    medicoes_realizadas = TextAreaField('Medições Realizadas')
    ensaios_realizados = TextAreaField('Ensaios Realizados')

class FotoExpressStandaloneForm(FlaskForm):
    """Formulário para adicionar foto ao relatório express standalone"""
    foto = FileField('Foto', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas arquivos JPG, JPEG e PNG!')
    ])
    legenda = StringField('Legenda', validators=[DataRequired(), Length(max=500)])
    categoria = SelectField('Categoria', choices=[
        ('Geral', 'Geral'),
        ('Estrutural', 'Estrutural'),
        ('Hidráulica', 'Hidráulica'),
        ('Elétrica', 'Elétrica'),
        ('Acabamentos', 'Acabamentos'),
        ('Segurança', 'Segurança'),
        ('Fachada', 'Fachada'),
        ('Impermeabilização', 'Impermeabilização')
    ], default='Geral')

class EnvioEmailExpressForm(FlaskForm):
    """Formulário para envio de relatório express por email"""
    destinatarios = StringField('E-mails dos Destinatários', validators=[DataRequired()], 
                               render_kw={'placeholder': 'cliente@empresa.com, outro@email.com'})
    assunto = StringField('Assunto', validators=[DataRequired(), Length(max=500)],
                         default='Relatório de Inspeção - {empresa} - {data}')
    mensagem = TextAreaField('Mensagem', validators=[DataRequired()],
                            default="""Prezado(a) cliente,

Segue em anexo o relatório de inspeção realizado conforme solicitado.

Em caso de dúvidas, favor entrar em contato conosco.

Atenciosamente,
Equipe ELP Consultoria e Engenharia""")
