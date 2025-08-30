from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional

class EmailClienteForm(FlaskForm):
    """Formulário para cadastro e edição de e-mails de clientes"""
    email = StringField(
        'E-mail',
        validators=[DataRequired(message='E-mail é obrigatório'), 
                   Email(message='E-mail inválido'), 
                   Length(max=120, message='E-mail muito longo')]
    )
    nome_contato = StringField(
        'Nome do Contato',
        validators=[Optional(), Length(max=200, message='Nome muito longo')]
    )
    receber_relatorio = BooleanField(
        'Receber Relatórios',
        default=True
    )
    projeto_id = HiddenField()

class EmailMultiploForm(FlaskForm):
    """Formulário para cadastrar múltiplos e-mails de uma vez"""
    emails_text = StringField(
        'E-mails (separados por vírgula ou quebra de linha)',
        validators=[DataRequired(message='Pelo menos um e-mail é obrigatório')],
        render_kw={'rows': 3}
    )
    receber_relatorio_padrao = BooleanField(
        'Todos devem receber relatórios por padrão',
        default=True
    )
    projeto_id = HiddenField()