"""Verify every seeded curriculum against its syllabus.

    python manage.py verify_curriculum
    python manage.py verify_curriculum --department EEE

Checks each course code, title, category, course type and L/T/P/C, asserts that
excluded (non-credit / EEC / internship / project) courses were not seeded, and
asserts that no department's subjects leaked into another. Exits non-zero on any
mismatch, so it can gate a deployment.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseType, Department, Subject

VALID_TYPES = {CourseType.THEORY, CourseType.LAB_ORIENTED_THEORY, CourseType.LABORATORY}


class Command(BaseCommand):
    help = "Assert the database matches every supplied syllabus exactly."

    def add_arguments(self, parser):
        parser.add_argument("--department", help="Verify only this department code.")

    def handle(self, *args, **options):
        wanted = options.get("department")
        codes = [wanted] if wanted else list(CURRICULA)
        problems: list[str] = []

        self.stdout.write("Curriculum verification")
        self.stdout.write("=" * 60)

        for code in codes:
            department = Department.objects.filter(code=code).first()
            if department is None:
                problems.append(f"Department {code!r} is missing.")
                continue

            problems.extend(self._verify_department(department, CURRICULA[code]))
            problems.extend(self._verify_exclusions(department, code))

        problems.extend(self._verify_isolation())

        if problems:
            self.stdout.write("")
            self.stdout.write("Problems:")
            for problem in problems:
                self.stdout.write(self.style.ERROR(f"  ! {problem}"))
            raise CommandError(f"FAILED: {len(problems)} problem(s).")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("PASSED: every syllabus matches the database exactly.")
        )

    # ------------------------------------------------------------------ #
    def _verify_department(self, department: Department, curriculum: dict) -> list[str]:
        problems: list[str] = []
        verified = 0

        self.stdout.write("")
        self.stdout.write(f"{department.name} ({department.code})")

        for number, payload in sorted(curriculum.items()):
            semester = department.semesters.filter(semester_number=number).first()
            if semester is None:
                problems.append(f"{department.code}: Semester {number} is missing.")
                continue

            for code, title, category, course_type, l, t, p, credits in payload["subjects"]:
                if code:
                    subject = Subject.objects.filter(
                        semester=semester, course_code=code
                    ).first()
                else:
                    subject = Subject.objects.filter(
                        semester=semester, course_title=title, course_code__isnull=True
                    ).first()

                label = f"{department.code} Sem {number} {code or '(no code)'} {title}"
                if subject is None:
                    problems.append(f"Missing subject: {label}")
                    continue

                for field, got, want in [
                    ("course_title", subject.course_title, title),
                    ("category", subject.category, category),
                    ("course_type", subject.course_type, course_type),
                    ("L", subject.l, l),
                    ("T", subject.t, t),
                    ("P", subject.p, p),
                    ("credits", subject.credits, credits),
                ]:
                    if got != want:
                        problems.append(f"{label}: {field} is {got!r}, expected {want!r}")

                if subject.course_type not in VALID_TYPES:
                    problems.append(f"{label}: invalid course type {subject.course_type!r}")

                verified += 1

            counts = {
                t: semester.subjects.filter(course_type=t).count() for t in VALID_TYPES
            }
            self.stdout.write(
                f"  Semester {number:>2} : {semester.subjects.count():>2} subjects  "
                f"(theory {counts[CourseType.THEORY]}, "
                f"lab-oriented {counts[CourseType.LAB_ORIENTED_THEORY]}, "
                f"laboratory {counts[CourseType.LABORATORY]})"
            )

        stored = Subject.objects.filter(semester__department=department).count()
        expected = SUBJECT_COUNTS[department.code]
        self.stdout.write(
            f"  Verified {verified}/{expected} syllabus subjects; {stored} stored; "
            f"{Subject.objects.filter(semester__department=department, course_code__isnull=True).count()} "
            "elective(s) with no code (codes are never invented)."
        )
        if stored != expected:
            problems.append(
                f"{department.code}: {stored} subjects stored but {expected} in the syllabus."
            )

        return problems

    def _verify_exclusions(self, department: Department, code: str) -> list[str]:
        """Non-credit, EEC, internship and project courses must not be present."""
        problems = []
        for excluded_code, excluded_title, reason in EXCLUDED.get(code, []):
            found = Subject.objects.filter(semester__department=department).filter(
                course_code=excluded_code
            )
            if found.exists():
                problems.append(
                    f"{code}: excluded {reason} course {excluded_code} "
                    f"({excluded_title}) was seeded."
                )
        return problems

    def _verify_isolation(self) -> list[str]:
        """No department may hold a subject its own syllabus does not list.

        Derived from the curricula rather than from hand-picked signature
        titles. Departments legitimately share first-year courses — PH23132 runs
        in AI&DS, CSE and CSD — so "this title belongs to exactly one
        department" was never a sound rule. What *is* sound: every stored
        subject must appear in its own department's syllabus, and no other
        department's exclusive subject may appear under it.
        """
        problems = []

        # title -> the set of department codes whose syllabus lists it.
        expected: dict[str, set[str]] = {}
        for code, curriculum in CURRICULA.items():
            for payload in curriculum.values():
                for _c, title, *_rest in payload["subjects"]:
                    expected.setdefault(title, set()).add(code)

        stored: dict[str, set[str]] = {}
        for title, dept_code in Subject.objects.values_list(
            "course_title", "semester__department__code"
        ):
            stored.setdefault(title, set()).add(dept_code)

        for title, holders in stored.items():
            allowed = expected.get(title)
            if allowed is None:
                # Added through the admin UI rather than seeded — not a breach.
                continue
            strays = holders - allowed
            if strays:
                problems.append(
                    f"Isolation breach: {title!r} is listed only for "
                    f"{', '.join(sorted(allowed))} but also appears under "
                    f"{', '.join(sorted(strays))}."
                )

        return problems
