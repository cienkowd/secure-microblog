import os
import pyotp
import qrcode
import time

from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from app.models import User, UserMessage, FailedLoginAttempt
from app.forms import RegistrationForm, LoginForm, MessageForm, RequestResetForm, ResetPasswordForm, Verify2FAForm, \
    Setup2FAForm, ChangePasswordForm
from app import db, bcrypt, mail
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError

routes = Blueprint('routes', __name__)
limiter = Limiter(key_func=get_remote_address)

MAX_FAILED_LOGINS = 5
LOCK_TIME_MINUTES = 15


def require_2fa(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_2fa_verified:
            if not session.get('2fa_verified'):
                flash('Musisz zweryfikować swoją tożsamość 2FA.', 'warning')
                return redirect(url_for('routes.verify_2fa'))
        return func(*args, **kwargs)
    return wrapper


def get_device_info():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Nieznane urządzenie')
    return {"ip": ip, "user_agent": user_agent}


@routes.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            totp_secret = pyotp.random_base32()  # Generowanie klucza dla TOTP
            user = User(username=form.username.data, email=form.email.data,
                        password_hash=hashed_password, totp_secret=totp_secret)
            db.session.add(user)
            db.session.commit()
            flash('Twoje konto zostało utworzone!', 'success')
            return redirect(url_for('routes.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Ten adres email jest już używany. Proszę użyć innego.', 'danger')
    return render_template('register.html', form=form)


@routes.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))

    form = LoginForm()
    ip_address = request.remote_addr
    failed_attempt = FailedLoginAttempt.query.filter_by(ip_address=ip_address).first()

    if not failed_attempt:
        failed_attempt = FailedLoginAttempt(ip_address=ip_address, attempts=0)
        db.session.add(failed_attempt)
        db.session.commit()

    if failed_attempt.locked_until and failed_attempt.locked_until > datetime.utcnow():
        flash(f'Twoje IP jest zablokowane. Spróbuj ponownie po {failed_attempt.locked_until}.', 'danger')
        return render_template('login.html', form=form)

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            device_info = get_device_info()
            known_devices = user.get_known_devices()
            failed_attempt.attempts = 0

            if device_info not in known_devices:
                flash("Zalogowano z nowego urządzenia. Wysłano powiadomienie e-mail.", "warning")
                send_new_device_email(user, device_info)
                user.add_known_device(device_info)
                db.session.commit()

            login_user(user)

            if user.is_2fa_verified:
                return redirect(url_for('routes.verify_2fa'))

            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('routes.home'))

        else:
            time.sleep(1)
            failed_attempt.attempts += 1
            if failed_attempt.attempts >= MAX_FAILED_LOGINS:
                failed_attempt.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_TIME_MINUTES)
                flash(f'Twoje IP zostało zablokowane na {LOCK_TIME_MINUTES} minut.', 'danger')
            else:
                flash('Nieprawidłowy email lub hasło.', 'danger')
            db.session.commit()

    return render_template('login.html', form=form)


@routes.route('/')
def welcome():
    return render_template('welcome.html', hide_sidebar=True)


@routes.route('/logout')
def logout():
    session.pop('2fa_verified', None)
    logout_user()
    flash('Zostałeś wylogowany.', 'success')
    return redirect(url_for('routes.welcome'))


@routes.route('/home', methods=['GET', 'POST'])
@login_required
@require_2fa
def home():
    messages = UserMessage.query.order_by(UserMessage.created_at.desc()).all()
    form = MessageForm()

    if form.validate_on_submit():
        message = UserMessage(content=form.content.data, user_id=current_user.id)
        message.generate_signature(current_user)
        db.session.add(message)
        db.session.commit()
        flash('Twoja wiadomość została opublikowana!', 'success')
        return redirect(url_for('routes.home'))

    return render_template('mainpage.html', form=form, messages=messages)


@routes.route('/profile', methods=['GET'])
@login_required
@require_2fa
def profile():
    user = current_user
    messages = UserMessage.query.filter_by(user_id=user.id).order_by(UserMessage.created_at.desc()).all()
    return render_template('profile.html', user=user, messages=messages)


@routes.route('/setup_2fa', methods=['GET', 'POST'])
@login_required
@require_2fa
def setup_2fa():
    if current_user.is_2fa_verified:
        flash('Masz już ustawioną weryfikację dwuetapową.', 'info')
        return redirect(url_for('routes.home'))

    form = Setup2FAForm()

    qr_code_dir = os.path.join('app', 'static', 'qrcodes')
    if not os.path.exists(qr_code_dir):
        os.makedirs(qr_code_dir)

    qr_code_filename = f"{current_user.id}_qrcode.png"
    qr_code_path = os.path.join(qr_code_dir, qr_code_filename)

    qr_code_uri = current_user.get_totp_uri()
    qr_code = qrcode.make(qr_code_uri)
    qr_code.save(qr_code_path)

    if request.method == 'POST' and form.validate_on_submit():
        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(form.token.data):
            current_user.is_2fa_verified = True
            db.session.commit()
            flash('Dwuetapowa weryfikacja została pomyślnie skonfigurowana.', 'success')
            return redirect(url_for('routes.home'))
        else:
            flash('Nieprawidłowy kod weryfikacyjny. Spróbuj ponownie.', 'danger')

    return render_template('setup_2fa.html', qr_code_filename=f'qrcodes/{qr_code_filename}', form=form)


