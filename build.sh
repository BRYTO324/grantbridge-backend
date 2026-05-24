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
python manage.py collectstatic --noinput --clear -v 0

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Seeding database..."
python manage.py shell -c "
from apps.users.models import User
from apps.pitches.models import PitchCard
import os

# Admin superuser
admin_email = os.environ.get('ADMIN_EMAIL', 'grantbrigdehq@gmail.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'GrantBridge@Admin2026')
if not User.objects.filter(email=admin_email).exists():
    u = User.objects.create_superuser(email=admin_email, password=admin_password, full_name='GrantBridge Admin', role='entrepreneur')
    u.email_verified = True
    u.verification_status = 'verified'
    u.save()
    print(f'Admin created: {admin_email}')
else:
    print(f'Admin exists: {admin_email}')

# Demo entrepreneur
if not User.objects.filter(email='entrepreneur@demo.com').exists():
    ent = User.objects.create_user(
        email='entrepreneur@demo.com', password='demo1234',
        full_name='Amara Okafor', role='entrepreneur',
        company='GreenHarvest Nigeria', phone='+2348012345678',
        verification_status='verified', email_verified=True, profile_completed=True,
    )
    PitchCard.objects.create(
        entrepreneur=ent, title='GreenHarvest — Smart Irrigation for Small Farms',
        description='We build affordable IoT-based irrigation systems that help smallholder farmers in Nigeria reduce water usage by 40% while increasing crop yield.',
        category='AgriTech', amount_needed=5000000, funding_status='open',
        stage='mvp', location='Lagos, Nigeria', tags=['agriculture','IoT','sustainability'],
        verified=True, verification_status='approved',
    )
    PitchCard.objects.create(
        entrepreneur=ent, title='PayEase — Micro-lending for Market Traders',
        description='A mobile-first micro-lending platform targeting the 40 million informal market traders in Nigeria who lack access to traditional banking.',
        category='FinTech', amount_needed=8000000, funding_status='open',
        stage='growth', location='Abuja, Nigeria', tags=['fintech','lending','mobile'],
        verified=True, verification_status='approved',
    )
    PitchCard.objects.create(
        entrepreneur=ent, title='MediLink — Telemedicine for Rural Communities',
        description='Connecting rural Nigerians to qualified doctors via USSD and low-bandwidth video calls. No smartphone required.',
        category='HealthTech', amount_needed=12000000, funding_status='open',
        stage='scale', location='Kano, Nigeria', tags=['health','telemedicine','rural'],
        verified=True, verification_status='approved',
    )
    print('Demo entrepreneur + 3 pitches created')
else:
    print('Demo entrepreneur exists')

# Demo funder
if not User.objects.filter(email='funder@demo.com').exists():
    User.objects.create_user(
        email='funder@demo.com', password='demo1234',
        full_name='Chidi Nwosu', role='funder',
        company='Lagos Ventures Capital', phone='+2348098765432',
        verification_status='verified', email_verified=True, profile_completed=True,
    )
    print('Demo funder created')
else:
    print('Demo funder exists')
"

echo "==> Build complete!"
