from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class HangmanForm(FlaskForm):
    guess = StringField('Guess a letter', validators=[DataRequired()])
    submit = SubmitField('Submit')