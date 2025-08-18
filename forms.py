from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, DateField, FloatField, IntegerField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional
from wtforms.widgets import TextArea
from models import User, TipoObra, Contato, ChecklistTemplate

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

class VisitaForm(FlaskForm):
    projeto_id = SelectField('Projeto', coerce=int, validators=[DataRequired()])
    data_agendada = DateTimeField('Data e Hora Agendada', validators=[DataRequired()])
    objetivo = TextAreaField('Objetivo da Visita', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(VisitaForm, self).__init__(*args, **kwargs)
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

class RelatorioForm(FlaskForm):
    titulo = StringField('Título do Relatório', validators=[DataRequired(), Length(max=300)])
    conteudo = TextAreaField('Conteúdo', widget=TextArea())
    aprovador_nome = StringField('Nome do Aprovador', validators=[Length(max=200)])
    data_relatorio = DateField('Data do Relatório', validators=[DataRequired()])

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
