import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User


def validate_password_strength(form, field):
    password = field.data
    if (len(password) < 8 or
            not re.search(r'[A-Z]', password) or
            not re.search(r'[0-9]', password) or
            not re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        raise ValidationError("Hasło musi mieć co najmniej 8 znaków, zawierać wielką literę, cyfrę i znak specjalny.")


def validate_content(form, field):
    forbidden_patterns = ["<script>", "javascript:", "onerror=", "onload="]
    for pattern in forbidden_patterns:
        if pattern in field.data.lower():
            raise ValidationError("Wiadomość zawiera niedozwolone elementy!")


class RegistrationForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired(message="To pole jest wymagane."), Length(min=4, max=25, message="Nazwa użytkownika musi mieć od 4 do 25 znaków.")])
    email = StringField('Adres email', validators=[DataRequired(message="To pole jest wymagane."), Email(message="Proszę podać prawidłowy adres email.")])
    password = PasswordField('Hasło', validators=[DataRequired(message="To pole jest wymagane."), validate_password_strength])
    confirm_password = PasswordField('Potwierdź hasło', validators=[DataRequired(message="To pole jest wymagane."), EqualTo('password', message="Hasła muszą być identyczne.")])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Zarejestruj')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ten adres email jest już używany. Proszę użyć innego.')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ta nazwa użytkownika jest już zajęta. Proszę wybrać inną.')

    def validate_honeypot(self, field):
        if field.data:
            raise ValidationError('Boty nie są mile widziane!')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Zaloguj')


class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(), validate_content])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Opublikuj')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Zresetuj hasło')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Zresetuj hasło')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Obecne hasło', validators=[DataRequired()])
    password = PasswordField('Nowe hasło', validators=[DataRequired(), validate_password_strength, EqualTo('confirm_password', message='Hasła muszą się zgadzać.')])
    confirm_password = PasswordField('Potwierdź nowe hasło', validators=[DataRequired()])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Zmień hasło')


class Verify2FAForm(FlaskForm):
    token = StringField('Kod weryfikacyjny', validators=[DataRequired(), Length(6, 6)])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Zatwierdź')


class Setup2FAForm(FlaskForm):
    token = StringField('Kod weryfikacyjny', validators=[DataRequired()])
    honeypot = StringField('Nie wypełniaj tego pola')
    submit = SubmitField('Zakończ konfigurację')
