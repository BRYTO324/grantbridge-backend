#!/usr/bin/env bash
# Render build script
set -o errexit

echo "==> Python version: $(python --version)"

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Checking DATABASE_URL..."
if [ -z "$DATABASE_URL" ]; then
  echo "WARNING: DATABASE_URL is not set — using SQLite fallback"
else
  echo "DATABASE_URL is configured (PostgreSQL)"
fi

echo "==> Clearing old static files..."
rm -rf staticfiles/

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Creating superuser (if not exists)..."
python manage.py shell -c "
from apps.users.models import User
import os
email = os.environ.get('ADMIN_EMAIL', 'grantbrigdehq@gmail.com')
password = os.environ.get('ADMIN_PASSWORD', 'GrantBridge@Admin2026')
if not User.objects.filter(email=email).exists():
    u = User.objects.create_superuser(
        email=email, password=password,
        full_name='GrantBridge Admin', role='entrepreneur'
    )
    u.email_verified = True
    u.verification_status = 'verified'
    u.save()
    print(f'Superuser created: {email}')
else:
    print(f'Superuser already exists: {email}')
"

echo "==> Build complete!"
