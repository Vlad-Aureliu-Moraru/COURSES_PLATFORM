import hashlib
import random
import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'

    @property
    def is_locked(self):
        return self.locked_until is not None and self.locked_until > timezone.now()

    def __str__(self):
        return self.email


class PasswordResetToken(models.Model):
    TOKEN_TTL = timedelta(hours=24)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='password_reset_tokens'
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'password_reset_tokens'

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user).delete()
        token = secrets.token_urlsafe(32)
        return cls.objects.create(
            user=user,
            token_hash=cls.hash_token(token),
            expires_at=timezone.now() + cls.TOKEN_TTL,
        ), token

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def consume(cls, token):
        instance = cls.objects.filter(token_hash=cls.hash_token(token)).first()
        if instance is None:
            return None
        if instance.expires_at <= timezone.now():
            instance.delete()
            return None
        return instance

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()


class EmailVerificationCode(models.Model):
    CODE_TTL = timedelta(minutes=15)
    CODE_LENGTH = 6

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='verification_codes'
    )
    code_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_verification_codes'

    @classmethod
    def generate_code(cls):
        return f'{random.SystemRandom().randint(0, 999999):06d}'

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user).delete()
        code = cls.generate_code()
        return cls.objects.create(
            user=user,
            code_hash=cls.hash_code(code),
            expires_at=timezone.now() + cls.CODE_TTL,
        ), code

    @staticmethod
    def hash_code(code):
        return hashlib.sha256(code.encode()).hexdigest()

    @classmethod
    def consume(cls, user, code):
        instance = cls.objects.filter(user=user, code_hash=cls.hash_code(code)).first()
        if instance is None:
            return None
        if instance.expires_at <= timezone.now():
            instance.delete()
            return None
        return instance

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()
