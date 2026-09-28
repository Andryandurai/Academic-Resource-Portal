"""Subject catalogue: seeding, filtering, and the read/write permission split."""

from __future__ import annotations

import pytest

from academics.curricula import AIDS_CURRICULUM as CURRICULUM, SUBJECT_COUNTS

SUBJECT_COUNT = SUBJECT_COUNTS["AI&DS"]
from academics.models import Semester, Subject

pytestmark = pytest.mark.django_db


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #
def test_seed_creates_the_whole_syllabus(curriculum):
    assert Semester.objects.count() == 8
    assert Subject.objects.filter(semester__department=curriculum).count() == SUBJECT_COUNT == 39


def test_seed_is_idempotent(curriculum):
    from django.core.management import call_command

    call_command("seed_academics", department="AI&DS", verbosity=0)
    call_command("seed_academics", department="AI&DS", verbosity=0)
    assert Semester.objects.filter(department=curriculum).count() == 8
    assert Subject.objects.filter(semester__department=curriculum).count() == 39


def test_seed_preserves_every_ltpc_value(curriculum):
    for number, payload in CURRICULUM.items():
        for code, title, category, course_type, l, t, p, credits in payload["subjects"]:
            subject = (
                Subject.objects.get(course_code=code)
                if code
                else Subject.objects.get(
                    course_title=title, course_code__isnull=True, semester__semester_number=number
                )
            )
            assert (subject.l, subject.t, subject.p, subject.credits) == (l, t, p, credits)
            assert subject.category == category
            assert subject.course_type == course_type
            assert subject.semester.semester_number == number


def test_electives_keep_a_null_course_code(curriculum):
    """A code is never invented for an elective the syllabus leaves blank."""
    electives = Subject.objects.filter(course_code__isnull=True)
    assert electives.count() == 8
    assert electives.filter(course_title="Professional Elective-I").exists()


def test_no_excluded_course_kinds_were_seeded(curriculum):
    titles = " | ".join(Subject.objects.values_list("course_title", flat=True)).lower()
    for banned in ("laboratory", "internship", "project phase", "non-credit", "employability"):
        assert banned not in titles


def test_only_academic_course_types_exist(curriculum):
    """No bucket exists for non-credit, EEC, internship or project courses."""
    assert set(Subject.objects.values_list("course_type", flat=True)) <= {
        "THEORY",
        "LAB_ORIENTED_THEORY",
        "LABORATORY",
    }


def test_verify_curriculum_command_passes(curriculum):
    from django.core.management import call_command

    call_command("verify_curriculum", department="AI&DS", verbosity=0)


def test_tamil_titles_survive_the_round_trip(curriculum):
    subject = Subject.objects.get(course_code="GE23117")
    assert subject.course_title.startswith("தமிழ")


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #
def test_subject_list_is_open_but_writes_need_faculty(api, curriculum):
    assert api.get("/api/subjects/").status_code == 200
    assert api.post("/api/subjects/", {"course_title": "Forged"}, format="json").status_code == 401


def test_student_can_list_subjects(student_api, curriculum):
    response = student_api.get("/api/subjects/", {"page_size": 200})
    assert response.status_code == 200
    assert response.data["count"] == 39


def test_semesters_carry_their_subject_counts(student_api, curriculum):
    response = student_api.get("/api/semesters/")
    assert response.status_code == 200
    by_number = {row["semester_number"]: row for row in response.data}
    assert by_number[1]["subject_count"] == 6
    assert by_number[8]["subject_count"] == 1


@pytest.mark.parametrize(
    "query,expected_code",
    [
        ({"search": "CS23231"}, "CS23231"),
        ({"search": "cs23231"}, "CS23231"),
        ({"search": "data structures"}, "CS23231"),
        ({"search": "Machine Learning"}, "AI23331"),
    ],
)
def test_search_matches_code_and_title_case_insensitively(
    student_api, curriculum, query, expected_code
):
    response = student_api.get("/api/subjects/", query)
    codes = [row["course_code"] for row in response.data["results"]]
    assert expected_code in codes


def test_filter_by_semester_number(student_api, curriculum):
    response = student_api.get("/api/subjects/", {"semester_number": 8})
    assert response.data["count"] == 1
    assert response.data["results"][0]["course_title"] == "Professional Elective-VI"


def test_filter_by_course_type_and_category(student_api, curriculum):
    theory = student_api.get("/api/subjects/", {"course_type": "THEORY", "page_size": 200})
    assert all(row["course_type"] == "THEORY" for row in theory.data["results"])

    electives = student_api.get("/api/subjects/", {"category": "PE", "page_size": 200})
    assert all(row["category"] == "PE" for row in electives.data["results"])


