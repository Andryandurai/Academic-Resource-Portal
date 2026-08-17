"""Mechanical Engineering and Information Technology curricula.

Asserts both syllabi were seeded exactly, that every EEC / non-credit /
internship / project course stayed out, and that the eight previously populated
departments were not disturbed.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseType, Department, Subject

pytestmark = pytest.mark.django_db

NEW = ["ME", "IT"]
EXISTING = {
    "AI&DS": 39, "AI&ML": 45, "EEE": 51, "BME": 50,
    "CIVIL": 51, "CSE": 44, "ECE": 46, "CSD": 43,
}


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
def test_both_departments_exist_and_were_reused(catalogue):
    assert catalogue["ME"].name == "Mechanical Engineering"
    assert catalogue["IT"].name == "Information Technology"
    assert Department.objects.count() == 19


@pytest.mark.parametrize("code", NEW)
def test_eight_semesters_each(catalogue, code):
    assert catalogue[code].semesters.count() == 8


@pytest.mark.parametrize("code,expected", [("ME", 50), ("IT", 45)])
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
def test_all_three_course_types_are_represented(catalogue, code):
    types = set(subjects_for(catalogue, code).values_list("course_type", flat=True))
    assert types == {
        CourseType.THEORY,
        CourseType.LAB_ORIENTED_THEORY,
        CourseType.LABORATORY,
    }


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
    "code,title",
    [
        ("ME", "Environmental Science and Engineering"),
        ("ME", "Indian Constitution and Freedom Movement"),
        ("ME", "Soft Skills-I"),
        ("ME", "Soft Skills-II"),
        ("ME", "Industrial Training Internship"),
        ("ME", "Problem Solving Techniques"),
        ("ME", "Innovation and Design Thinking for Mechanical Engineer"),
        ("ME", "Comprehension"),
        ("ME", "Project Phase I"),
        ("ME", "Project Work"),
        ("IT", "Environmental Science and Engineering"),
        ("IT", "Indian Constitution and Freedom Movement"),
        ("IT", "Soft Skills-I"),
        ("IT", "Internship"),
        ("IT", "Soft Skills-II"),
        ("IT", "Design Thinking and Innovation"),
        ("IT", "Problem Solving Techniques"),
        ("IT", "Project Phase I"),
        ("IT", "Project Phase II"),
    ],
)
def test_named_excluded_titles_are_absent(catalogue, code, title):
    assert not subjects_for(catalogue, code).filter(course_title=title).exists()


# --------------------------------------------------------------------------- #
# Cross-department test from the brief
# --------------------------------------------------------------------------- #
def test_me_semester_three_contents(catalogue):
    titles = set(subjects_for(catalogue, "ME", 3).values_list("course_title", flat=True))
    assert titles == {
        "Engineering Thermodynamics",
        "Manufacturing Technology I",
        "Kinematics of Machinery",
        "Transforms and Statistics",
        "Strength of Materials",
        "Manufacturing Technology Laboratory I",
        "Python Programming for Machine Learning",
    }


def test_it_semester_three_contents(catalogue):
    titles = set(subjects_for(catalogue, "IT", 3).values_list("course_title", flat=True))
    assert titles == {
        "Fourier Series and Number Theory",
        "Analog and Digital Communication",
        "Design and Analysis of Algorithms",
        "Database Management Systems",
        "Object Oriented Programming using Java",
        "Digital Logic and Computer Architecture",
    }


def test_me_and_it_semester_three_share_nothing(catalogue):
    me = set(subjects_for(catalogue, "ME", 3).values_list("course_title", flat=True))
    it = set(subjects_for(catalogue, "IT", 3).values_list("course_title", flat=True))
    assert me & it == set()


def test_ge23111_is_two_records_in_mechanical(catalogue):
    """ME runs the code as Engineering Graphics in I and Mechanics in II."""
    rows = {
        s.semester.semester_number: s.course_title
        for s in subjects_for(catalogue, "ME").filter(course_code="GE23111")
    }
    assert rows == {1: "Engineering Graphics", 2: "Engineering Mechanics"}


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #
def test_semester_three_differs_across_every_populated_department(catalogue):
    # Compared on (course code, title) pairs, not titles alone: Mechatronics
    # and Robotics and Automation publish an identical Semester III apart from a
    # single course code, so a title-only comparison would report a false clash.
    per_department = {
        code: frozenset(
            subjects_for(catalogue, code, 3).values_list("course_code", "course_title")
        )
        for code in CURRICULA
    }
    for code, rows in per_department.items():
        assert rows, f"{code} Semester III is empty"
    assert len(set(per_department.values())) == len(CURRICULA)


def test_no_department_holds_a_foreign_subject(catalogue):
    """Every stored subject appears in its own department's syllabus."""
    allowed: dict[str, set[str]] = {}
    for code, curriculum in CURRICULA.items():
        for payload in curriculum.values():
            for _c, title, *_rest in payload["subjects"]:
                allowed.setdefault(title, set()).add(code)

    for title, dept_code in Subject.objects.values_list(
        "course_title", "semester__department__code"
    ):
        assert dept_code in allowed[title], (
            f"{title!r} appears under {dept_code} but is listed only for "
            f"{sorted(allowed[title])}"
        )


