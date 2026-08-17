"""CSE, ECE and CSD curricula.

Asserts the three syllabi were seeded exactly, that every EEC / non-credit /
internship / project course stayed out, and that the five previously populated
departments were not disturbed.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseType, Department, Subject

pytestmark = pytest.mark.django_db

NEW = ["CSE", "ECE", "CSD"]
EXISTING = {"AI&DS": 39, "AI&ML": 45, "EEE": 51, "BME": 50, "CIVIL": 51}


@pytest.fixture
def catalogue(db):
    from django.core.management import call_command

    call_command("seed_departments", verbosity=0)
    call_command("seed_academics", verbosity=0)
    return {d.code: d for d in Department.objects.all()}


def subjects_for(catalogue, code, semester_number=None):
    query = Subject.objects.filter(semester__department=catalogue[code])
    if semester_number:
        query = query.filter(semester__semester_number=semester_number)
    return query


# --------------------------------------------------------------------------- #
# Departments and totals
# --------------------------------------------------------------------------- #
def test_the_three_departments_exist_and_were_reused(catalogue):
    assert catalogue["CSE"].name == "Computer Science and Engineering"
    assert catalogue["ECE"].name == "Electronics and Communication Engineering"
    assert catalogue["CSD"].name == "Computer Science and Design"
    # Reused, not duplicated — the register stays at nineteen.
    assert Department.objects.count() == 19


@pytest.mark.parametrize("code", NEW)
def test_eight_semesters_each(catalogue, code):
    assert catalogue[code].semesters.count() == 8


@pytest.mark.parametrize("code,expected", [("CSE", 44), ("ECE", 46), ("CSD", 43)])
def test_subject_totals(catalogue, code, expected):
    assert subjects_for(catalogue, code).count() == SUBJECT_COUNTS[code] == expected


@pytest.mark.parametrize("code", NEW)
def test_every_field_matches_the_syllabus(catalogue, code):
    for number, payload in CURRICULA[code].items():
        semester = catalogue[code].semesters.get(semester_number=number)
        for c, title, category, course_type, l, t, p, credits in payload["subjects"]:
            subject = (
                Subject.objects.get(semester=semester, course_code=c)
                if c
                else Subject.objects.get(
                    semester=semester, course_title=title, course_code__isnull=True
                )
            )
            assert (subject.l, subject.t, subject.p, subject.credits) == (l, t, p, credits)
            assert subject.category == category
            assert subject.course_type == course_type


@pytest.mark.parametrize("code", NEW)
def test_theory_and_lab_oriented_are_present(catalogue, code):
    types = set(subjects_for(catalogue, code).values_list("course_type", flat=True))
    assert CourseType.THEORY in types
    assert CourseType.LAB_ORIENTED_THEORY in types


def test_laboratory_courses_exist_where_the_syllabus_lists_them(catalogue):
    for code in NEW:
        labs = subjects_for(catalogue, code).filter(course_type=CourseType.LABORATORY)
        assert labs.exists(), f"{code} has no laboratory courses"


# --------------------------------------------------------------------------- #
# Exclusions
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("code", NEW)
def test_no_excluded_course_was_seeded(catalogue, code):
    for excluded_code, title, reason in EXCLUDED[code]:
        assert not subjects_for(catalogue, code).filter(course_code=excluded_code).exists(), (
            f"{code}: excluded {reason} course {excluded_code} ({title}) was seeded"
        )


@pytest.mark.parametrize(
    "code,absent_code",
    [
        ("CSE", "MC23111"), ("CSE", "MC23112"), ("CSE", "GE23627"), ("CSE", "GE23421"),
        ("CSE", "CS23421"), ("CSE", "GE23521"), ("CSE", "GE23621"), ("CSE", "CS23721"),
        ("CSE", "CS23821"),
        ("ECE", "MC23111"), ("ECE", "MC23112"), ("ECE", "GE23421"), ("ECE", "EC23522"),
        ("ECE", "GE23521"), ("ECE", "GE23621"), ("ECE", "GE23627"), ("ECE", "EC23721"),
        ("ECE", "EC23821"),
        ("CSD", "MC23111"), ("CSD", "MC23112"), ("CSD", "GE23421"), ("CSD", "CD23421"),
        ("CSD", "GE23627"), ("CSD", "GE23521"), ("CSD", "CD23632"), ("CSD", "GE23621"),
        ("CSD", "CD23722"), ("CSD", "CD23821"),
    ],
)
def test_each_listed_exclusion_is_absent(catalogue, code, absent_code):
    assert not subjects_for(catalogue, code).filter(course_code=absent_code).exists()


def test_ece_ai_ml_course_is_excluded(catalogue):
    """EC23721 is a PC-category course, but the syllabus files it under EEC."""
    assert not Subject.objects.filter(course_code="EC23721").exists()


# --------------------------------------------------------------------------- #
# Spot checks
# --------------------------------------------------------------------------- #
def test_cse_semester_three_contents(catalogue):
    titles = set(subjects_for(catalogue, "CSE", 3).values_list("course_title", flat=True))
    assert titles == {
        "Fourier Series and Number Theory",
        "Computer Architecture",
        "Design and Analysis of Algorithms",
        "Database Management Systems",
        "Object Oriented Programming Using Java",
        "Fundamentals of Data Science",
    }


def test_cse_semester_six_is_all_lab_oriented_plus_one_laboratory(catalogue):
    """The syllabus lists no theory course in this semester."""
    sixth = subjects_for(catalogue, "CSE", 6)
    assert sixth.count() == 6
    assert sixth.filter(course_type=CourseType.THEORY).count() == 0
    assert sixth.filter(course_type=CourseType.LABORATORY).count() == 1


def test_csd_semester_three_contents(catalogue):
    titles = set(subjects_for(catalogue, "CSD", 3).values_list("course_title", flat=True))
    assert titles == {
        "Discrete Mathematics for AI",
        "Design Processes and Perspectives",
        "Design and Analysis of Algorithms",
        "UI and UX Design",
        "Database Management Systems",
        "Python Programming for Design",
    }


def test_ece_semester_six_contents(catalogue):
    titles = set(subjects_for(catalogue, "ECE", 6).values_list("course_title", flat=True))
    assert titles == {
        "Antenna Theory and Wave Propagation",
        "Open Elective-II",
        "VLSI and Chip Design",
        "Communication Networks",
        "Wireless Communication",
    }


def test_ma23111_carries_its_department_specific_title(catalogue):
    """CSD runs the code as Mathematics for Design; CSE and ECE do not."""
    assert subjects_for(catalogue, "CSD").get(course_code="MA23111").course_title == (
        "Mathematics for Design"
    )
    for code in ("CSE", "ECE"):
        assert subjects_for(catalogue, code).get(course_code="MA23111").course_title == (
            "Linear Algebra and Calculus"
        )


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #
def test_semester_three_differs_across_every_populated_department(catalogue):
    per_department = {
        # (code, title) pairs, not titles alone: Mechatronics and Robotics and
        # Automation publish an identical Semester III apart from one course
        # code, so a title-only comparison would report a false clash.
        code: frozenset(
            subjects_for(catalogue, code, 3).values_list("course_code", "course_title")
        )
        for code in CURRICULA
    }
    for code, rows in per_department.items():
        assert rows, f"{code} Semester III is empty"
    # One distinct subject list per populated department.
    assert len(set(per_department.values())) == len(CURRICULA)


@pytest.mark.parametrize(
    "code,foreign_code",
    [
        ("CSE", "EC23631"),   # ECE's VLSI course
        ("CSE", "CD23332"),   # CSD's UI and UX Design
        ("ECE", "CS23311"),   # CSE's Computer Architecture
        ("ECE", "CD23321"),   # CSD's Python for Design
        ("CSD", "CS23311"),   # CSE's Computer Architecture
        ("CSD", "EC23511"),   # ECE's Control System Engineering
    ],
)
def test_no_foreign_course_is_reachable(catalogue, code, foreign_code):
    assert not subjects_for(catalogue, code).filter(course_code=foreign_code).exists()


def test_shared_first_year_courses_are_separate_records(catalogue):
    """PH23132 runs in several departments — as one distinct row each.

    The expected set is derived from the curricula so adding a department that
    also runs the course does not turn this into a false failure.
    """
    expected = {
        code
        for code, curriculum in CURRICULA.items()
        for payload in curriculum.values()
        for c, *_rest in payload["subjects"]
        if c == "PH23132"
    }
    rows = Subject.objects.filter(course_code="PH23132")
    assert set(rows.values_list("semester__department__code", flat=True)) == expected
    assert rows.count() == len(expected)
    assert len(set(rows.values_list("id", flat=True))) == len(expected)


def test_api_isolates_the_new_departments(student_api, catalogue):
    for code, expected in [("CSE", 44), ("ECE", 46), ("CSD", 43)]:
        department = catalogue[code]
        rows = student_api.get(
            "/api/subjects/", {"department": department.id, "page_size": 200}
        ).data
        assert rows["count"] == expected
        assert all(row["department"] == department.id for row in rows["results"])

    # A CSE-only code must not be reachable through ECE.
    assert (
        student_api.get(
            "/api/subjects/", {"department": catalogue["ECE"].id, "search": "CS23311"}
        ).data["count"]
        == 0
    )


def test_stats_are_per_department(student_api, catalogue):
    for code, expected in SUBJECT_COUNTS.items():
        stats = student_api.get("/api/stats/", {"department": catalogue[code].id}).data
        assert stats["semesters"] == 8
        assert stats["subjects"] == expected


# --------------------------------------------------------------------------- #
# Existing departments
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("code,expected", list(EXISTING.items()))
def test_previously_populated_departments_are_untouched(catalogue, code, expected):
    assert subjects_for(catalogue, code).count() == expected


def test_only_departments_with_a_syllabus_report_curriculum(student_api, catalogue):
    rows = student_api.get("/api/departments/").data
    ready = sorted(row["code"] for row in rows if row["has_curriculum"])
    assert ready == sorted(CURRICULA)
    assert sum(1 for row in rows if not row["has_curriculum"]) == 19 - len(CURRICULA)


def test_seed_is_idempotent_across_all_departments(catalogue):
    from django.core.management import call_command

    call_command("seed_academics", verbosity=0)
    call_command("seed_academics", verbosity=0)
    assert Subject.objects.count() == sum(SUBJECT_COUNTS.values())
    assert Department.objects.count() == 19


def test_verify_curriculum_passes_for_all(catalogue):
    from django.core.management import call_command

    call_command("verify_curriculum", verbosity=0)


def test_resources_stay_within_their_department(admin_api, student_api, catalogue):
    from conftest import pdf_upload

    targets = [
        ("CSE", "CS23332", "CSE DBMS Unit 1"),
        ("ECE", "EC23631", "ECE VLSI Unit 1"),
        ("CSD", "CD23332", "CSD UI/UX CAT 1"),
    ]

    for code, course_code, title in targets:
        subject = subjects_for(catalogue, code).get(course_code=course_code)
        response = admin_api.post(
            "/api/resources/",
            {
                "subject": subject.id,
                "resource_type": "UNIT_1",
                "title": title,
                "file": pdf_upload(),
            },
            format="multipart",
        )
        assert response.status_code == 201, response.data

    for code, _course_code, title in targets:
        rows = student_api.get(
            "/api/resources/", {"department": catalogue[code].id}
        ).data
        assert rows["count"] == 1
        assert rows["results"][0]["title"] == title

    # A department with no curriculum sees none of it.
    assert (
        student_api.get(
            "/api/resources/", {"department": catalogue["ME"].id}
        ).data["count"]
        == 0
    )
