"""The Department -> Semester -> Course -> Unit cascade.

The cascade is composed on the frontend out of endpoints that already existed,
so nothing here tests new API surface. What it pins is the contract those four
requests rely on: each level, queried with the level above it as its scope, must
return options belonging *only* to that scope. If that ever stops holding, the
filter silently starts offering another department's semesters.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA
from academics.models import Department, Subject
from resources.models import ResourceType

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogue(db):
    from django.core.management import call_command

    call_command("seed_departments", verbosity=0)
    call_command("seed_academics", verbosity=0)
    return {d.code: d for d in Department.objects.all()}


# --------------------------------------------------------------------------- #
# Level 1 — Department -> Semester
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("code", sorted(CURRICULA))
def test_semester_options_belong_only_to_the_chosen_department(student_api, catalogue, code):
    department = catalogue[code]
    rows = student_api.get("/api/semesters/", {"department": department.id}).data
    rows = rows["results"] if isinstance(rows, dict) else rows

    assert rows, f"{code} offers no semesters"
    assert all(row["department"] == department.id for row in rows)
    assert sorted(row["semester_number"] for row in rows) == [1, 2, 3, 4, 5, 6, 7, 8]


def test_a_department_without_a_syllabus_offers_no_semesters(student_api, catalogue):
    """The picker omits these, but the endpoint must not invent options either.

    Every canonical department now carries a syllabus, so the empty one is
    created here rather than selected — the endpoint must still answer with an
    empty list rather than inventing options.
    """
    empty = Department.objects.create(name="Unseeded (cascade test)", code="NONE")
    rows = student_api.get("/api/semesters/", {"department": empty.id}).data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert rows == []


# --------------------------------------------------------------------------- #
# Level 2 — Department + Semester -> Course
# --------------------------------------------------------------------------- #
def test_course_options_belong_only_to_the_chosen_department_and_semester(
    student_api, catalogue
):
    for code in ["CSE", "CSE-CS", "FT", "MCT", "RA", "IT", "ECE", "CSD"]:
        department = catalogue[code]
        for semester in department.semesters.all():
            rows = student_api.get(
                "/api/subjects/",
                {"department": department.id, "semester": semester.id, "page_size": 200},
            ).data
            assert rows["count"] == semester.subjects.count()
            for row in rows["results"]:
                assert row["department"] == department.id
                assert row["semester"] == semester.id


def test_a_semester_from_another_department_yields_nothing(student_api, catalogue):
    """The pair is validated in the database, not trusted from the client.

    The frontend cannot produce this combination, but a hand-edited request can:
    it must return an empty list, never fall back to ignoring one of the two.
    """
    cse_semester = catalogue["CSE"].semesters.get(semester_number=3)
    rows = student_api.get(
        "/api/subjects/", {"department": catalogue["FT"].id, "semester": cse_semester.id}
    ).data
    assert rows["count"] == 0


# --------------------------------------------------------------------------- #
# Level 3 — Course -> Unit
# --------------------------------------------------------------------------- #
def test_every_course_offers_all_eight_units(student_api, catalogue):
    """Unit is the resource category, and all eight always exist for a course."""
    expected = sorted(choice for choice, _ in ResourceType.choices)
    assert len(expected) == 8

    for code in ["CSE", "FT"]:
        for subject in Subject.objects.filter(semester__department=catalogue[code])[:5]:
            counts = student_api.get(f"/api/subjects/{subject.id}/resource-counts/").data
            assert sorted(counts) == expected
            assert all(isinstance(value, int) for value in counts.values())


# --------------------------------------------------------------------------- #
# Level 4 — the full path, and every partial one
# --------------------------------------------------------------------------- #
@pytest.fixture
def uploaded(admin_api, catalogue):
    """Four files spread across two departments, two semesters and two units."""
    from conftest import pdf_upload

    cse = catalogue["CSE"]
    dbms = Subject.objects.get(semester__department=cse, course_code="CS23332")
    web = Subject.objects.get(semester__department=cse, course_code="CS23531")
    microbiology = Subject.objects.get(
        semester__department=catalogue["FT"], course_code="FT23301"
    )

    rows = [
        (dbms, "UNIT_2", "DBMS Unit 2"),
        (dbms, "UNIT_1", "DBMS Unit 1"),
        (web, "UNIT_2", "Web Programming Unit 2"),
        (microbiology, "UNIT_2", "Food Microbiology Unit 2"),
    ]
    for subject, unit, title in rows:
        response = admin_api.post(
            "/api/resources/",
            {
                "subject": subject.id,
                "resource_type": unit,
                "title": title,
                "file": pdf_upload(name=f"{title}.pdf"),
            },
            format="multipart",
        )
        assert response.status_code == 201, response.data

    return {"cse": cse, "dbms": dbms, "web": web, "microbiology": microbiology}


def titles(response):
    return sorted(row["title"] for row in response.data["results"])


def test_the_briefs_full_path(student_api, catalogue, uploaded):
    """CSE -> Semester III -> Database Management Systems -> Unit 2."""
    dbms = uploaded["dbms"]
    response = student_api.get(
        "/api/resources/",
        {
            "department": uploaded["cse"].id,
            "semester": dbms.semester_id,
            "subject": dbms.id,
            "resource_type": "UNIT_2",
        },
    )
    assert titles(response) == ["DBMS Unit 2"]


def test_partial_paths_widen_correctly(student_api, catalogue, uploaded):
    cse, dbms = uploaded["cse"], uploaded["dbms"]

    # Department only — everything CSE has published.
    assert titles(student_api.get("/api/resources/", {"department": cse.id})) == [
        "DBMS Unit 1",
        "DBMS Unit 2",
        "Web Programming Unit 2",
    ]
    # Department + semester.
    assert titles(
        student_api.get(
            "/api/resources/", {"department": cse.id, "semester": dbms.semester_id}
        )
    ) == ["DBMS Unit 1", "DBMS Unit 2"]
    # Department + semester + course, unit left open.
    assert titles(
        student_api.get(
            "/api/resources/",
            {"department": cse.id, "semester": dbms.semester_id, "subject": dbms.id},
        )
    ) == ["DBMS Unit 1", "DBMS Unit 2"]


def test_search_narrows_the_filtered_path_rather_than_replacing_it(
    student_api, catalogue, uploaded
):
    cse, dbms = uploaded["cse"], uploaded["dbms"]

    assert titles(student_api.get("/api/resources/", {"department": cse.id, "search": "Unit 2"})) == [
        "DBMS Unit 2",
        "Web Programming Unit 2",
    ]
    assert titles(
        student_api.get(
            "/api/resources/",
            {"department": cse.id, "semester": dbms.semester_id, "search": "Unit 2"},
        )
    ) == ["DBMS Unit 2"]
    # A term that matches only another department's file must stay invisible.
    assert (
        student_api.get(
            "/api/resources/", {"department": cse.id, "search": "Microbiology"}
        ).data["count"]
        == 0
    )


def test_the_cascade_cannot_reach_another_departments_resources(
    student_api, catalogue, uploaded
):
    food = catalogue["FT"]
    assert titles(student_api.get("/api/resources/", {"department": food.id})) == [
        "Food Microbiology Unit 2"
    ]
    assert (
        student_api.get("/api/resources/", {"department": food.id, "search": "DBMS"}).data["count"]
        == 0
    )
    # A department paired with a foreign semester resolves to nothing.
    assert (
        student_api.get(
            "/api/resources/",
            {"department": food.id, "semester": uploaded["dbms"].semester_id},
        ).data["count"]
        == 0
    )


def test_selecting_a_unit_with_nothing_in_it_returns_empty_not_everything(
    student_api, catalogue, uploaded
):
    dbms = uploaded["dbms"]
    response = student_api.get(
        "/api/resources/",
        {"department": uploaded["cse"].id, "subject": dbms.id, "resource_type": "CAT_1"},
    )
    assert response.data["count"] == 0


def test_the_cascade_grants_a_student_no_write_access(student_api, catalogue, uploaded):
    resource_id = student_api.get(
        "/api/resources/", {"department": uploaded["cse"].id}
    ).data["results"][0]["id"]
    assert student_api.delete(f"/api/resources/{resource_id}/").status_code == 403