@pytest.mark.parametrize(
    "code,foreign_code",
    [
        ("ME", "IT23331"),   # IT's Digital Logic and Computer Architecture
        ("ME", "CS23332"),   # IT's DBMS
        ("IT", "ME23311"),   # ME's Engineering Thermodynamics
        ("IT", "ME23631"),   # ME's Robotics Laboratory
    ],
)
def test_no_foreign_course_is_reachable(catalogue, code, foreign_code):
    assert not subjects_for(catalogue, code).filter(course_code=foreign_code).exists()


def test_api_isolates_the_new_departments(student_api, catalogue):
    for code, expected in [("ME", 50), ("IT", 45)]:
        department = catalogue[code]
        rows = student_api.get(
            "/api/subjects/", {"department": department.id, "page_size": 200}
        ).data
        assert rows["count"] == expected
        assert all(row["department"] == department.id for row in rows["results"])

    assert (
        student_api.get(
            "/api/subjects/", {"department": catalogue["ME"].id, "search": "IT23331"}
        ).data["count"]
        == 0
    )
    assert (
        student_api.get(
            "/api/subjects/", {"department": catalogue["IT"].id, "search": "ME23311"}
        ).data["count"]
        == 0
    )


def test_stats_are_per_department(student_api, catalogue):
    for code, expected in SUBJECT_COUNTS.items():
        stats = student_api.get("/api/stats/", {"department": catalogue[code].id}).data
        assert stats["semesters"] == 8
        assert stats["subjects"] == expected


# --------------------------------------------------------------------------- #
# Regression and resources
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
    """The brief's isolation test: an ME upload and an IT upload stay apart."""
    from conftest import pdf_upload

    me_subject = subjects_for(catalogue, "ME").get(course_code="ME23311")
    it_subject = subjects_for(catalogue, "IT").get(course_code="CS23332")

    for subject, title in [
        (me_subject, "ME Thermodynamics Unit 1"),
        (it_subject, "IT DBMS Unit 1"),
    ]:
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

    me_rows = student_api.get("/api/resources/", {"department": catalogue["ME"].id}).data
    assert me_rows["count"] == 1
    assert me_rows["results"][0]["title"] == "ME Thermodynamics Unit 1"

    it_rows = student_api.get("/api/resources/", {"department": catalogue["IT"].id}).data
    assert it_rows["count"] == 1
    assert it_rows["results"][0]["title"] == "IT DBMS Unit 1"

    # The IT upload must not surface anywhere in Mechanical Engineering.
    assert "IT DBMS Unit 1" not in [r["title"] for r in me_rows["results"]]


def test_student_still_cannot_write_to_the_new_departments(student_api, catalogue):
    from conftest import pdf_upload

    subject = subjects_for(catalogue, "ME").get(course_code="ME23311")
    response = student_api.post(
        "/api/resources/",
        {
            "subject": subject.id,
            "resource_type": "UNIT_1",
            "title": "Forged",
            "file": pdf_upload(),
        },
        format="multipart",
    )
    assert response.status_code == 403
    assert student_api.delete(f"/api/subjects/{subject.id}/").status_code == 403
