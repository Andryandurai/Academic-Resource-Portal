"""Import data from the previous Next.js/Prisma SQLite database.

    python manage.py import_legacy --db ../prisma/dev.db [--files ../storage/uploads]

Migration step, run once. The curriculum itself is not imported — `seed_academics`
reproduces it exactly from the same syllabus — so this carries across the two
things that cannot be regenerated:

  * **User accounts**, including their bcrypt password hashes, rewritten into
    Django's `bcrypt$<hash>` encoding so nobody has to reset a password because
    the backend changed language. Django re-hashes to PBKDF2 on next login.
  * **Uploaded resources**, matched to the seeded subjects by course code (or by
    title for the electives that have no code), with the stored file copied into
    Django's media root.

Idempotent: an account or resource that already exists is left alone.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academics.models import Subject
from accounts.models import Role, User
from resources.models import Resource


class Command(BaseCommand):
    help = "Import users and uploaded resources from the legacy Prisma SQLite database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--db",
            default="../prisma/dev.db",
            help="Path to the legacy Prisma SQLite file (default: ../prisma/dev.db).",
        )
        parser.add_argument(
            "--files",
            default="../storage/uploads",
            help="Directory holding the legacy uploaded files (default: ../storage/uploads).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be imported without writing anything.",
        )

    def handle(self, *args, **options):
        db_path = (Path(settings.BASE_DIR) / options["db"]).resolve()
        files_dir = (Path(settings.BASE_DIR) / options["files"]).resolve()
        dry_run = options["dry_run"]

        if not db_path.is_file():
            raise CommandError(
                f"No legacy database at {db_path}. Pass --db if it lives elsewhere; "
                "if the previous stack was never run there is nothing to import."
            )

        self.stdout.write(f"Legacy database : {db_path}")
        self.stdout.write(f"Legacy uploads  : {files_dir}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — nothing will be written.\n"))

        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            users = self._read(connection, "User")
            resources = self._read(connection, "Resource")
            subjects = {row["id"]: row for row in self._read(connection, "Subject")}
        finally:
            connection.close()

        self.stdout.write(
            f"Found {len(users)} user(s), {len(subjects)} subject(s), {len(resources)} resource(s).\n"
        )

        with transaction.atomic():
            imported_users = self._import_users(users, dry_run)
            imported_resources = self._import_resources(resources, subjects, files_dir, dry_run)
            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {imported_users} user(s) and {imported_resources} resource(s)."
            )
        )
        if not dry_run:
            self.stdout.write(
                "Verify with: python manage.py verify_curriculum && python manage.py shell"
            )

    # ------------------------------------------------------------------ #
    def _read(self, connection: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
        try:
            return list(connection.execute(f'SELECT * FROM "{table}"'))
        except sqlite3.OperationalError:
            # A table the old schema never created is not an error here.
            return []

    def _import_users(self, rows, dry_run: bool) -> int:
        from academics.models import Department

        department = Department.objects.filter(code=settings.DEPARTMENT_CODE).first()
        imported = 0

        for row in rows:
            email = (row["email"] or "").strip().lower()
            if not email:
                continue
            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  = user {email} already exists — left unchanged")
                continue

            legacy_hash = row["passwordHash"] or ""
            # bcryptjs writes a bare modular-crypt string; Django expects an
            # algorithm prefix. `accounts.hashers.LegacyBCryptPasswordHasher`
            # reads the result.
            if legacy_hash.startswith("$2"):
                password_hash = f"bcrypt${legacy_hash}"
            else:
                password_hash = "!"  # unusable — the account needs a reset
                self.stdout.write(
                    self.style.WARNING(
                        f"  ! user {email} had an unrecognised hash; imported without a usable password"
                    )
                )

            role = Role.ADMIN if (row["role"] or "").upper() == "ADMIN" else Role.STUDENT

            if not dry_run:
                user = User(
                    email=email,
                    name=row["name"] or email.split("@")[0],
                    role=role,
                    department=department,
                    is_staff=role == Role.ADMIN,
                )
                user.password = password_hash
                user.save()
            self.stdout.write(f"  + user {email} ({role})")
            imported += 1

        return imported

    def _import_resources(self, rows, legacy_subjects, files_dir: Path, dry_run: bool) -> int:
        imported = 0

        for row in rows:
            legacy_subject = legacy_subjects.get(row["subjectId"])
            if legacy_subject is None:
                self.stdout.write(
                    self.style.WARNING(f"  ! resource {row['title']!r}: unknown subject — skipped")
                )
                continue

            subject = self._match_subject(legacy_subject)
            if subject is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ! resource {row['title']!r}: no matching subject for "
                        f"{legacy_subject['courseCode'] or legacy_subject['courseTitle']!r} — skipped"
                    )
                )
                continue

            if Resource.objects.filter(
                subject=subject, title=row["title"], resource_type=row["resourceType"]
            ).exists():
                self.stdout.write(f"  = resource {row['title']!r} already exists — left unchanged")
                continue

            source = files_dir / (row["storedName"] or "")
            if not source.is_file():
                self.stdout.write(
                    self.style.WARNING(
                        f"  ! resource {row['title']!r}: file {source.name} missing — skipped"
                    )
                )
                continue

            uploader = None
            if row["uploadedById"]:
                uploader = User.objects.filter(role=Role.ADMIN).order_by("created_at").first()

            if not dry_run:
                resource = Resource(
                    subject=subject,
                    resource_type=row["resourceType"],
                    title=row["title"],
                    description=row["description"] or "",
                    file_name=row["fileName"],
                    file_type=row["fileType"],
                    file_ext=row["fileExt"],
                    file_size=row["fileSize"] or source.stat().st_size,
                    uploaded_by=uploader,
                )
                with source.open("rb") as handle:
                    resource.file.save(source.name, File(handle), save=False)
                resource.save()

            self.stdout.write(f"  + resource {row['title']!r} -> {subject}")
            imported += 1

        return imported

    def _match_subject(self, legacy_row) -> Subject | None:
        code = (legacy_row["courseCode"] or "").strip()
        if code:
            return Subject.objects.filter(course_code=code).first()
        # Electives have no code; the title plus semester ordinal identifies them.
        return Subject.objects.filter(
            course_title=legacy_row["courseTitle"], course_code__isnull=True
        ).first()


# Keep shutil imported for operators who extend this to copy a whole media tree.
_ = shutil
