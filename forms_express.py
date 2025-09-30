from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField, FloatField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Optional, Length

class RelatorioExpressForm(FlaskForm):
    """
    Formulário para Relatório Express - replica exatamente o relatório padrão
    mas com dados da empresa ao invés de projeto
    """
    
    # Dados da Empresa (substitui seleção de projeto)
    empresa_nome = StringField('Nome da Empresa', 
                              validators=[DataRequired(), Length(max=200)],
                              render_kw={'placeholder': 'Nome completo da empresa'})
    
    empresa_endereco = TextAreaField('Endereço da Empresa', 
                                   validators=[Optional()],
                                   render_kw={'rows': 2, 'placeholder': 'Endereço completo da empresa'})
    
    empresa_telefone = StringField('Telefone da Empresa', 
                                  validators=[Optional(), Length(max=20)],
                                  render_kw={'placeholder': '(00) 00000-0000'})
    
    empresa_email = StringField('E-mail da Empresa', 
                               validators=[Optional(), Email(), Length(max=120)],
                               render_kw={'placeholder': 'contato@empresa.com'})
    
    empresa_responsavel = StringField('Responsável da Empresa', 
                                    validators=[Optional(), Length(max=200)],
                                    render_kw={'placeholder': 'Nome do responsável'})
    
    # Dados da Visita (idênticos ao relatório padrão)
    data_visita = DateField('Data da Visita', validators=[DataRequired()])
    
    periodo_inicio = TimeField('Período - Início', validators=[Optional()])
    periodo_fim = TimeField('Período - Fim', validators=[Optional()])
    
    condicoes_climaticas = SelectField('Condições Climáticas',
                                     choices=[
                                         ('', 'Selecione...'),
                                         ('Ensolarado', 'Ensolarado'),
                                         ('Nublado', 'Nublado'),
                                         ('Chuvoso', 'Chuvoso'),
                                         ('Parcialmente nublado', 'Parcialmente nublado'),
                                         ('Tempestade', 'Tempestade'),
                                         ('Neblina', 'Neblina')
                                     ],
                                     validators=[Optional()])
    
    temperatura = StringField('Temperatura', 
                            validators=[Optional(), Length(max=50)],
                            render_kw={'placeholder': 'Ex: 25°C'})
    
    # Localização da visita
    endereco_visita = TextAreaField('Endereço do Local da Visita', 
                                   validators=[Optional()],
                                   render_kw={'rows': 2, 'placeholder': 'Endereço onde foi realizada a visita'})
    
    latitude = HiddenField()
    longitude = HiddenField()
    
    # Observações e relatório (idênticos ao padrão)
    observacoes_gerais = TextAreaField('Observações Gerais', 
                                     validators=[Optional()],
                                     render_kw={'rows': 4, 'placeholder': 'Observações gerais sobre a visita'})
    
    pendencias = TextAreaField('Pendências', 
                             validators=[Optional()],
                             render_kw={'rows': 3, 'placeholder': 'Pendências identificadas'})
    
    recomendacoes = TextAreaField('Recomendações', 
                                validators=[Optional()],
                                render_kw={'rows': 3, 'placeholder': 'Recomendações técnicas'})
    
    # Checklist (campo oculto para armazenar dados JSON)
    checklist_completo = HiddenField('Checklist Completo')
    
    # Participantes da visita
    participantes = SelectMultipleField('Funcionários Participantes', coerce=int, validators=[Optional()])
    
    # Upload de fotos (idêntico ao padrão)
    fotos = MultipleFileField('Fotos', 
                             validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG e PNG são permitidas.')],
                             render_kw={'accept': 'image/*', 'multiple': True})
    
    def __init__(self, *args, **kwargs):
        super(RelatorioExpressForm, self).__init__(*args, **kwargs)
        from models import User
        
        # Carregar usuários ativos para seleção de participantes
        usuarios_ativos = User.query.filter_by(ativo=True).all()
        self.participantes.choices = [(u.id, f"{u.nome_completo} ({u.cargo})") for u in usuarios_ativos]

class FotoExpressForm(FlaskForm):
    """Formulário para edição individual de fotos do relatório express"""
    
    titulo = StringField('Título da Foto', 
                        validators=[Optional(), Length(max=500)],
                        render_kw={'placeholder': 'Título da foto'})
    
    legenda = StringField('Legenda', 
                         validators=[Optional(), Length(max=500)],
                         render_kw={'placeholder': 'Legenda da foto'})
    
    descricao = TextAreaField('Descrição', 
                            validators=[Optional()],
                            render_kw={'rows': 3, 'placeholder': 'Descrição detalhada da foto'})
    
    tipo_servico = SelectField('Tipo de Serviço (Categoria)',
                              choices=[('', 'Selecione...')],
                              validators=[Optional()])
    
    def set_categoria_choices(self, projeto_id):
        """Define as escolhas de categoria baseado no projeto"""
        from models import CategoriaObra
        
        categorias = CategoriaObra.query.filter_by(projeto_id=projeto_id).order_by(CategoriaObra.ordem).all()
        
        # Carrega categorias dinâmicas do banco de dados
        if categorias:
            self.tipo_servico.choices = [('', 'Selecione...')] + [
                (c.nome_categoria, c.nome_categoria) for c in categorias
            ]
        else:
            # Projeto sem categorias - lista vazia
            self.tipo_servico.choices = [('', 'Nenhuma categoria cadastrada para este projeto')]

# Alias para compatibilidade com imports existentes
EditarFotoExpressForm = FotoExpressForm