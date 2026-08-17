"""Seed the college's departments.

    python manage.py seed_departments

Idempotent and non-destructive. Departments are matched on their code, so the
existing AI&DS record — which already owns eight semesters and 39 subjects — is
updated in place rather than duplicated, and its curriculum is untouched.

Seeds department records only. No semesters, subjects or resources are created
for departments whose curriculum has not been supplied.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from academics.departments import DEPARTMENTS
from academics.models import Department, Semester, Subject


class Command(BaseCommand):
    help = "Seed the college's departments (idempotent, non-destructive)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate-unlisted",
            action="store_true",
            help=(
                "Mark departments that are not in the canonical list as inactive. "
                "Never deletes: a department may already hold curriculum."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created = updated = 0

        for name, code, _group in DEPARTMENTS:
            department = Department.objects.filter(code=code).first()
            if department is None:
                # Fall back to the name so a record created before codes existed
                # is adopted rather than duplicated.
                department = Department.objects.filter(name=name).first()

            if department is None:
                Department.objects.create(name=name, code=code, is_active=True)
                created += 1
                self.stdout.write(f"  + {code:<7} {name}")
            else:
                changed = []
                if department.name != name:
                    changed.append(f"name {department.name!r} -> {name!r}")
                    department.name = name
                if department.code != code:
                    changed.append(f"code {department.code!r} -> {code!r}")
                    department.code = code
                if not department.is_active:
                    changed.append("reactivated")
                    department.is_active = True
                if changed:
                    department.save()
                    updated += 1
                    self.stdout.write(f"  ~ {code:<7} {name}  ({'; '.join(changed)})")

        if options["deactivate_unlisted"]:
            listed = [code for _name, code, _group in DEPARTMENTS]
            stale = Department.objects.exclude(code__in=listed).filter(is_active=True)
            for department in stale:
                department.is_active = False
                department.save(update_fields=["is_active", "updated_at"])
                self.stdout.write(self.style.WARNING(f"  - {department.code} deactivated"))

        total = Department.objects.count()
        with_curriculum = (
            Department.objects.filter(semesters__subjects__isnull=False).distinct().count()
        )

        self.stdout.write("")
        self.stdout.write(
            f"Departments: {created} created, {updated} updated, {total} total."
        )
        self.stdout.write(
            f"With curriculum: {with_curriculum} "
            f"({Semester.objects.count()} semesters, {Subject.objects.count()} subjects). "
            "The rest are awaiting their syllabus."
        )
        self.stdout.write(self.style.SUCCESS("Department seed complete."))
