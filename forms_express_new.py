from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, DateField, HiddenField, SelectField
from wtforms.validators import DataRequired, Length, Email, Optional
from datetime import date

class RelatorioExpressForm(FlaskForm):
    """Formulário completo para criação de relatório express"""
    
    # Dados da empresa/obra
    nome_empresa = StringField(
        'Nome da Empresa/Cliente *',
        validators=[
            DataRequired(message='O nome da empresa é obrigatório'),
            Length(max=200, message='Máximo 200 caracteres')
        ],
        render_kw={
            'placeholder': 'Ex: Construtora ABC Ltda',
            'class': 'form-control'
        }
    )
    
    nome_obra = StringField(
        'Nome da Obra/Projeto *',
        validators=[
            DataRequired(message='O nome da obra é obrigatório'),
            Length(max=200, message='Máximo 200 caracteres')
        ],
        render_kw={
            'placeholder': 'Ex: Edifício Residencial Torre A',
            'class': 'form-control'
        }
    )
    
    endereco_obra = TextAreaField(
        'Endereço da Obra *',
        validators=[
            DataRequired(message='O endereço é obrigatório'),
            Length(max=500, message='Máximo 500 caracteres')
        ],
        render_kw={
            'rows': 3,
            'placeholder': 'Endereço completo da obra com CEP',
            'class': 'form-control'
        }
    )
    
    # Dados do relatório
    observacoes = TextAreaField(
        'Observações Gerais *',
        validators=[
            DataRequired(message='As observações são obrigatórias'),
            Length(max=2000, message='Máximo 2000 caracteres')
        ],
        render_kw={
            'rows': 6,
            'placeholder': 'Descreva os itens observados, estado da obra, recomendações...',
            'class': 'form-control'
        }
    )
    
    itens_observados = TextAreaField(
        'Itens Observados/Checklist',
        validators=[
            Optional(),
            Length(max=1000, message='Máximo 1000 caracteres')
        ],
        render_kw={
            'rows': 4,
            'placeholder': 'Liste os principais itens verificados durante a visita',
            'class': 'form-control'
        }
    )
    
    # Assinaturas
    preenchido_por = StringField(
        'Preenchido por *',
        validators=[
            DataRequired(message='Campo obrigatório'),
            Length(max=200, message='Máximo 200 caracteres')
        ],
        render_kw={
            'placeholder': 'Nome do responsável pelo preenchimento',
            'class': 'form-control'
        }
    )
    
    liberado_por = StringField(
        'Liberado por',
        validators=[
            Optional(),
            Length(max=200, message='Máximo 200 caracteres')
        ],
        render_kw={
            'placeholder': 'Nome do responsável pela liberação (opcional)',
            'class': 'form-control'
        }
    )
    
    responsavel_obra = StringField(
        'Responsável da Obra',
        validators=[
            Optional(),
            Length(max=200, message='Máximo 200 caracteres')
        ],
        render_kw={
            'placeholder': 'Nome do responsável técnico da obra (opcional)',
            'class': 'form-control'
        }
    )
    
    data_relatorio = DateField(
        'Data do Relatório *',
        validators=[DataRequired(message='A data é obrigatória')],
        default=date.today,
        render_kw={'class': 'form-control'}
    )

class FotoExpressForm(FlaskForm):
    """Formulário para upload de fotos do relatório express"""
    foto = FileField(
        'Foto *',
        validators=[
            FileRequired('Selecione uma foto'),
            FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG, JPEG ou PNG são permitidas')
        ],
        render_kw={'class': 'form-control', 'accept': 'image/*'}
    )
    
    legenda = StringField(
        'Legenda da Foto *',
        validators=[
            DataRequired(message='A legenda é obrigatória'),
            Length(max=500, message='Máximo 500 caracteres')
        ],
        render_kw={
            'placeholder': 'Descreva o que está sendo mostrado na foto...',
            'class': 'form-control'
        }
    )
    
    categoria = SelectField(
        'Categoria',
        choices=[
            ('Geral', 'Geral'),
            ('Estrutural', 'Estrutural'),
            ('Hidráulica', 'Hidráulica'),
            ('Elétrica', 'Elétrica'),
            ('Acabamentos', 'Acabamentos'),
            ('Segurança', 'Segurança'),
            ('Fachada', 'Fachada'),
            ('Impermeabilização', 'Impermeabilização')
        ],
        default='Geral',
        render_kw={'class': 'form-control'}
    )

class EditarFotoExpressForm(FlaskForm):
    """Formulário para editar legenda de foto do relatório express"""
    legenda = StringField(
        'Legenda da Foto *',
        validators=[
            DataRequired(message='A legenda é obrigatória'),
            Length(max=500, message='Máximo 500 caracteres')
        ],
        render_kw={'class': 'form-control'}
    )
    
    categoria = SelectField(
        'Categoria',
        choices=[
            ('Geral', 'Geral'),
            ('Estrutural', 'Estrutural'),
            ('Hidráulica', 'Hidráulica'),
            ('Elétrica', 'Elétrica'),
            ('Acabamentos', 'Acabamentos'),
            ('Segurança', 'Segurança'),
            ('Fachada', 'Fachada'),
            ('Impermeabilização', 'Impermeabilização')
        ],
        render_kw={'class': 'form-control'}
    )
    
    foto_id = HiddenField()

class EnvioEmailExpressForm(FlaskForm):
    """Formulário para envio de relatório express por email"""
    emails_destinatarios = TextAreaField(
        'E-mails dos Destinatários *',
        validators=[
            DataRequired(message='Pelo menos um e-mail é obrigatório'),
            Length(max=1000, message='Máximo 1000 caracteres')
        ],
        render_kw={
            'rows': 3,
            'placeholder': 'email1@exemplo.com, email2@exemplo.com (separados por vírgula)',
            'class': 'form-control'
        }
    )
    
    assunto = StringField(
        'Assunto do E-mail',
        validators=[
            Optional(),
            Length(max=200, message='Máximo 200 caracteres')
        ],
        render_kw={
            'placeholder': 'Se vazio, será gerado automaticamente',
            'class': 'form-control'
        }
    )
    
    mensagem = TextAreaField(
        'Mensagem Adicional',
        validators=[
            Optional(),
            Length(max=1000, message='Máximo 1000 caracteres')
        ],
        render_kw={
            'rows': 4,
            'placeholder': 'Mensagem personalizada para o cliente (opcional)',
            'class': 'form-control'
        }
    )