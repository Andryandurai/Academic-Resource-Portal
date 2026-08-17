"""Seed every department's curriculum.

    python manage.py seed_academics                 # all departments with data
    python manage.py seed_academics --department EEE

Idempotent: subjects are matched on (semester, course code) — or on
(semester, title) for electives, which publish no code — so re-running updates
rows rather than duplicating them. Uploaded resources are never touched.

Seeds academic metadata only. Notes, question papers and other resources exist
only once an administrator uploads them.
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academics.curricula import CURRICULA, SUBJECT_COUNTS
from academics.models import Department, Semester, Subject


class Command(BaseCommand):
    help = "Seed the curriculum for every department that has one (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--department",
            help="Seed only this department code (e.g. EEE). Defaults to all.",
        )
        parser.add_argument(
            "--prune",
            action="store_true",
            help=(
                "Remove subjects that are no longer in the syllabus. "
                "Refuses to delete any subject that has uploaded resources."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        wanted = options.get("department")
        if wanted and wanted not in CURRICULA:
            raise CommandError(
                f"No curriculum defined for {wanted!r}. Known: {', '.join(CURRICULA)}."
            )

        codes = [wanted] if wanted else list(CURRICULA)
        totals = {"created": 0, "updated": 0}

        for code in codes:
            department = Department.objects.filter(code=code).first()
            if department is None:
                raise CommandError(
                    f"Department {code!r} does not exist. Run `manage.py seed_departments` first."
                )

            created, updated, seen = self._seed_department(department, CURRICULA[code])
            totals["created"] += created
            totals["updated"] += updated

            self.stdout.write(
                f"{department.name} ({code}): {created} subject(s) created, "
                f"{updated} updated — {SUBJECT_COUNTS[code]} in the syllabus."
            )

            if options["prune"]:
                self._prune(department, seen)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete — {Semester.objects.count()} semesters, "
                f"{Subject.objects.count()} subjects, "
                f"{_resource_count()} resources (resources are uploaded by an administrator)."
            )
        )

    def _seed_department(self, department: Department, curriculum: dict):
        created = updated = 0
        seen: list[int] = []

        for number, payload in sorted(curriculum.items()):
            semester, _ = Semester.objects.update_or_create(
                department=department,
                semester_number=number,
                defaults={"name": payload["name"]},
            )

            for code, title, category, course_type, l, t, p, credits in payload["subjects"]:
                fields = {
                    "semester": semester,
                    "course_title": title,
                    "category": category,
                    "course_type": course_type,
                    "l": l,
                    "t": t,
                    "p": p,
                    "credits": credits,
                }

                # Course codes repeat across departments (and, for Engineering
                # Graphics, across semesters), so the lookup is always scoped to
                # the semester. Electives carry no code and match on title.
                if code:
                    subject = Subject.objects.filter(
                        semester=semester, course_code=code
                    ).first()
                else:
                    subject = Subject.objects.filter(
                        semester=semester, course_title=title, course_code__isnull=True
                    ).first()

                if subject is None:
                    subject = Subject.objects.create(course_code=code, **fields)
                    created += 1
                else:
                    for key, value in {"course_code": code, **fields}.items():
                        setattr(subject, key, value)
                    subject.save()
                    updated += 1

                seen.append(subject.id)

        return created, updated, seen

    def _prune(self, department: Department, keep_ids: list[int]) -> None:
        extras = Subject.objects.filter(semester__department=department).exclude(
            id__in=keep_ids
        )
        blocked = [s for s in extras if s.resources.exists()]
        removable = [s for s in extras if not s.resources.exists()]

        for subject in blocked:
            self.stdout.write(
                self.style.WARNING(
                    f"  kept {subject}: it has uploaded resources and was not removed."
                )
            )
        if removable:
            Subject.objects.filter(id__in=[s.id for s in removable]).delete()
            self.stdout.write(
                f"  pruned {len(removable)} subject(s) no longer in the {department.code} syllabus."
            )


def _resource_count() -> int:
    from resources.models import Resource

    return Resource.objects.count()


# Kept so anything importing the old name still resolves.
DEPARTMENT_CODE = settings.DEPARTMENT_CODE
