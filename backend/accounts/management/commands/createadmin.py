"""Create or promote an administrator account.

    python manage.py createadmin --email admin@college.edu --name "Dept Admin"

Administrator accounts are never created through the web interface — public
self-registration always produces a student, so privilege escalation is not on
the public attack surface at all. Without --password a strong one is generated
and printed once.
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from academics.models import Department
from accounts.models import Role, User


class Command(BaseCommand):
    help = "Create an administrator account, or promote an existing user to administrator."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--name", default="Administrator")
        parser.add_argument(
            "--password",
            default=None,
            help="Omit to have a strong password generated and printed once.",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        try:
            validate_email(email)
        except ValidationError as exc:
            raise CommandError(f"{email!r} is not a valid email address.") from exc

        password = options["password"] or secrets.token_urlsafe(12)
        generated = options["password"] is None

        if len(password) < 8:
            raise CommandError("The password must be at least 8 characters.")

        department = Department.objects.filter(code=settings.DEPARTMENT_CODE).first()
        user = User.objects.filter(email=email).first()

        if user:
            user.role = Role.ADMIN
            user.is_staff = True
            user.name = options["name"]
            user.set_password(password)
            user.save()
            self.stdout.write(f"Updated {email}: role set to ADMIN and password reset.")
        else:
            User.objects.create_user(
                email=email,
                password=password,
                name=options["name"],
                role=Role.ADMIN,
                is_staff=True,
                department=department,
            )
            self.stdout.write(f"Created administrator {email}.")

        if generated:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"  Generated password: {password}"))
            self.stdout.write("  Store it securely — it is not shown again.")
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Sign in at /admin/login"))
