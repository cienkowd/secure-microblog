# Secure Microblog

> Microblog with TOTP 2FA, account lockout, rate limiting, CSP and HMAC-signed posts.

A web application for publishing short public messages whose authorship can be verified. The focus of the project is security: protecting user accounts and defending against common web attacks.

## Tech stack

**Backend**
- Python 3, Flask
- Flask-SQLAlchemy (ORM), Flask-Migrate / Alembic (migrations)
- Flask-WTF (forms, CSRF protection)
- Flask-Bcrypt (password hashing)
- Flask-Login (sessions)
- Flask-Mail (password reset and new-device e-mails)
- Flask-Limiter (rate limiting)
- PyOTP (TOTP two-factor authentication)
- Markdown + Bleach (message formatting and HTML sanitization)
- python-dotenv (configuration)

**Frontend:** HTML5, CSS3

**Infrastructure:** Nginx (TLS termination, reverse proxy), Docker, Docker Compose

## Features

**Account security**
- Registration and login
- Two-factor authentication (TOTP)
- Strong password policy on registration and password change
- Account lockout after too many failed login attempts (per IP)
- Login rate limiting (5 attempts per minute)
- Delayed server response on failed login to slow down brute-force attacks
- New-device login detection with e-mail notification
- Password change confirmed with 2FA
- Password reset with time-limited tokens

**Publishing and verifying messages**
- Messages with basic Markdown formatting
- Messages signed with HMAC-SHA256 using a per-user secret key, so authorship can be verified
- Signature verification status shown next to each message
- User profile page with the user's public messages
- Public profiles visible to all logged-in users

**Protection against attacks**
- CSRF protection (Flask-WTF)
- Message content sanitized before rendering (XSS protection, Bleach)
- Content-Security-Policy headers
- Nginx version header disabled (`server_tokens off`)
- Honeypot fields in forms against bots
- Server-side validation of all input

**Deployment**
- Application packaged as a Docker image
- Docker Compose setup running the app behind Nginx with HTTPS

## Requirements

- Docker and Docker Compose
- Python 3.x (for local development without Docker)

## Running

### With Docker Compose (recommended)

1. **Clone the repository:**
    ```bash
    git clone https://github.com/cienkowd/secure-microblog.git
    cd secure-microblog
    ```

2. **Create `.env` from `.env.example` and fill in the values** (`SECRET_KEY`, database URI, mail server credentials):
    ```bash
    cp .env.example .env
    ```

3. **Generate a TLS certificate for Nginx** (see [`certs/README.md`](certs/README.md)).

4. **Start the application:**
    ```bash
    docker-compose up --build
    ```

5. **Open `https://localhost`** (`http://localhost` redirects to HTTPS).

### Local development (without Docker)

1. **Clone the repository** (as above).

2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate     # Windows
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Create `.env` from `.env.example`** (as above).

5. **Apply database migrations:**
    ```bash
    flask db upgrade
    ```

6. **Run the app:**
    ```bash
    flask run
    ```

7. **Open `http://127.0.0.1:5000/`**

## Configuration

The app is configured with environment variables from `.env`:

- `SECRET_KEY` – Flask secret key used for sessions and CSRF tokens
- `SQLALCHEMY_DATABASE_URI` – database URI (e.g. `sqlite:///secure-app.db`)
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD` – SMTP server used for password resets and notifications

## Known limitations

- The TOTP setup QR code is saved as an image under `app/static/qrcodes/`, which is publicly served. It should be rendered inline (e.g. as a base64 data URI) instead of being written to disk.
- No automated tests yet.

## Possible extensions

- Editing and deleting one's own messages
- Comments under messages
- More Markdown formatting options
- Unit and integration tests
- Security event logging and monitoring

---

Built as coursework at Applied Computer Science, Warsaw University of Technology. The user interface is in Polish.
