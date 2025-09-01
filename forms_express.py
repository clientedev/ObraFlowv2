from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from datetime import date

class RelatorioExpressForm(FlaskForm):
    # Dados da empresa/cliente
    nome_empresa = StringField('Nome da Empresa/Cliente', validators=[DataRequired(), Length(max=200)])
    cnpj_empresa = StringField('CNPJ', validators=[Optional(), Length(max=18)])
    endereco_empresa = TextAreaField('Endereço da Empresa', validators=[Optional()])
    cidade_empresa = StringField('Cidade', validators=[Optional(), Length(max=100)])
    estado_empresa = SelectField('Estado', choices=[
        ('', 'Selecione'),
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ], validators=[Optional()])
    cep_empresa = StringField('CEP', validators=[Optional(), Length(max=10)])
    contato_empresa = StringField('Pessoa de Contato', validators=[Optional(), Length(max=200)])
    telefone_empresa = StringField('Telefone', validators=[Optional(), Length(max=20)])
    email_empresa = StringField('E-mail', validators=[Optional(), Email(), Length(max=255)])
    
    # Dados do relatório
    titulo_obra = StringField('Título da Obra/Projeto', validators=[DataRequired(), Length(max=500)])
    endereco_obra = TextAreaField('Endereço da Obra', validators=[Optional()])
    latitude = DecimalField('Latitude', validators=[Optional()], places=6)
    longitude = DecimalField('Longitude', validators=[Optional()], places=6)
    data_visita = DateField('Data da Visita', validators=[DataRequired()], default=date.today)
    responsavel_obra = StringField('Responsável na Obra', validators=[Optional(), Length(max=200)])
    tipo_servico = SelectField('Tipo de Serviço', choices=[
        ('', 'Selecione'),
        ('Inspeção Predial', 'Inspeção Predial'),
        ('Consultoria Técnica', 'Consultoria Técnica'),
        ('Perícia Técnica', 'Perícia Técnica'),
        ('Avaliação Estrutural', 'Avaliação Estrutural'),
        ('Análise de Fachada', 'Análise de Fachada'),
        ('Investigação Patológica', 'Investigação Patológica'),
        ('Acompanhamento de Obra', 'Acompanhamento de Obra'),
        ('Vistoria Técnica', 'Vistoria Técnica'),
        ('Análise de Conformidade', 'Análise de Conformidade'),
        ('Outros', 'Outros')
    ], validators=[Optional()])
    
    # Campos do relatório
    introducao = TextAreaField('Introdução', validators=[Optional()])
    metodologia = TextAreaField('Metodologia', validators=[Optional()])
    itens_observados = TextAreaField('Itens Observados', validators=[Optional()])
    observacoes_gerais = TextAreaField('Observações Gerais', validators=[Optional()])
    conclusoes = TextAreaField('Conclusões', validators=[Optional()])
    recomendacoes = TextAreaField('Recomendações', validators=[Optional()])

class FotoExpressForm(FlaskForm):
    foto = FileField('Foto', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas arquivos de imagem!')
    ])
    titulo = StringField('Título da Foto', validators=[Optional(), Length(max=500)])
    legenda = StringField('Legenda', validators=[Optional(), Length(max=500)])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    tipo_servico = SelectField('Categoria', choices=[
        ('Geral', 'Geral'),
        ('Estrutural', 'Estrutural'),
        ('Hidráulica', 'Hidráulica'),
        ('Elétrica', 'Elétrica'),
        ('Acabamentos', 'Acabamentos'),
        ('Segurança', 'Segurança'),
        ('Fachada', 'Fachada'),
        ('Impermeabilização', 'Impermeabilização'),
        ('Problema', 'Problema'),
        ('Vista Geral', 'Vista Geral')
    ], default='Geral')

class EditarFotoExpressForm(FlaskForm):
    titulo = StringField('Título da Foto', validators=[Optional(), Length(max=500)])
    legenda = StringField('Legenda', validators=[Optional(), Length(max=500)])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    tipo_servico = SelectField('Categoria', choices=[
        ('Geral', 'Geral'),
        ('Estrutural', 'Estrutural'),
        ('Hidráulica', 'Hidráulica'),
        ('Elétrica', 'Elétrica'),
        ('Acabamentos', 'Acabamentos'),
        ('Segurança', 'Segurança'),
        ('Fachada', 'Fachada'),
        ('Impermeabilização', 'Impermeabilização'),
        ('Problema', 'Problema'),
        ('Vista Geral', 'Vista Geral')
    ], default='Geral')
    anotacoes_dados = HiddenField('Dados das Anotações')

class EnvioEmailExpressForm(FlaskForm):
    destinatarios = TextAreaField('E-mails dos Destinatários', validators=[DataRequired()], 
                                 description='Digite os e-mails separados por vírgula ou quebra de linha')
    cc = TextAreaField('CC (Cópia)', validators=[Optional()],
                      description='E-mails para receber cópia (opcional)')
    bcc = TextAreaField('CCO (Cópia Oculta)', validators=[Optional()],
                       description='E-mails para receber cópia oculta (opcional)')
    assunto = StringField('Assunto', validators=[DataRequired(), Length(max=500)],
                         default='Relatório Express - {data}')
    mensagem = TextAreaField('Mensagem', validators=[Optional()],
                            default="""Prezado(a),

Segue em anexo o relatório técnico conforme solicitado.

Em caso de dúvidas, favor entrar em contato conosco.

Atenciosamente,
Equipe ELP Consultoria e Engenharia
Engenharia Civil & Fachadas""")

    def validate_destinatarios(self, field):
        if not field.data.strip():
            raise ValidationError('É necessário informar pelo menos um destinatário.')
        
        emails = [email.strip() for email in field.data.replace('\n', ',').split(',') if email.strip()]
        if not emails:
            raise ValidationError('É necessário informar pelo menos um e-mail válido.')
        
        # Validação básica de formato de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in emails:
            if not re.match(email_pattern, email):
                raise ValidationError(f'E-mail inválido: {email}')