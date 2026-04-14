from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class SearchForm(FlaskForm):
    search = StringField('Chercher un artiste ou un titre', validators=[DataRequired()])
    submit = SubmitField('Rechercher')

class ReviewForm(FlaskForm):
    content = TextAreaField('Votre avis', validators=[DataRequired(), Length(min=5, max=500)])
    rating = IntegerField('Note (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Publier')

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

class TrackForm(FlaskForm):
    title = StringField('Titre de la chanson', validators=[DataRequired(message="Le titre est obligatoire.")])
    artist = StringField('Artiste', validators=[DataRequired(message="Le nom de l'artiste est obligatoire.")])
    # On utilise StringField car le Deezer ID est souvent traité comme une chaîne dans ton code
    deezer_id = StringField('Deezer ID (Numérique)', validators=[DataRequired(message="L'ID Deezer est nécessaire pour le lecteur.")])
    cover_medium = StringField('URL de la pochette (Medium)', validators=[Length(max=500)])
    cover_big = StringField('URL de la pochette (Large)', validators=[Length(max=500)])
    preview = StringField('URL de l\'extrait MP3', validators=[Length(max=500)])
    
    submit = SubmitField('Enregistrer')