@routes.route('/verify_2fa', methods=['GET', 'POST'])
@login_required
def verify_2fa():
    if current_user.is_2fa_verified:
        if session.get('2fa_verified'):
            return redirect(url_for('routes.home'))

    form = Verify2FAForm()
    if form.validate_on_submit():
        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(form.token.data):
            session['2fa_verified'] = True
            flash('Weryfikacja 2FA zakończona pomyślnie!', 'success')
            return redirect(url_for('routes.home'))
        else:
            flash('Nieprawidłowy kod 2FA. Spróbuj ponownie.', 'danger')

    return render_template('verify_2fa.html', form=form)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Żądanie zresetowania hasła',
                  sender='your_email@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Aby zresetować hasło, odwiedź poniższy link:
{url_for('routes.reset_password', token=token, _external=True)}

Jeśli nie prosiłeś o resetowanie hasła, zignoruj tę wiadomość.
'''
    mail.send(msg)


def send_new_device_email(user, device_info):
    msg = Message(
        subject='Logowanie z nowego urządzenia',
        sender='no-reply@yourapp.com',
        recipients=[user.email]
    )
    msg.body = f"""Cześć {user.username},

Zalogowano do Twojego konta z nowego urządzenia:
Adres IP: {device_info['ip']}
Przeglądarka: {device_info['user_agent']}

Jeśli to nie Ty, zalogowałeś/aś się, prosimy o zmianę hasła i skontaktowanie się z naszym wsparciem technicznym.

Pozdrawiamy,
Zespół X Secure App
"""
    mail.send(msg)


@routes.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))

    form = RequestResetForm()

    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('Na Twój adres email wysłano instrukcje do resetowania hasła.', 'info')
            return redirect(url_for('routes.login'))
        else:
            flash('Nie znaleziono użytkownika z podanym adresem email.', 'danger')

    return render_template('reset_request.html', form=form)


@routes.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('routes.home'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Nieprawidłowy lub wygasły token.', 'warning')
        return redirect(url_for('routes.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password_hash = hashed_password
        db.session.commit()
        flash('Twoje hasło zostało zaktualizowane! Możesz się teraz zalogować.', 'success')
        return redirect(url_for('routes.login'))
    return render_template('reset_password.html', form=form)


@routes.route('/user/<string:username>')
@login_required
@require_2fa
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    messages = UserMessage.query.filter_by(user_id=user.id).order_by(UserMessage.created_at.desc()).all()
    return render_template('public_profile.html', user=user, messages=messages)


@routes.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@routes.errorhandler(500)
def internal_server_error(e):
    form = MessageForm()
    return render_template('500.html', form=form), 500


@routes.route('/change_password', methods=['GET', 'POST'])
@login_required
@require_2fa
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not bcrypt.check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Obecne hasło jest nieprawidłowe.', 'danger')
            return redirect(url_for('routes.change_password'))

        session['new_password'] = form.password.data

        return redirect(url_for('routes.confirm_change_password'))

    return render_template('change_password.html', form=form)


@routes.route('/confirm_change_password', methods=['GET', 'POST'])
@login_required
@require_2fa
def confirm_change_password():
    form = Verify2FAForm()

    if not current_user.is_2fa_verified:
        flash('Nie masz aktywnego 2FA. Zmiana hasła wymaga skonfigurowania 2FA.', 'danger')
        return redirect(url_for('routes.setup_2fa'))

    if 'new_password' not in session:
        flash('Nieprawidłowe dane. Rozpocznij proces zmiany hasła od początku.', 'danger')
        return redirect(url_for('routes.change_password'))

    if form.validate_on_submit():
        totp = pyotp.TOTP(current_user.totp_secret)
        token = form.token.data  # Pobierz kod 2FA z formularza

        if not totp.verify(token):
            flash('Kod 2FA jest nieprawidłowy. Spróbuj ponownie.', 'danger')
            return render_template('confirm_change_password.html', form=form)

        hashed_password = bcrypt.generate_password_hash(session['new_password']).decode('utf-8')
        current_user.password_hash = hashed_password
        db.session.commit()
        session.pop('new_password', None)
        flash('Twoje hasło zostało pomyślnie zmienione!', 'success')
        return redirect(url_for('routes.home'))

    return render_template('confirm_change_password.html', form=form)


