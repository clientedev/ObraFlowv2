from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField, FloatField, HiddenField
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
    
    # Upload de fotos (idêntico ao padrão)
    fotos = MultipleFileField('Fotos', 
                             validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG e PNG são permitidas.')],
                             render_kw={'accept': 'image/*', 'multiple': True})

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
    
    tipo_servico = SelectField('Tipo de Serviço',
                              choices=[
                                  ('', 'Selecione...'),
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
                              ],
                              validators=[Optional()])

# Alias para compatibilidade com imports existentes
EditarFotoExpressForm = FotoExpressForm