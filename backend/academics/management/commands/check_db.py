"""Verify the configured database is reachable, without printing credentials.

    python manage.py check_db

Opens a connection using whatever DATABASE_URL / REC_DATABASE_URL (or the
SQLite default) settings.py resolved, runs a trivial query, and reports the
database engine and name only — never the host, user or password. Exits
non-zero on failure, so it can gate a deployment step the way
`verify_curriculum` gates a data check.

This is a read-only diagnostic. It creates no tables and touches no data.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Check that the configured database is reachable, without exposing credentials."

    def handle(self, *args, **options):
        vendor = connection.vendor  # "postgresql" or "sqlite"
        db_name = connection.settings_dict.get("NAME", "")

        self.stdout.write(f"Engine:   {vendor}")
        self.stdout.write(f"Database: {db_name}")

        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            raise CommandError(f"Could not connect to the database: {exc.__class__.__name__}") from exc

        self.stdout.write(self.style.SUCCESS("Connection OK — the database is reachable."))
