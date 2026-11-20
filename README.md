# Secure Microblog

> Microblog with TOTP 2FA, account lockout, rate limiting, CSP and HMAC-signed posts. Flask, SQLAlchemy, Nginx, Docker.

## Opis projektu

Celem projektu jest stworzenie bezpiecznej aplikacji internetowej umożliwiającej użytkownikom publikowanie krótkich wiadomości publicznych z możliwością weryfikacji autorstwa. Aplikacja kładzie duży nacisk na bezpieczeństwo danych użytkowników oraz ochronę przed typowymi atakami internetowymi.

## Technologie użyte

*   **Backend:**
    *   Python 3
    *   Flask - mikroframework webowy
    *   Flask-SQLAlchemy - ORM dla baz danych SQL
    *   Flask-Migrate - migracje bazy danych
    *   Flask-WTF - obsługa formularzy i ochrona CSRF
    *   Flask-Bcrypt - haszowanie haseł
    *   Flask-Login - zarządzanie sesjami użytkowników
    *   Flask-Mail - obsługa wysyłki e-maili
    *   Flask-Limiter - ograniczanie liczby żądań
    *   PyOTP - obsługa TOTP (Two-Factor Authentication)
    *   Alembic - narzędzie do migracji bazy danych
    *   Markdown - formatowanie wiadomości
    *   Bleach - sanityzacja HTML
    *   dotenv - zarządzanie zmiennymi środowiskowymi
    *   Docker, Docker Compose - konteneryzacja aplikacji
*   **Frontend:**
    *   HTML5, CSS3
*   **Serwer WWW i Proxy:**
    *   Nginx

## Funkcjonalności aplikacji

*   **Bezpieczeństwo konta użytkownika:**
    *   Rejestracja i logowanie użytkowników.
    *   Autentykacja dwuetapowa (2FA) z wykorzystaniem TOTP.
    *   Wymuszanie silnych haseł podczas rejestracji i zmiany hasła.
    *   Blokada konta po przekroczeniu limitu nieudanych prób logowania.
    *   Ograniczenie liczby prób logowania na minutę (rate limiting).
    *   Opóźnienie odpowiedzi serwera podczas logowania, aby utrudnić ataki brute-force.
    *   Monitorowanie logowania z nowych urządzeń i powiadomienia e-mail.
    *   Możliwość zmiany hasła z dodatkowym potwierdzeniem 2FA.
    *   Mechanizm resetowania hasła z wykorzystaniem tokenów ważnych czasowo.
*   **Publikowanie i weryfikacja wiadomości:**
    *   Publikowanie wiadomości z prostym formatowaniem Markdown.
    *   Podpisywanie wiadomości algorytmem HMAC-SHA256, co umożliwia weryfikację autorstwa.
    *   Wyświetlanie statusu weryfikacji podpisu wiadomości.
    *   Strona profilu użytkownika z listą jego publicznych wiadomości.
    *   Publiczne profile użytkowników dostępne dla wszystkich zalogowanych użytkowników.
*   **Ochrona przed atakami:**
    *   Ochrona przed CSRF (Cross-Site Request Forgery) dzięki Flask-WTF.
    *   Sanityzacja treści wiadomości przed wyświetleniem (ochrona przed XSS) za pomocą Bleach.
    *   Zabezpieczenia Content-Security-Policy (CSP) w nagłówkach HTTP.
    *   Wyłączenie nagłówka `Server` w Nginx.
    *   Honeypot fields w formularzach w celu ochrony przed botami.
    *   Walidacja wszystkich danych wejściowych po stronie serwera.
*   **Konteneryzacja:**
    *   Aplikacja spakowana w kontener Docker.
    *   Konfiguracja Docker Compose ułatwiająca uruchomienie aplikacji wraz z bazą danych i serwerem Nginx.

## Wymagania

*   Docker i Docker Compose zainstalowane na systemie.
*   Python 3.x (zalecane dla środowiska deweloperskiego, ale Docker izoluje aplikację).

## Uruchomienie aplikacji

### Uruchomienie za pomocą Docker Compose (zalecane)