def test_resource_counts_endpoint_returns_all_eight_categories(student_api, data_structures):
    response = student_api.get(f"/api/subjects/{data_structures.id}/resource-counts/")
    assert response.status_code == 200
    assert set(response.data) == {
        "UNIT_1",
        "UNIT_2",
        "UNIT_3",
        "UNIT_4",
        "UNIT_5",
        "CAT_1",
        "CAT_2",
        "SEMESTER_EXAM",
    }
    assert all(value == 0 for value in response.data.values())


def test_stats_are_computed_not_invented(student_api, curriculum):
    response = student_api.get("/api/stats/")
    assert response.data["semesters"] == 8
    assert response.data["subjects"] == 39
    assert response.data["resources"] == 0
    assert response.data["exam_resources"] == 0


# --------------------------------------------------------------------------- #
# Writing — administrators only
# --------------------------------------------------------------------------- #
SUBJECT_PAYLOAD = {
    "course_code": "ZZ99999",
    "course_title": "Test Subject",
    "category": "PC",
    "course_type": "THEORY",
    "l": 3,
    "t": 0,
    "p": 0,
    "credits": 3,
}


def test_student_cannot_create_a_subject(student_api, curriculum):
    semester = Semester.objects.get(semester_number=1)
    response = student_api.post(
        "/api/subjects/", {**SUBJECT_PAYLOAD, "semester": semester.id}, format="json"
    )
    assert response.status_code == 403
    assert not Subject.objects.filter(course_code="ZZ99999").exists()


def test_student_cannot_update_or_delete_a_subject(student_api, data_structures):
    assert (
        student_api.patch(
            f"/api/subjects/{data_structures.id}/", {"credits": 99}, format="json"
        ).status_code
        == 403
    )
    assert student_api.delete(f"/api/subjects/{data_structures.id}/").status_code == 403
    data_structures.refresh_from_db()
    assert data_structures.credits == 5


def test_admin_can_create_update_and_delete_a_subject(admin_api, curriculum):
    semester = Semester.objects.get(semester_number=1)

    created = admin_api.post(
        "/api/subjects/", {**SUBJECT_PAYLOAD, "semester": semester.id}, format="json"
    )
    assert created.status_code == 201
    subject_id = created.data["id"]

    updated = admin_api.patch(
        f"/api/subjects/{subject_id}/", {"course_title": "Renamed Subject"}, format="json"
    )
    assert updated.status_code == 200
    assert updated.data["course_title"] == "Renamed Subject"

    assert admin_api.delete(f"/api/subjects/{subject_id}/").status_code == 204
    assert not Subject.objects.filter(id=subject_id).exists()


def test_duplicate_course_code_is_rejected(admin_api, curriculum):
    """Uniqueness is per semester — HS23111 already sits in AI&DS Semester I."""
    semester = Semester.objects.get(semester_number=1, department=curriculum)
    response = admin_api.post(
        "/api/subjects/",
        {**SUBJECT_PAYLOAD, "course_code": "HS23111", "semester": semester.id},
        format="json",
    )
    assert response.status_code == 400
    assert "course_code" in response.data


def test_same_course_code_is_allowed_in_another_department(admin_api, curriculum):
    """Departments share first-year codes; the constraint must not block that."""
    from academics.models import Department

    other = Department.objects.create(name="Test Department", code="TD")
    other_semester = Semester.objects.create(
        department=other, semester_number=1, name="Semester I"
    )
    response = admin_api.post(
        "/api/subjects/",
        {**SUBJECT_PAYLOAD, "course_code": "HS23111", "semester": other_semester.id},
        format="json",
    )
    assert response.status_code == 201, response.data


def test_blank_course_code_is_stored_as_null(admin_api, curriculum):
    semester = Semester.objects.get(semester_number=5)
    response = admin_api.post(
        "/api/subjects/",
        {**SUBJECT_PAYLOAD, "course_code": "", "course_title": "Elective X", "semester": semester.id},
        format="json",
    )
    assert response.status_code == 201
    assert Subject.objects.get(id=response.data["id"]).course_code is None


def test_theory_course_may_not_carry_practical_periods(admin_api, curriculum):
    semester = Semester.objects.get(semester_number=1)
    response = admin_api.post(
        "/api/subjects/",
        {**SUBJECT_PAYLOAD, "course_code": "ZZ88888", "p": 4, "semester": semester.id},
        format="json",
    )
    assert response.status_code == 400
    assert "p" in response.data


def test_invalid_category_is_rejected(admin_api, curriculum):
    semester = Semester.objects.get(semester_number=1)
    response = admin_api.post(
        "/api/subjects/",
        {**SUBJECT_PAYLOAD, "course_code": "ZZ77777", "category": "XX", "semester": semester.id},
        format="json",
    )
    assert response.status_code == 400
    assert "category" in response.data
