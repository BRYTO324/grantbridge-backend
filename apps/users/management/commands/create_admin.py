"""
Management command to create the initial superuser non-interactively.
Usage: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create the initial GrantBridge admin superuser"

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@grantbridge.com")
        parser.add_argument("--password", default="Admin1234!")
        parser.add_argument("--full-name", default="GrantBridge Admin")

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        full_name = options["full_name"]

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"Admin user '{email}' already exists."))
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            full_name=full_name,
            role="entrepreneur",
        )
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Superuser created successfully!\n"
            f"  Email:    {email}\n"
            f"  Password: {password}\n"
            f"  Admin:    http://localhost:8000/admin/\n"
        ))
