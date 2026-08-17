"""Departments: seeding, search, and isolation between departments.

The point of the department layer is that one department's material can never
surface under another. These tests assert that at the query level, not by
checking what a UI happens to render.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA
from academics.departments import DEPARTMENT_COUNT, DEPARTMENTS
from academics.models import Department, Semester, Subject

pytestmark = pytest.mark.django_db


@pytest.fixture
def departments(db):
    from django.core.management import call_command

    call_command("seed_departments", verbosity=0)
    return Department.objects.all()


@pytest.fixture
def full_catalogue(db):
    """All 19 departments, with AI&DS carrying the seeded curriculum."""
    from django.core.management import call_command

    call_command("seed_departments", verbosity=0)
    call_command("seed_academics", verbosity=0)
    return Department.objects.get(code="AI&DS")


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #
def test_seeds_exactly_nineteen_departments(departments):
    assert Department.objects.count() == DEPARTMENT_COUNT == 19


def test_seed_is_idempotent(departments):
    from django.core.management import call_command

    call_command("seed_departments", verbosity=0)
    call_command("seed_departments", verbosity=0)
    assert Department.objects.count() == 19


def test_every_named_department_is_present(departments):
    stored = set(Department.objects.values_list("name", flat=True))
    for name, _code, _group in DEPARTMENTS:
        assert name in stored


def test_department_codes_are_unique(departments):
    codes = list(Department.objects.values_list("code", flat=True))
    assert len(codes) == len(set(codes)) == 19


def test_seeding_departments_does_not_create_curriculum(departments):
    """seed_departments creates department records only — never curriculum."""
    assert Semester.objects.count() == 0
    assert Subject.objects.count() == 0


def test_existing_aids_department_is_reused_not_duplicated(curriculum):
    """The AI&DS record already owns the curriculum before departments seed."""
    from django.core.management import call_command

    original = Department.objects.get(code="AI&DS")
    assert original.semesters.count() == 8

    call_command("seed_departments", verbosity=0)

    reused = Department.objects.get(code="AI&DS")
    assert reused.id == original.id
    assert Department.objects.filter(code="AI&DS").count() == 1
    # The curriculum survives the rename intact.
    assert reused.name == "Artificial Intelligence and Data Science"
    assert reused.semesters.count() == 8
    assert Subject.objects.filter(semester__department=reused).count() == 39


def test_seed_academics_after_departments_keeps_one_department(departments):
    from django.core.management import call_command

    call_command("seed_academics", verbosity=0)
    assert Department.objects.filter(code="AI&DS").count() == 1
    assert Department.objects.count() == 19
    assert Subject.objects.filter(semester__department__code="AI&DS").count() == 39


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
def test_department_list_requires_authentication(api, departments):
    assert api.get("/api/departments/").status_code == 401


def test_student_can_list_departments(student_api, full_catalogue):
    response = student_api.get("/api/departments/")
    assert response.status_code == 200
    assert len(response.data) == 19

    payload = {row["code"]: row for row in response.data}
    assert payload["AI&DS"]["name"] == "Artificial Intelligence and Data Science"
    assert set(payload["AI&DS"]) == {
        "id",
        "name",
        "code",
        "is_active",
        "has_curriculum",
        "semester_count",
        "subject_count",
    }


def test_departments_are_alphabetical(student_api, departments):
    names = [row["name"] for row in student_api.get("/api/departments/").data]
    assert names == sorted(names)


def test_only_aids_reports_curriculum(student_api, full_catalogue):
    rows = student_api.get("/api/departments/").data
    ready = [row for row in rows if row["has_curriculum"]]

    assert sorted(row["code"] for row in ready) == sorted(CURRICULA)
    for row in ready:
        assert row["semester_count"] == 8 and row["subject_count"] > 0
    # Every department without a syllabus is honestly empty.
    for row in rows:
        if row["code"] not in CURRICULA:
            assert row["semester_count"] == 0 and row["subject_count"] == 0


@pytest.mark.parametrize(
    "term,expected_codes",
    [
        ("Artificial", {"AI&DS", "AI&ML"}),
        ("artificial", {"AI&DS", "AI&ML"}),
        ("CSE", {"CSE", "CSE-CS"}),
        ("cse", {"CSE", "CSE-CS"}),
        ("Computer Science", {"CSBS", "CSD", "CSE", "CSE-CS"}),
        ("mechanical", {"ME"}),
        ("ROBOT", {"RA"}),
    ],
)
def test_department_search_is_case_insensitive(student_api, departments, term, expected_codes):
    rows = student_api.get("/api/departments/", {"search": term}).data
    assert {row["code"] for row in rows} == expected_codes


def test_search_matches_code_as_well_as_name(student_api, departments):
    rows = student_api.get("/api/departments/", {"search": "EEE"}).data
    assert [row["name"] for row in rows] == ["Electrical and Electronics Engineering"]


def test_departments_are_read_only_over_the_api(admin_api, departments):
    """Departments are seeded data, not user-generated content."""
    department = Department.objects.first()
    assert admin_api.post("/api/departments/", {"name": "Fake", "code": "FK"}).status_code == 405
    assert admin_api.delete(f"/api/departments/{department.id}/").status_code == 405


# --------------------------------------------------------------------------- #
# Department scoping
# --------------------------------------------------------------------------- #
def test_semesters_are_department_scoped(student_api, full_catalogue, empty_department):
    aids = full_catalogue
    mechanical = empty_department

    ai_semesters = student_api.get("/api/semesters/", {"department": aids.id}).data
    assert len(ai_semesters) == 8
    assert all(row["department"] == aids.id for row in ai_semesters)

    # A department without a syllabus returns nothing — not another's semesters.
    assert student_api.get("/api/semesters/", {"department": mechanical.id}).data == []


def test_subjects_are_department_scoped(student_api, full_catalogue, empty_department):
    aids = full_catalogue
    mechanical = empty_department

    mine = student_api.get("/api/subjects/", {"department": aids.id, "page_size": 200}).data
    assert mine["count"] == 39
    assert all(row["department"] == aids.id for row in mine["results"])

    theirs = student_api.get("/api/subjects/", {"department": mechanical.id}).data
    assert theirs["count"] == 0


def test_subject_search_cannot_cross_department_boundaries(student_api, full_catalogue, empty_department):
    """CS23231 exists — but not in a department with no syllabus."""
    mechanical = empty_department
    response = student_api.get(
        "/api/subjects/", {"department": mechanical.id, "search": "CS23231"}
    )
    assert response.data["count"] == 0


def test_department_scoping_by_code(student_api, full_catalogue):
    response = student_api.get("/api/subjects/", {"department_code": "ai&ds", "page_size": 200})
    assert response.data["count"] == 39


def test_resources_are_department_scoped(admin_api, student_api, full_catalogue, empty_department):
    from conftest import pdf_upload

    subject = Subject.objects.get(course_code="CS23231", semester__department=full_catalogue)
    created = admin_api.post(
        "/api/resources/",
        {
            "subject": subject.id,
            "resource_type": "UNIT_1",
            "title": "Unit 1 Complete Notes",
            "file": pdf_upload(),
        },
        format="multipart",
    )
    assert created.status_code == 201

    aids = full_catalogue
    mechanical = empty_department

    assert student_api.get("/api/resources/", {"department": aids.id}).data["count"] == 1
    # The resource belongs to AI&DS through Subject -> Semester -> Department and
    # cannot be reached by asking for another department.
    assert student_api.get("/api/resources/", {"department": mechanical.id}).data["count"] == 0
    assert (
        len(student_api.get("/api/resources/recent/", {"department": mechanical.id}).data) == 0
    )


def test_stats_are_department_scoped(student_api, full_catalogue, empty_department):
    aids = full_catalogue
    mechanical = empty_department

    mine = student_api.get("/api/stats/", {"department": aids.id}).data
    assert (mine["semesters"], mine["subjects"]) == (8, 39)

    empty = student_api.get("/api/stats/", {"department": mechanical.id}).data
    assert (empty["semesters"], empty["subjects"], empty["resources"]) == (0, 0, 0)


def test_stats_rejects_a_non_numeric_department(student_api, full_catalogue):
    assert student_api.get("/api/stats/", {"department": "'; DROP TABLE"}).status_code == 400


def test_unscoped_queries_still_work(student_api, full_catalogue):
    """Omitting the department is college-wide, not an error."""
    from academics.curricula import SUBJECT_COUNTS

    assert student_api.get("/api/stats/").data["subjects"] == sum(SUBJECT_COUNTS.values())
    assert len(student_api.get("/api/semesters/").data) == 8 * len(SUBJECT_COUNTS)
