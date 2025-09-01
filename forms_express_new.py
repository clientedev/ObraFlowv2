from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, DateField, HiddenField, SelectField
from wtforms.validators import DataRequired, Length, Email, Optional
from datetime import date

# Formulário para dados da empresa (Etapa 1)
class DadosEmpresaExpressForm(FlaskForm):
    """Formulário para dados da empresa - Etapa 1"""
    
    # Dados da empresa
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
    
    cnpj_empresa = StringField(
        'CNPJ da Empresa',
        validators=[
            Optional(),
            Length(max=20, message='Máximo 20 caracteres')
        ],
        render_kw={
            'placeholder': 'XX.XXX.XXX/XXXX-XX',
            'class': 'form-control'
        }
    )
    
    telefone_empresa = StringField(
        'Telefone da Empresa',
        validators=[
            Optional(),
            Length(max=20, message='Máximo 20 caracteres')
        ],
        render_kw={
            'placeholder': '(11) 99999-9999',
            'class': 'form-control'
        }
    )
    
    email_empresa = StringField(
        'E-mail da Empresa',
        validators=[
            Optional(),
            Email(message='E-mail inválido'),
            Length(max=120, message='Máximo 120 caracteres')
        ],
        render_kw={
            'placeholder': 'contato@empresa.com.br',
            'class': 'form-control'
        }
    )
    
    endereco_empresa = TextAreaField(
        'Endereço da Empresa',
        validators=[
            Optional(),
            Length(max=500, message='Máximo 500 caracteres')
        ],
        render_kw={
            'rows': 3,
            'placeholder': 'Endereço completo da empresa',
            'class': 'form-control'
        }
    )
    
    # Dados da obra
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
            DataRequired(message='O endereço da obra é obrigatório'),
            Length(max=500, message='Máximo 500 caracteres')
        ],
        render_kw={
            'rows': 3,
            'placeholder': 'Endereço completo da obra com CEP',
            'class': 'form-control'
        }
    )
    
    tipo_obra = SelectField(
        'Tipo de Obra',
        choices=[
            ('', 'Selecione o tipo'),
            ('Residencial', 'Residencial'),
            ('Comercial', 'Comercial'),
            ('Industrial', 'Industrial'),
            ('Institucional', 'Institucional'),
            ('Infraestrutura', 'Infraestrutura'),
            ('Reforma', 'Reforma'),
            ('Outros', 'Outros')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-control'}
    )
    
    coordenadas_gps = StringField(
        'Coordenadas GPS',
        validators=[
            Optional(),
            Length(max=100, message='Máximo 100 caracteres')
        ],
        render_kw={
            'placeholder': 'Ex: -23.550520, -46.633308',
            'class': 'form-control'
        }
    )

# Formulário para dados do relatório (Etapa 2)
class DadosRelatorioExpressForm(FlaskForm):
    """Formulário para dados do relatório - Etapa 2"""
    
    # Dados gerais do relatório
    titulo_relatorio = StringField(
        'Título do Relatório',
        validators=[
            Optional(),
            Length(max=300, message='Máximo 300 caracteres')
        ],
        render_kw={
            'placeholder': 'Ex: Relatório de Visita Técnica - Estrutura',
            'class': 'form-control'
        }
    )
    
    objetivo_visita = TextAreaField(
        'Objetivo da Visita',
        validators=[
            Optional(),
            Length(max=1000, message='Máximo 1000 caracteres')
        ],
        render_kw={
            'rows': 3,
            'placeholder': 'Descreva o objetivo principal desta visita técnica...',
            'class': 'form-control'
        }
    )
    
    # Observações técnicas
    observacoes = TextAreaField(
        'Observações Gerais *',
        validators=[
            DataRequired(message='As observações são obrigatórias'),
            Length(max=3000, message='Máximo 3000 caracteres')
        ],
        render_kw={
            'rows': 6,
            'placeholder': 'Descreva detalhadamente os aspectos observados durante a visita...',
            'class': 'form-control'
        }
    )
    
    conclusoes = TextAreaField(
        'Conclusões',
        validators=[
            Optional(),
            Length(max=2000, message='Máximo 2000 caracteres')
        ],
        render_kw={
            'rows': 4,
            'placeholder': 'Principais conclusões da visita técnica...',
            'class': 'form-control'
        }
    )
    
    recomendacoes = TextAreaField(
        'Recomendações',
        validators=[
            Optional(),
            Length(max=2000, message='Máximo 2000 caracteres')
        ],
        render_kw={
            'rows': 4,
            'placeholder': 'Recomendações e sugestões para a obra...',
            'class': 'form-control'
        }
    )
    
    # Itens técnicos
    itens_observados = TextAreaField(
        'Itens Observados',
        validators=[
            Optional(),
            Length(max=1500, message='Máximo 1500 caracteres')
        ],
        render_kw={
            'rows': 4,
            'placeholder': 'Liste os principais itens verificados durante a visita...',
            'class': 'form-control'
        }
    )
    
    itens_conformes = TextAreaField(
        'Itens Conformes',
        validators=[
            Optional(),
            Length(max=1500, message='Máximo 1500 caracteres')
        ],
        render_kw={
            'rows': 3,
            'placeholder': 'Itens que estão em conformidade com o projeto/normas...',
            'class': 'form-control'
        }
    )
    
    itens_nao_conformes = TextAreaField(
        'Itens Não Conformes',
        validators=[
            Optional(),
            Length(max=1500, message='Máximo 1500 caracteres')
        ],
        render_kw={
            'rows': 3,
            'placeholder': 'Itens que necessitam correção ou ajuste...',
            'class': 'form-control'
        }
    )
    
    # Dados da visita
    data_visita = DateField(
        'Data da Visita *',
        validators=[DataRequired(message='A data da visita é obrigatória')],
        default=date.today,
        render_kw={'class': 'form-control'}
    )
    
    hora_inicio = StringField(
        'Hora de Início',
        validators=[
            Optional(),
            Length(max=10, message='Máximo 10 caracteres')
        ],
        render_kw={
            'placeholder': 'Ex: 09:00',
            'class': 'form-control'
        }
    )
    
    hora_fim = StringField(
        'Hora de Término',
        validators=[
            Optional(),
            Length(max=10, message='Máximo 10 caracteres')
        ],
        render_kw={
            'placeholder': 'Ex: 12:00',
            'class': 'form-control'
        }
    )
    
    condicoes_climaticas = SelectField(
        'Condições Climáticas',
        choices=[
            ('', 'Selecione'),
            ('Ensolarado', 'Ensolarado'),
            ('Parcialmente nublado', 'Parcialmente nublado'),
            ('Nublado', 'Nublado'),
            ('Chuvoso', 'Chuvoso'),
            ('Ventoso', 'Ventoso')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-control'}
    )
    
    # Responsáveis
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
            'placeholder': 'Nome do responsável pela liberação',
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
            'placeholder': 'Nome do responsável técnico da obra',
            'class': 'form-control'
        }
    )
    
    cargo_responsavel_obra = StringField(
        'Cargo do Responsável',
        validators=[
            Optional(),
            Length(max=100, message='Máximo 100 caracteres')
        ],
        render_kw={
            'placeholder': 'Ex: Engenheiro Civil, Mestre de Obras',
            'class': 'form-control'
        }
    )
    
    data_relatorio = DateField(
        'Data do Relatório *',
        validators=[DataRequired(message='A data do relatório é obrigatória')],
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