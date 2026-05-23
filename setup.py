"""
One-shot setup script: makemigrations + migrate + create superuser.
Run with: python setup.py
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.core.management import call_command

print("=" * 60)
print("Step 1: Making migrations...")
print("=" * 60)
for app in ["users", "pitches", "offers", "payments", "progress"]:
    print(f"  -> {app}")
    call_command("makemigrations", app, verbosity=1)

print("\n" + "=" * 60)
print("Step 2: Running migrate...")
print("=" * 60)
call_command("migrate", verbosity=1)

print("\n" + "=" * 60)
print("Step 3: Creating superuser (admin / admin@grantbridge.com / admin123)...")
print("=" * 60)
from apps.users.models import User
if not User.objects.filter(email="admin@grantbridge.com").exists():
    User.objects.create_superuser(
        email="admin@grantbridge.com",
        password="admin123",
        full_name="Admin User",
        role="entrepreneur",
    )
    print("  Superuser created: admin@grantbridge.com / admin123")
else:
    print("  Superuser already exists.")

print("\n" + "=" * 60)
print("Step 4: Creating sample data...")
print("=" * 60)
from apps.users.models import User
from apps.pitches.models import PitchCard

# Create a sample entrepreneur
if not User.objects.filter(email="entrepreneur@demo.com").exists():
    ent = User.objects.create_user(
        email="entrepreneur@demo.com",
        password="demo1234",
        full_name="Amara Okafor",
        role="entrepreneur",
        company="GreenHarvest Nigeria",
        phone="+2348012345678",
        verification_status="verified",
        email_verified=True,
        profile_completed=True,
    )
    print("  Entrepreneur: entrepreneur@demo.com / demo1234")

    # Create sample pitches
    PitchCard.objects.create(
        entrepreneur=ent,
        title="GreenHarvest — Smart Irrigation for Small Farms",
        description="We build affordable IoT-based irrigation systems that help smallholder farmers in Nigeria reduce water usage by 40% while increasing crop yield. Our MVP is deployed across 12 farms in Ogun State.",
        category="AgriTech",
        amount_needed=5000000,
        funding_status="open",
        stage="mvp",
        location="Lagos, Nigeria",
        tags=["agriculture", "IoT", "sustainability", "food security"],
        verified=True,
        verification_status="approved",
    )
    PitchCard.objects.create(
        entrepreneur=ent,
        title="PayEase — Micro-lending for Market Traders",
        description="A mobile-first micro-lending platform targeting the 40 million informal market traders in Nigeria who lack access to traditional banking. We use AI-based credit scoring from transaction history.",
        category="FinTech",
        amount_needed=8000000,
        funding_status="open",
        stage="growth",
        location="Abuja, Nigeria",
        tags=["fintech", "lending", "financial inclusion", "mobile"],
        verified=True,
        verification_status="approved",
    )
    PitchCard.objects.create(
        entrepreneur=ent,
        title="MediLink — Telemedicine for Rural Communities",
        description="Connecting rural Nigerians to qualified doctors via USSD and low-bandwidth video calls. No smartphone required. Currently serving 3,000 patients monthly across 5 states.",
        category="HealthTech",
        amount_needed=12000000,
        funding_status="open",
        stage="scale",
        location="Kano, Nigeria",
        tags=["health", "telemedicine", "rural", "USSD"],
        verified=True,
        verification_status="approved",
    )
    print("  3 sample pitches created.")
else:
    print("  Demo entrepreneur already exists.")

# Create a sample funder
if not User.objects.filter(email="funder@demo.com").exists():
    User.objects.create_user(
        email="funder@demo.com",
        password="demo1234",
        full_name="Chidi Nwosu",
        role="funder",
        company="Lagos Ventures Capital",
        phone="+2348098765432",
        verification_status="verified",
        email_verified=True,
        profile_completed=True,
    )
    print("  Funder: funder@demo.com / demo1234")
else:
    print("  Demo funder already exists.")

print("\n" + "=" * 60)
print("SETUP COMPLETE!")
print("=" * 60)
print("\nDemo accounts:")
print("  Entrepreneur : entrepreneur@demo.com / demo1234")
print("  Funder       : funder@demo.com       / demo1234")
print("  Admin        : admin@grantbridge.com  / admin123")
print("\nStart the server with:")
print("  .\\venv\\Scripts\\python.exe manage.py runserver")
print("=" * 60)
