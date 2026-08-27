"""Aeronautical, Automobile and Biotechnology curricula.

Asserts all three syllabi were seeded exactly, that every non-credit / EEC /
internship / project course stayed out, that the Aeronautical department was
recoded from AE to AERO in place rather than duplicated, and that the fourteen
previously populated departments were not disturbed.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseType, Department, Subject

pytestmark = pytest.mark.django_db

NEW = ["AERO", "AUTO", "BT"]
EXISTING = {
    "AI&DS": 39, "AI&ML": 45, "EEE": 51, "BME": 50,
    "CIVIL": 51, "CSE": 44, "ECE": 46, "CSD": 43,
    "ME": 50, "IT": 45, "MCT": 52, "RA": 49,
    "CSE-CS": 43, "FT": 52,
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


def titles(catalogue, code, semester_number=None):
    return set(
        subjects_for(catalogue, code, semester_number).values_list("course_title", flat=True)
    )


# --------------------------------------------------------------------------- #
# Departments
# --------------------------------------------------------------------------- #
def test_all_three_departments_exist_with_the_requested_codes(catalogue):
    assert catalogue["AERO"].name == "Aeronautical Engineering"
    assert catalogue["AUTO"].name == "Automobile Engineering"
    assert catalogue["BT"].name == "Biotechnology"
    assert Department.objects.count() == 19


def test_aeronautical_was_recoded_in_place_not_duplicated(catalogue):
    """AE -> AERO must adopt the existing row, never fork it.

    `seed_departments` falls back to matching on the name, which is what lets a
    code change land on the record that already holds the curriculum.
    """
    matching = Department.objects.filter(name="Aeronautical Engineering")
    assert matching.count() == 1
    assert matching.first().code == "AERO"
    assert not Department.objects.filter(code="AE").exists()


@pytest.mark.parametrize("code", NEW)
def test_eight_semesters_each(catalogue, code):
    assert sorted(
        catalogue[code].semesters.values_list("semester_number", flat=True)
    ) == [1, 2, 3, 4, 5, 6, 7, 8]


@pytest.mark.parametrize("code,expected", [("AERO", 48), ("AUTO", 49), ("BT", 55)])
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
    assert set(subjects_for(catalogue, code).values_list("course_type", flat=True)) == {
        CourseType.THEORY,
        CourseType.LAB_ORIENTED_THEORY,
        CourseType.LABORATORY,
    }


def test_biotechnology_semester_eight_exists_but_is_empty(catalogue):
    """Its only course is BT23822 Capstone Project, which is an EEC course."""
    semester = catalogue["BT"].semesters.get(semester_number=8)
    assert semester.name == "Semester VIII"
    assert semester.subjects.count() == 0
    assert not subjects_for(catalogue, "BT").filter(course_title="Capstone Project").exists()


# --------------------------------------------------------------------------- #
# Every course code the brief asked to be checked
# --------------------------------------------------------------------------- #
AERO_CODES = """AE23211 AE23331 AE23332 AE23333 AE23411 AE23412 AE23431 AE23432
AE23433 AE23511 AE23512 AE23513 AE23531 AE23521 AE23611 AE23631 AE23622 AE23623
AE23731 AE23711 AE23722""".split()

AUTO_CODES = """AT23111 AT23331 AT23332 AT23333 AT23334 AT23321 AT23411 AT23412
AT23431 AT23432 AT23433 AT23511 AT23531 AT23532 AT23521 AT23522 AT23631 AT23632
AT23633 AT23711 AT23712 AT23713 AT23721 AT23722 AT23723""".split()

BT_CODES = """BT23131 BT23211 BT23221 BT23311 BT23312 BT23313 BT23314 BT23321
BT23331 BT23411 BT23412 BT23413 BT23414 BT23421 BT23422 BT23511 BT23512 BT23513
BT23514 BT23521 BT23522 BT23523 BT23611 BT23612 BT23621 BT23622 BT23711 BT23712
BT23713 BT23721 BT23722""".split()


@pytest.mark.parametrize(
    "code,expected_codes",
    [("AERO", AERO_CODES), ("AUTO", AUTO_CODES), ("BT", BT_CODES)],
)
def test_every_departmental_course_code_is_present_exactly_once(
    catalogue, code, expected_codes
):
    stored = list(
        subjects_for(catalogue, code)
        .exclude(course_code__isnull=True)
        .values_list("course_code", flat=True)
    )
    for expected in expected_codes:
        assert stored.count(expected) == 1, f"{code}: {expected} appears {stored.count(expected)}x"


@pytest.mark.parametrize(
    "code,course_code,title,semester,category,ltpc",
    [
        ("AERO", "AE23431", "Incompressible Aerodynamics", 4, "PC", (2, 1, 2, 4)),
        ("AERO", "AE23513", "Flight Dynamics", 5, "PC", (3, 1, 0, 4)),
        ("AERO", "AE23623", "Airframe Repair and Aero Engine Laboratory", 6, "PC", (0, 0, 4, 2)),
        ("AUTO", "AT23532", "Electric and Hybrid Vehicles - II", 5, "PC", (3, 0, 2, 4)),
        ("AUTO", "AT23632", "Vehicle Dynamics", 6, "PC", (2, 1, 2, 4)),
        ("AUTO", "AT23111", "Production Technology", 1, "PC", (3, 0, 0, 3)),
        ("BT", "BT23512", "Bioinformatics", 5, "PC", (3, 0, 0, 3)),
        ("BT", "BT23131", "Microbiology", 1, "PC", (2, 0, 4, 4)),
        ("BT", "BT23713", "Comprehension in Biotechnology", 7, "PC", (2, 0, 0, 2)),
    ],
)
def test_named_courses_are_exact(
    catalogue, code, course_code, title, semester, category, ltpc
):
    subject = subjects_for(catalogue, code).get(course_code=course_code)
    assert subject.course_title == title
    assert subject.semester.semester_number == semester
    assert subject.category == category
    assert (subject.l, subject.t, subject.p, subject.credits) == ltpc


def test_electives_carry_no_invented_code(catalogue):
    for code, expected in [("AERO", 8), ("AUTO", 7), ("BT", 8)]:
        blank = subjects_for(catalogue, code).filter(course_code__isnull=True)
        assert blank.count() == expected
        assert all(
            row.startswith(("Professional Elective", "Open Elective"))
            for row in blank.values_list("course_title", flat=True)
        )


def test_aeronautical_electives_use_one_consistent_spelling(catalogue):
    """The source prints one elective with an en dash and the rest with a hyphen.

    Normalised to the department's dominant form, so a single elective series
    does not appear under two spellings in the filter bar.
    """
    blank = set(
        subjects_for(catalogue, "AERO")
        .filter(course_code__isnull=True)
        .values_list("course_title", flat=True)
    )
    assert blank == {
        "Open Elective - I",
        "Open Elective - II",
        "Professional Elective - I",
        "Professional Elective - II",
        "Professional Elective - III",
        "Professional Elective - IV",
        "Professional Elective - V",
        "Professional Elective - VI",
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
        ("AERO", "Environmental Science and Engineering"),
        ("AERO", "Indian Constitution and Freedom Movement"),
        ("AERO", "Internship"),
        ("AERO", "Project Work Phase I"),
        ("AERO", "Project Work Phase II"),
        ("AUTO", "Industrial Training"),
        ("AUTO", "Internship"),
        ("AUTO", "Project Work"),
        ("BT", "Professional Internship"),
        ("BT", "Capstone Project"),
        ("BT", "Environmental Science and Engineering"),
    ],
)
def test_named_excluded_titles_are_absent(catalogue, code, title):
    assert not subjects_for(catalogue, code).filter(course_title=title).exists()


@pytest.mark.parametrize("code", NEW)
def test_no_zero_credit_course_reached_the_database(catalogue, code):
    assert not subjects_for(catalogue, code).filter(credits=0).exists()


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #
def test_semester_three_still_differs_across_every_populated_department(catalogue):
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
        ("AERO", "AT23532"),   # Automobile's Electric and Hybrid Vehicles - II
        ("AERO", "BT23512"),   # Biotechnology's Bioinformatics
        ("AUTO", "AE23431"),   # Aeronautical's Incompressible Aerodynamics
        ("AUTO", "BT23131"),   # Biotechnology's Microbiology
        ("BT", "AE23731"),     # Aeronautical's Avionics
        ("BT", "AT23632"),     # Automobile's Vehicle Dynamics
    ],
)
def test_no_foreign_course_is_reachable(catalogue, code, foreign_code):
    assert not subjects_for(catalogue, code).filter(course_code=foreign_code).exists()


def test_api_isolates_the_three_new_departments(student_api, catalogue):
    for code, expected in [("AERO", 48), ("AUTO", 49), ("BT", 55)]:
        department = catalogue[code]
        rows = student_api.get(
            "/api/subjects/", {"department": department.id, "page_size": 200}
        ).data
        assert rows["count"] == expected
        assert all(row["department"] == department.id for row in rows["results"])


# --------------------------------------------------------------------------- #
# The brief's search and cascade tests
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "term,code,title",
    [
        ("AE23431", "AERO", "Incompressible Aerodynamics"),
        ("AT23632", "AUTO", "Vehicle Dynamics"),
        ("BT23512", "BT", "Bioinformatics"),
        ("Incompressible Aerodynamics", "AERO", "Incompressible Aerodynamics"),
        ("Bioinformatics", "BT", "Bioinformatics"),
    ],
)
def test_search_finds_the_new_courses(student_api, catalogue, term, code, title):
    rows = student_api.get("/api/subjects/", {"search": term, "page_size": 200}).data
    found = [r for r in rows["results"] if r["course_title"] == title]
    assert found, f"{term!r} did not find {title}"
    assert any(r["department_code"] == code for r in found)


@pytest.mark.parametrize(
    "term,code,expected",
    [
        ("Aeronautical", "AERO", 48),
        ("Automobile", "AUTO", 49),
        ("Biotechnology", "BT", 55),
    ],
)
def test_department_search_reaches_the_new_departments(student_api, catalogue, term, code, expected):
    rows = student_api.get(
        "/api/subjects/", {"department_search": term, "page_size": 200}
    ).data
    assert rows["count"] == expected
    assert {r["department_code"] for r in rows["results"]} == {code}


def test_the_briefs_cascade_paths(student_api, catalogue):
    """TEST 1, 2 and 3 from the brief, walked through the API."""
    checks = [
        ("AERO", 1, "Engineering Graphics", "GE23111"),
        ("AUTO", 5, "Electric and Hybrid Vehicles - II", "AT23532"),
        ("BT", 5, "Bioinformatics", "BT23512"),
    ]
    for code, number, title, course_code in checks:
        semester = catalogue[code].semesters.get(semester_number=number)
        rows = student_api.get(
            "/api/subjects/",
            {"department": catalogue[code].id, "semester": semester.id, "page_size": 200},
        ).data
        # Only that department's semester is returned...
        assert rows["count"] == semester.subjects.count()
        assert all(r["department"] == catalogue[code].id for r in rows["results"])
        # ...and it contains the course the brief names, with the right code.
        match = [r for r in rows["results"] if r["course_title"] == title]
        assert len(match) == 1, f"{code} Semester {number} is missing {title}"
        assert match[0]["course_code"] == course_code


def test_facets_offer_the_three_new_departments(student_api, catalogue):
    data = student_api.get("/api/subjects/facets/").data
    by_code = {d["code"]: d for d in data["departments"]}
    for code in NEW:
        assert by_code[code]["total"] == SUBJECT_COUNTS[code]
    assert data["total"] == sum(SUBJECT_COUNTS.values())


# --------------------------------------------------------------------------- #
# Regression
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("code,expected", list(EXISTING.items()))
def test_previously_populated_departments_are_untouched(catalogue, code, expected):
    assert subjects_for(catalogue, code).count() == expected


def test_only_departments_with_a_syllabus_report_curriculum(student_api, catalogue):
    rows = student_api.get("/api/departments/").data
    ready = sorted(row["code"] for row in rows if row["has_curriculum"])
    assert ready == sorted(CURRICULA)
    assert sum(1 for row in rows if not row["has_curriculum"]) == 19 - len(CURRICULA)


def test_the_new_departments_appear_in_the_selector(student_api, catalogue):
    listed = {row["code"]: row for row in student_api.get("/api/departments/").data}
    for code in NEW:
        assert listed[code]["is_active"] is True
        assert listed[code]["has_curriculum"] is True
        assert listed[code]["semester_count"] == 8
        assert listed[code]["subject_count"] == SUBJECT_COUNTS[code]


def test_seed_is_idempotent_across_all_departments(catalogue):
    from django.core.management import call_command

    from academics.models import Semester

    call_command("seed_departments", verbosity=0)
    call_command("seed_academics", verbosity=0)
    call_command("seed_academics", verbosity=0)

    assert Department.objects.count() == 19
    assert Subject.objects.count() == sum(SUBJECT_COUNTS.values())
    assert Semester.objects.count() == 8 * len(CURRICULA)
    for code in NEW:
        assert subjects_for(catalogue, code).count() == SUBJECT_COUNTS[code]


def test_verify_curriculum_passes_for_all(catalogue):
    from django.core.management import call_command

    call_command("verify_curriculum", verbosity=0)


def test_resources_stay_within_the_new_departments(admin_api, student_api, catalogue):
    from conftest import pdf_upload

    aero = subjects_for(catalogue, "AERO").get(course_code="AE23431")
    bio = subjects_for(catalogue, "BT").get(course_code="BT23512")

    for subject, title in [(aero, "Aerodynamics Unit 1"), (bio, "Bioinformatics Unit 1")]:
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

    aero_rows = student_api.get("/api/resources/", {"department": catalogue["AERO"].id}).data
    assert [r["title"] for r in aero_rows["results"]] == ["Aerodynamics Unit 1"]

    bt_rows = student_api.get("/api/resources/", {"department": catalogue["BT"].id}).data
    assert [r["title"] for r in bt_rows["results"]] == ["Bioinformatics Unit 1"]

    assert (
        student_api.get("/api/resources/", {"department": catalogue["AUTO"].id}).data["count"] == 0
    )


def test_student_cannot_write_to_the_new_departments(student_api, catalogue):
    from conftest import pdf_upload

    for code, course_code in [("AERO", "AE23431"), ("AUTO", "AT23632"), ("BT", "BT23512")]:
        subject = subjects_for(catalogue, code).get(course_code=course_code)
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
