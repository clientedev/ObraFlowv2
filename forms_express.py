"""
Formulários para sistema de Relatório Express
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import TextAreaField, StringField, HiddenField
from wtforms.validators import DataRequired, Length, Optional

class RelatorioExpressForm(FlaskForm):
    """Formulário para criação de relatório express"""
    observacoes = TextAreaField(
        'Observações Rápidas',
        validators=[DataRequired(message='As observações são obrigatórias'), 
                   Length(max=2000, message='Máximo 2000 caracteres')],
        render_kw={
            'rows': 6,
            'placeholder': 'Digite suas observações sobre a visita/obra...'
        }
    )

class FotoExpressForm(FlaskForm):
    """Formulário para upload de fotos do relatório express"""
    foto = FileField(
        'Foto',
        validators=[
            FileRequired('Selecione uma foto'),
            FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG, JPEG ou PNG são permitidas')
        ]
    )
    legenda = StringField(
        'Legenda da Foto',
        validators=[
            DataRequired(message='A legenda é obrigatória'),
            Length(max=500, message='Máximo 500 caracteres')
        ],
        render_kw={
            'placeholder': 'Descreva brevemente a foto...'
        }
    )

class EditarFotoExpressForm(FlaskForm):
    """Formulário para editar legenda de foto do relatório express"""
    legenda = StringField(
        'Legenda da Foto',
        validators=[
            DataRequired(message='A legenda é obrigatória'),
            Length(max=500, message='Máximo 500 caracteres')
        ]
    )
    foto_id = HiddenField()