"""
Formulários para sistema de e-mail
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional
from wtforms.widgets import CheckboxInput, ListWidget

class MultiCheckboxField(SelectMultipleField):
    """Campo personalizado para múltiplas seleções com checkboxes"""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class ConfiguracaoEmailForm(FlaskForm):
    """Formulário para configuração de e-mail"""
    nome_configuracao = StringField('Nome da Configuração', validators=[DataRequired(), Length(max=100)])
    servidor_smtp = StringField('Servidor SMTP', validators=[DataRequired(), Length(max=255)])
    porta_smtp = IntegerField('Porta SMTP', validators=[DataRequired()])
    use_tls = BooleanField('Usar TLS', default=True)
    use_ssl = BooleanField('Usar SSL', default=False)
    email_remetente = StringField('E-mail Remetente', validators=[DataRequired(), Email(), Length(max=255)])
    nome_remetente = StringField('Nome Remetente', validators=[DataRequired(), Length(max=200)])
    template_assunto = StringField('Template de Assunto', validators=[Length(max=500)])
    template_corpo = TextAreaField('Template do Corpo do E-mail')
    ativo = BooleanField('Configuração Ativa', default=True)

class EnvioEmailForm(FlaskForm):
    """Formulário para envio de e-mail"""
    destinatarios = MultiCheckboxField('Destinatários', coerce=str, validators=[DataRequired()])
    cc_emails = TextAreaField('CC (Cópia)', validators=[Optional()], 
                             description='Um e-mail por linha ou separados por vírgula')
    bcc_emails = TextAreaField('BCC (Cópia Oculta)', validators=[Optional()],
                              description='Um e-mail por linha ou separados por vírgula')
    assunto_personalizado = StringField('Assunto (Personalizar)', validators=[Optional(), Length(max=500)])
    corpo_personalizado = TextAreaField('Mensagem (Personalizar)', validators=[Optional()],
                                       description='Deixe em branco para usar o template padrão')
    preview_mode = BooleanField('Visualizar antes de enviar', default=True)