1.  **Sklonuj repozytorium projektu:**
    ```bash
    git clone [ADRES_REPOZYTORIUM]
    cd [NAZWA_FOLDERU_PROJEKTU]
    ```

2.  **Utwórz plik `.env` na podstawie `.env.example` i skonfiguruj zmienne środowiskowe.**

    ```bash
    cp .env.example .env
    # Edytuj plik .env i wprowadź odpowiednie wartości, np. SECRET_KEY, dane bazy danych, dane serwera poczty e-mail.
    nano .env
    ```

3.  **Uruchom aplikację za pomocą Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    Lub użyj skryptu `run-docker.sh`:
    ```bash
    sh run-docker.sh
    ```

4.  **Aplikacja będzie dostępna pod adresem `https://localhost`** (przekierowanie z `http://localhost` jest automatyczne).

### Uruchomienie w środowisku deweloperskim (bez Dockera)

1.  **Sklonuj repozytorium projektu:**
    ```bash
    git clone [ADRES_REPOZYTORIUM]
    cd [NAZWA_FOLDERU_PROJEKTU]
    ```

2.  **Utwórz i aktywuj środowisko wirtualne:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate  # Windows
    ```

3.  **Zainstaluj zależności z pliku `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Plik `requirements.txt` należy wygenerować poleceniem `pip freeze > requirements.txt` w aktywnym środowisku wirtualnym po zainstalowaniu wymaganych pakietów.)*

4.  **Utwórz plik `.env` na podstawie `.env.example` i skonfiguruj zmienne środowiskowe.**

    ```bash
    cp .env.example .env
    # Edytuj plik .env i wprowadź odpowiednie wartości, np. SECRET_KEY, dane bazy danych, dane serwera poczty e-mail.
    nano .env
    ```

5.  **Uruchom migracje bazy danych:**
    ```bash
    flask db upgrade
    ```

6.  **Uruchom aplikację Flask:**
    ```bash
    flask run
    ```

7.  **Aplikacja będzie dostępna pod adresem `http://127.0.0.1:5000/`**

## Konfiguracja

Konfiguracja aplikacji odbywa się poprzez zmienne środowiskowe zdefiniowane w pliku `.env`. Przykładowe zmienne konfiguracyjne:

*   `SECRET_KEY` - sekretny klucz Flask używany do ochrony przed CSRF i podpisywania sesji.
*   `SQLALCHEMY_DATABASE_URI` - URI bazy danych SQLAlchemy (np. `sqlite:///site.db` dla SQLite).
*   `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD` - konfiguracja serwera poczty e-mail używanego do resetowania haseł i powiadomień.

## Bezpieczeństwo

Aplikacja została zaprojektowana z myślą o bezpieczeństwie. Kluczowe aspekty bezpieczeństwa obejmują:

*   **Bezpieczne przechowywanie haseł:** Użycie `bcrypt` do haszowania haseł.
*   **Autentykacja dwuetapowa:** Wdrożenie TOTP dla dodatkowej warstwy bezpieczeństwa.
*   **Ochrona przed atakami brute-force:** Limity prób logowania i blokady IP.
*   **Ochrona przed XSS i CSRF:** Sanityzacja danych wyjściowych i mechanizmy CSRF.
*   **HTTPS:** Wymuszone bezpieczne połączenie HTTPS dzięki konfiguracji Nginx.
*   **Content Security Policy:** Ograniczenie źródeł zasobów dla przeglądarki.
*   **Honeypots:** Zabezpieczenia przed botami w formularzach.
*   **Regularne migracje bazy danych:** Utrzymanie aktualności schematu bazy danych.

## Dalszy rozwój

*   Dodanie możliwości edycji i usuwania własnych wiadomości.
*   Implementacja systemu komentarzy pod wiadomościami.
*   Rozszerzenie formatowania wiadomości o dodatkowe elementy Markdown.
*   Dodanie testów jednostkowych i integracyjnych.
*   Implementacja monitoringu i logowania zdarzeń bezpieczeństwa.

## Autor

Damian Cienkowski

---