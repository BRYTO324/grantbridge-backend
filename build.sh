#!/usr/bin/env bash
# Render build script — runs before the web service starts
set -o errexit

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running migrations..."
python manage.py migrate

echo "==> Creating superuser (if not exists)..."
python manage.py shell -c "
from apps.users.models import User
import os
email = os.environ.get('ADMIN_EMAIL', 'grantbrigdehq@gmail.com')
password = os.environ.get('ADMIN_PASSWORD', 'GrantBridge@Admin2026')
if not User.objects.filter(email=email).exists():
    u = User.objects.create_superuser(email=email, password=password, full_name='GrantBridge Admin', role='entrepreneur')
    u.email_verified = True
    u.verification_status = 'verified'
    u.save()
    print(f'Superuser created: {email}')
else:
    print(f'Superuser already exists: {email}')
"

echo "==> Build complete!"
