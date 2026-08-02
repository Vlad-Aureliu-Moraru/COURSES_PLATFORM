# BaniOnline — Backend API (Django)

API-ul pentru **BaniOnline**: autentificare JWT, cursuri, acces și plăți Stripe.
Deployat în Docker pe VPS, expus la `api.banionline.ro`.

## Cerințe

- Python 3.12 (venv în `backend/.venv`)
- PostgreSQL 16 (sau SQLite în dezvoltare)

## Dezvoltare

```sh
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env     # setează cheile (Stripe, email)
python manage.py migrate
python manage.py runserver
```

Configurația vine din `.env` (vezi `.env.example`). În dezvoltare se folosește
SQLite (`USE_SQLITE=True`); în producție, `DATABASE_URL` / variabile Postgres.

## Teste

```sh
pytest        # 28 de teste (auth, cursuri, plăți/webhook, admin, emailuri)
```

## Aplicații

| Aplicație | Rol |
|---|---|
| `accounts` | User custom (email), autentificare SimpleJWT, throttling |
| `courses` | Course / Lesson / Enrollment, gating acces |
| `payments` | Stripe Checkout + webhook, notificări email |
| `orders` | Structură de comandă (nefolosită în fluxul actual de plată) |
| `health` | Endpoint `/api/v1/health/` pentru monitoring |

## Fluxul plății

1. Clientul autentificat face `POST /api/v1/payments/checkout/`.
2. Backend-ul creează un Stripe Checkout Session (cu taxe automate) și întoarce `checkout_url`.
3. Clientul e redirecționat pe pagina Stripe; după plată revine pe `/success?session_id=…`.
4. Webhook-ul `checkout.session.completed` marchează plata `paid` și acordă accesul la curs.
5. Emailul de confirmare e trimis (console în dev, SMTP Resend în producție).

Cursul este **nerambursabil** — webhook-ul nu gestionează refund-uri.

## Setări de producție

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DEBUG=False`; `ALLOWED_HOSTS=api.banionline.ro`
- Static servit de **WhiteNoise** (`collectstatic` → `/static/`)
- `SECURE_*` + HSTS + CSRF cookies `Secure`
- Gunicorn (4 workers) în Docker; `entrypoint.sh` rulează migrate + collectstatic

Vezi `docker-compose.yml` (db + api) și `backend/Dockerfile`.
