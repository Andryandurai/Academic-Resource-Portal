"""User model.

Email is the credential — students and administrators sign in with the address
the department knows them by, so there is no separate username to remember or to
keep unique alongside it.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.TextChoices):
    STUDENT = "STUDENT", "Student"
    ADMIN = "ADMIN", "Administrator"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email: str, password: str | None, **extra):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        # set_password runs the configured hasher; a raw value never reaches the
        # column. `set_unusable_password` covers accounts created without one.
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra):
        extra.setdefault("role", Role.STUDENT)
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra):
        extra.setdefault("role", Role.ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra["role"] != Role.ADMIN:
            raise ValueError("A superuser must have the ADMIN role.")
        return self._create(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, max_length=254)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT, db_index=True)
    department = models.ForeignKey(
        "academics.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)
    # Django's admin site is not enabled, but PermissionsMixin and createsuperuser
    # both expect this field to exist.
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["role", "-created_at"]
        indexes = [models.Index(fields=["role", "created_at"])]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    def get_short_name(self) -> str:
        return self.name.split(" ")[0] if self.name else self.email

    def get_full_name(self) -> str:
        return self.name
