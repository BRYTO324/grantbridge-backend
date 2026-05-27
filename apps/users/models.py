"""
Custom User model and VerificationDocument model.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "entrepreneur")
        extra_fields.setdefault("verification_status", "verified")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("entrepreneur", "Entrepreneur"),
        ("funder", "Funder"),
    ]
    VERIFICATION_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    company = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, default="")
    website = models.CharField(max_length=500, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    # Bank account details for receiving payments
    bank_name = models.CharField(max_length=100, blank=True, default="")
    bank_account_number = models.CharField(max_length=20, blank=True, default="")
    bank_account_name = models.CharField(max_length=255, blank=True, default="")
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default="pending",
    )
    profile_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, default="")

    # Password reset
    password_reset_token = models.CharField(max_length=64, blank=True, default="")
    password_reset_token_created_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name} <{self.email}> [{self.role}]"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return ""


class VerificationDocument(models.Model):
    ID_TYPE_CHOICES = [
        ("national_id", "National ID"),
        ("passport", "Passport"),
        ("drivers_license", "Driver's License"),
        ("voters_card", "Voter's Card"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="verification_document",
    )
    id_type = models.CharField(max_length=30)  # national_id, passport, drivers_license, voters_card
    id_number = models.CharField(max_length=100)
    id_front = models.FileField(upload_to="verification/id_front/")
    id_back = models.FileField(upload_to="verification/id_back/", blank=True, null=True)
    selfie = models.FileField(upload_to="verification/selfies/")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_documents"

    def __str__(self):
        return f"Verification docs for {self.user.email}"
