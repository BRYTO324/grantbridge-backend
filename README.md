# GrantBridge Backend

Django REST Framework backend for the GrantBridge platform — connecting entrepreneurs and funders, with Paystack payment integration.

---

## Tech Stack

- Python 3.11+, Django 5.x, Django REST Framework
- JWT auth via `djangorestframework-simplejwt`
- Paystack for payments
- SQLite (dev) / PostgreSQL (production)
- `djangorestframework-camel-case` — auto converts snake_case ↔ camelCase

---

## Project Structure

```
grantbridge-backend/
├── manage.py
├── .env                    ← your local env vars (never commit this)
├── .env.example            ← template
├── requirements.txt
├── config/
│   ├── settings/
│   │   ├── base.py         ← shared settings
│   │   ├── development.py  ← dev overrides
│   │   └── production.py   ← prod overrides
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── core/               ← shared permissions + exception handler
    ├── users/              ← User model, JWT auth, email verification
    ├── pitches/            ← PitchCard, likes, bookmarks
    ├── offers/             ← FundingOffer (accept/reject flow)
    ├── payments/           ← Paystack integration
    └── progress/           ← WeeklyProgress updates
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
```

Edit `.env` and fill in your values — especially `PAYSTACK_SECRET_KEY` and `PAYSTACK_PUBLIC_KEY`.

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (for Django admin)

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | — |
| `DATABASE_URL` | Database connection URL | `sqlite:///db.sqlite3` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `PAYSTACK_SECRET_KEY` | Paystack secret key (from dashboard) | — |
| `PAYSTACK_PUBLIC_KEY` | Paystack public key (from dashboard) | — |
| `EMAIL_BACKEND` | Django email backend | `console` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | — |
| `EMAIL_HOST_PASSWORD` | SMTP password | — |
| `DEFAULT_FROM_EMAIL` | From address for emails | `GrantBridge <noreply@...>` |
| `FRONTEND_URL` | Frontend base URL (for email links) | `http://localhost:5173` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:5173` |

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register/` | Register new user |
| POST | `/auth/login/` | Login → returns JWT tokens |
| POST | `/auth/logout/` | Blacklist refresh token |
| POST | `/auth/token/refresh/` | Refresh access token |
| POST | `/auth/verify-email/` | Verify email with token |
| POST | `/auth/resend-verification/` | Resend verification email |
| POST | `/auth/forgot-password/` | Request password reset |
| POST | `/auth/reset-password/` | Reset password with token |
| GET | `/auth/me/` | Get current user |
| PATCH | `/auth/me/` | Update profile |

### Verification
| Method | Endpoint | Description |
|---|---|---|
| POST | `/verification/submit/` | Upload KYC documents (multipart) |
| GET | `/verification/status/` | Get verification status |

### Pitches
| Method | Endpoint | Description |
|---|---|---|
| GET | `/pitches/` | List all pitches (public) |
| POST | `/pitches/` | Create pitch (entrepreneur only) |
| GET | `/pitches/:id/` | Get pitch detail with offers |
| PUT | `/pitches/:id/` | Update pitch (owner only) |
| DELETE | `/pitches/:id/` | Delete pitch (owner only) |
| PATCH | `/pitches/:id/like/` | Toggle like |
| PATCH | `/pitches/:id/bookmark/` | Toggle bookmark |

### Offers
| Method | Endpoint | Description |
|---|---|---|
| POST | `/offers/` | Submit funding offer (funder only) |
| PUT | `/offers/:id/` | Accept or reject offer (pitch owner only) |

### Payments
| Method | Endpoint | Description |
|---|---|---|
| POST | `/payments/initialize/` | Initialize Paystack transaction |
| POST | `/payments/verify/` | Verify payment after redirect |
| POST | `/payments/webhook/` | Paystack webhook (server-to-server) |
| GET | `/payments/history/` | Current user's payment history |

### Progress
| Method | Endpoint | Description |
|---|---|---|
| POST | `/progress/` | Submit weekly update (entrepreneur only) |
| GET | `/progress/` | List own progress updates |

---

## Paystack Payment Flow

1. Funder clicks "Fund This Project" on the frontend
2. Frontend calls `POST /payments/initialize/` with `{ pitchId, amount }`
3. Backend creates a pending `Payment` record and calls Paystack API
4. Backend returns `{ authorizationUrl, reference }`
5. Frontend redirects user to `authorizationUrl` (Paystack hosted page)
6. After payment, Paystack redirects back to `FRONTEND_URL/dashboard/funder/payment/callback?reference=...`
7. Frontend calls `POST /payments/verify/` with the `reference`
8. Backend verifies with Paystack, marks payment as success, updates pitch to `funded`

Paystack also sends a webhook to `POST /payments/webhook/` as a backup confirmation.

---

## Django Admin

Access at `http://localhost:8000/admin/` after creating a superuser.

You can:
- View and manage users, verify/reject KYC documents
- View all pitches and manually change funding status
- View all payments and their Paystack references
- View funding offers

---

## Switching to PostgreSQL

Update `.env`:
```
DATABASE_URL=postgres://username:password@localhost:5432/grantbridge
```

Then run:
```bash
pip install psycopg2-binary
python manage.py migrate
```
