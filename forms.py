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

# Formulário para troca de senha no primeiro login
class FirstLoginForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('new_password', message='As senhas devem coincidir')])

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
    endereco = TextAreaField('Endereço')
    latitude = HiddenField()
    longitude = HiddenField()
    construtora = StringField('Construtora', validators=[DataRequired(), Length(max=200)])
    nome_funcionario = StringField('Nome do Funcionário', validators=[DataRequired(), Length(max=200)])
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
        # Filtrar apenas contatos ativos
        from models import Contato
        contatos_ativos = Contato.query.filter_by(ativo=True).all() if hasattr(Contato, 'ativo') else Contato.query.all()
        self.contato_id.choices = [(c.id, f"{c.nome} - {c.empresa or 'Sem empresa'}") for c in contatos_ativos]

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

# ReportForm removed - use RelatorioForm instead which doesn't have titulo field

class ChecklistPadraoForm(FlaskForm):
    titulo = StringField('Título do Item', validators=[DataRequired(), Length(max=200)])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    categoria = SelectField('Categoria', choices=[
        ('Estrutural', 'Estrutural'),
        ('Acabamentos', 'Acabamentos'),
        ('Instalações', 'Instalações'),
        ('Segurança', 'Segurança'),
        ('Limpeza', 'Limpeza'),
        ('Geral', 'Geral')
    ], default='Geral', validators=[DataRequired()])
    ordem = IntegerField('Ordem', validators=[Optional(), NumberRange(min=1)])
    obrigatorio = BooleanField('Item Obrigatório', default=False)
    ativo = BooleanField('Ativo', default=True)

class RelatorioForm(FlaskForm):
    projeto_id = SelectField('Projeto', coerce=int, validators=[DataRequired()])
    titulo = StringField('Título do Relatório', validators=[DataRequired(), Length(max=300)], default='Relatório de visita')
    data_relatorio = DateField('Data do Relatório', validators=[DataRequired()], default=datetime.date.today)
    aprovador_nome = StringField('Nome do Aprovador', validators=[DataRequired(), Length(max=200)])
    conteudo = TextAreaField('Conteúdo do Relatório', validators=[Optional()], widget=TextArea())
    observacoes = TextAreaField('Observações Gerais', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Rascunho', 'Rascunho'),
        ('Aguardando Aprovacao', 'Aguardando Aprovação'),
        ('Aprovado', 'Aprovado'),
        ('Rejeitado', 'Rejeitado')
    ], default='Rascunho')
    
    def __init__(self, *args, **kwargs):
        super(RelatorioForm, self).__init__(*args, **kwargs)
        from models import Projeto
        self.projeto_id.choices = [(0, 'Selecione um projeto')] + [(p.id, f"{p.numero} - {p.nome}") for p in Projeto.query.filter_by(status='Ativo').all()]

class ReembolsoForm(FlaskForm):
    titulo = StringField('Título do Reembolso', validators=[DataRequired(), Length(max=200)])
    projeto_id = SelectField('Projeto', coerce=int, validators=[DataRequired()])
    data_solicitacao = DateField('Data da Solicitação', validators=[DataRequired()], default=datetime.date.today)
    descricao = TextAreaField('Descrição/Justificativa', validators=[DataRequired()])
    
    # Categoria gastos com tratamento robusto
    quilometragem = FloatField('Quilometragem', validators=[Optional(), NumberRange(min=0)], default=0)
    valor_km = FloatField('Valor por KM (R$)', validators=[Optional(), NumberRange(min=0)], default=0)
    alimentacao = FloatField('Alimentação (R$)', validators=[Optional(), NumberRange(min=0)], default=0)
    hospedagem = FloatField('Hospedagem (R$)', validators=[Optional(), NumberRange(min=0)], default=0)
    outros_gastos = FloatField('Outros Gastos (R$)', validators=[Optional(), NumberRange(min=0)], default=0)
    
    status = SelectField('Status', choices=[
        ('Pendente', 'Pendente'),
        ('Aprovado', 'Aprovado'),
        ('Rejeitado', 'Rejeitado'),
        ('Pago', 'Pago')
    ], default='Pendente')
    
    def __init__(self, *args, **kwargs):
        super(ReembolsoForm, self).__init__(*args, **kwargs)
        from models import Projeto
        self.projeto_id.choices = [(0, 'Selecione um projeto')] + [(p.id, f"{p.numero} - {p.nome}") for p in Projeto.query.filter_by(status='Ativo').all()]
    
    def validate(self, extra_validators=None):
        """Validação personalizada para garantir que pelo menos um valor seja preenchido"""
        if not super().validate(extra_validators):
            return False
        
        # Verificar se pelo menos um campo de valor foi preenchido
        valores = [
            self.quilometragem.data or 0,
            self.alimentacao.data or 0,
            self.hospedagem.data or 0,
            self.outros_gastos.data or 0
        ]
        
        if all(v == 0 for v in valores):
            self.quilometragem.errors.append('Pelo menos um valor de gasto deve ser informado.')
            return False
        
        return True

class ConfiguracaoEmailForm(FlaskForm):
    smtp_server = StringField('Servidor SMTP', validators=[DataRequired(), Length(max=255)])
    smtp_port = IntegerField('Porta SMTP', validators=[DataRequired(), NumberRange(min=1, max=65535)])
    smtp_username = StringField('Usuário SMTP', validators=[DataRequired(), Email(), Length(max=255)])
    smtp_password = PasswordField('Senha SMTP', validators=[Optional(), Length(max=255)])
    use_tls = BooleanField('Usar TLS', default=True)
    remetente_nome = StringField('Nome do Remetente', validators=[DataRequired(), Length(max=200)])
    remetente_email = StringField('E-mail do Remetente', validators=[DataRequired(), Email(), Length(max=255)])

# Formulários adicionais que estavam faltando
class VisitaRealizadaForm(FlaskForm):
    data_realizada = DateTimeField('Data da Visita Realizada', validators=[DataRequired()])
    observacoes = TextAreaField('Observações da Visita')
    checklist_items = TextAreaField('Itens Verificados')

class FotoRelatorioForm(FlaskForm):
    legenda = StringField('Legenda da Foto', validators=[Optional(), Length(max=500)])
    categoria = SelectField('Categoria', choices=[
        ('Torre 1', 'Torre 1'),
        ('Torre 2', 'Torre 2'),
        ('Área Comum', 'Área Comum'),
        ('Piscina', 'Piscina')
    ], default='Torre 1')

class LegendaPredefinidaForm(FlaskForm):
    texto = StringField('Texto da Legenda', validators=[DataRequired(), Length(max=500)])
    categoria = SelectField('Categoria', choices=[
        ('Torre 1', 'Torre 1'),
        ('Torre 2', 'Torre 2'),
        ('Área Comum', 'Área Comum'),
        ('Piscina', 'Piscina')
    ], default='Torre 1', validators=[DataRequired()])
    ativo = BooleanField('Ativo', default=True)