import json
import os
import pyotp
import hashlib
import hmac

from app import db
from flask_login import UserMixin
from app import login_manager
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from markdown import markdown
from sqlalchemy.orm import relationship
from datetime import datetime
from markupsafe import Markup
from bleach import clean


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    totp_secret = db.Column(db.String(16), nullable=True, default=None)
    is_2fa_verified = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(120), nullable=False, default='default_profile.png')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reset_token_timestamp = db.Column(db.DateTime, nullable=True, default=None)
    failed_logins = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True, default=None)
    known_devices = db.Column(db.Text, nullable=True, default="[]")
    private_key = db.Column(db.String(64), nullable=False, default=lambda: os.urandom(32).hex())

    def verify_signature(self, message_content, signature):
        expected_signature = hmac.new(self.private_key.encode(), message_content.encode(), hashlib.sha256).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def get_known_devices(self):
        return json.loads(self.known_devices or "[]")

    def add_known_device(self, device):
        devices = self.get_known_devices()
        devices.append(device)
        self.known_devices = json.dumps(devices)

    def get_totp_uri(self):
        if self.totp_secret:
            return pyotp.TOTP(self.totp_secret).provisioning_uri(
                name=self.email, issuer_name="X Secure App"
            )
        return None

    def get_reset_token(self, expires_sec=1800):
        self.reset_token_timestamp = datetime.utcnow()
        db.session.commit()

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id, 'timestamp': datetime.utcnow().timestamp()}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='password-reset-salt', max_age=1800)
            user = User.query.get(data['user_id'])

            if not user:
                return None

            if user.reset_token_timestamp and user.reset_token_timestamp.timestamp() > data.get('timestamp'):
                return None

        except Exception as e:
            print(f"Error verifying token: {e}")
            return None
        return user

    def sign_message(self, message_content):
        return hmac.new(self.private_key.encode(), message_content.encode(), hashlib.sha256).hexdigest()

    def verify_message_signature(self, message_content, signature):
        expected_signature = self.sign_message(message_content)
        return hmac.compare_digest(expected_signature, signature)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class UserMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    user = relationship('User', backref='messages', lazy=True)
    signature = db.Column(db.String(64), nullable=False)

    def generate_signature(self, user):
        self.signature = user.sign_message(self.content)

    def __repr__(self):
        return f"UserMessage('{self.content}', '{self.created_at}')"

    def render_content(self):
        sanitized_content = clean(
            self.content,
            tags=['b', 'i', 'strong', 'em', 'a', 'img'],
            attributes={'a': ['href', 'title'], 'img': ['src', 'alt']},
            protocols=['http', 'https']
        )
        rendered_content = markdown(
            sanitized_content,
            extensions=['fenced_code', 'codehilite', 'tables', 'nl2br']
        )
        return Markup(rendered_content)


class FailedLoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
