"""Computer Science and Business Systems, and Chemical Engineering.

The last two departments. Beyond the usual per-field verification, this module
pins two things the earlier departments never exercised: the new MS
(Management Studies) category, and the fact that the college now has no
department left without a syllabus.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseCategory, CourseType, Department, Subject

pytestmark = pytest.mark.django_db

NEW = ["CSBS", "CHEM"]
EXISTING = {
    "AI&DS": 39, "AI&ML": 45, "EEE": 51, "BME": 50,
    "CIVIL": 51, "CSE": 44, "ECE": 46, "CSD": 43,
    "ME": 50, "IT": 45, "MCT": 52, "RA": 49,
    "CSE-CS": 43, "FT": 52, "AERO": 48, "AUTO": 49, "BT": 55,
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
# Departments
# --------------------------------------------------------------------------- #
def test_both_departments_exist_and_were_reused(catalogue):
    assert catalogue["CSBS"].name == "Computer Science and Business Systems"
    assert catalogue["CHEM"].name == "Chemical Engineering"
    assert Department.objects.count() == 19


def test_every_department_now_has_a_syllabus(catalogue):
    """The catalogue is complete: nineteen departments, nineteen curricula."""
    assert sorted(CURRICULA) == sorted(catalogue)
    assert len(CURRICULA) == 19
    for code in catalogue:
        assert subjects_for(catalogue, code).exists(), f"{code} has no subjects"


@pytest.mark.parametrize("code", NEW)
def test_eight_semesters_each(catalogue, code):
    assert sorted(
        catalogue[code].semesters.values_list("semester_number", flat=True)
    ) == [1, 2, 3, 4, 5, 6, 7, 8]


@pytest.mark.parametrize("code,expected", [("CSBS", 47), ("CHEM", 51)])
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


# --------------------------------------------------------------------------- #
# The new MS category
# --------------------------------------------------------------------------- #
def test_management_studies_is_a_real_category(catalogue):
    """CSBS is the first department to publish MS courses.

    Added to the model rather than folded into HS, because the category is
    published academic data and rewriting it would misreport the syllabus.
    """
    assert CourseCategory.MS.value == "MS"
    assert CourseCategory("MS").label == "Management Studies"


def test_the_five_management_courses_are_stored_as_ms(catalogue):
    rows = dict(
        subjects_for(catalogue, "CSBS")
        .filter(category="MS")
        .values_list("course_code", "course_title")
    )
    assert rows == {
        "BA23217": "Fundamentals of Economics",
        "BA23412": "Fundamentals of Management",
        "BA23511": "Principles of Financial Management",
        "BA23611": "Financial and Cost Accounting",
        "BA23612": "Business Strategy",
    }


def test_no_other_department_uses_ms(catalogue):
    holders = set(
        Subject.objects.filter(category="MS").values_list(
            "semester__department__code", flat=True
        )
    )
    assert holders == {"CSBS"}


def test_ms_is_filterable_and_searchable(student_api, catalogue):
    rows = student_api.get(
        "/api/subjects/", {"category": "MS", "page_size": 200}
    ).data
    assert rows["count"] == 5
    assert all(row["category_label"] == "Management Studies" for row in rows["results"])

    facets = student_api.get("/api/subjects/facets/").data
    assert "MS" in {c["value"] for c in facets["categories"]}


# --------------------------------------------------------------------------- #
# Course data
# --------------------------------------------------------------------------- #
CSBS_CODES = """HS23112 MA23115 MA23114 CB23131 EE23131 PH23133 MA23211 BA23217
MA23231 CB23231 EC23242 CS23221 HS23225 CB23311 CB23312 CB23331 CB23332 CB23333
CS23333 BA23412 CB23431 CB23432 CB23433 MA23437 HS23421 BA23511 CB23531 CB23532
GE23627 BA23611 BA23612 CB23631 CB23632 CB23633 HS23621 CB23731 CB23732""".split()

CHEM_CODES = """HS23111 MA23112 PH23111 CY23132 GE23111 GE23121 MA23212 CH23211
GE23233 PH23233 EE23133 GE23122 MA23311 CY23334 CH23311 CH23312 CH23313 CH23331
MA23431 CH23411 CH23412 CH23431 CS23422 CH23421 CH23511 CH23512 CH23513 CH23514
CH23521 EC23527 CH23611 CH23612 CH23613 CH23614 CH23621 CH23711 CH23712 CH23713
CH23721 CH23722 CH23723""".split()


@pytest.mark.parametrize("code,expected", [("CSBS", CSBS_CODES), ("CHEM", CHEM_CODES)])
def test_every_course_code_is_present_exactly_once(catalogue, code, expected):
    stored = list(
        subjects_for(catalogue, code)
        .exclude(course_code__isnull=True)
        .values_list("course_code", flat=True)
    )
    for course_code in expected:
        assert stored.count(course_code) == 1, (
            f"{code}: {course_code} appears {stored.count(course_code)} time(s)"
        )
    # Totality is derived from the curriculum rather than from the hand-written
    # list above, which covers only the department-prefixed codes.
    from_syllabus = [
        row[0] for sem in CURRICULA[code].values() for row in sem["subjects"] if row[0]
    ]
    assert sorted(stored) == sorted(from_syllabus)


@pytest.mark.parametrize(
    "code,course_code,title,semester,category,ltpc",
    [
        ("CSBS", "CB23333", "Database Technology", 3, "PC", (3, 0, 2, 4)),
        ("CSBS", "CB23231", "Data Structures and Algorithms", 2, "PC", (2, 1, 4, 5)),
        ("CSBS", "CB23632", "Cloud, Microservices and Application", 6, "PC", (2, 1, 2, 4)),
        ("CSBS", "BA23612", "Business Strategy", 6, "MS", (2, 0, 0, 2)),
        ("CHEM", "CH23613", "Process Control and Instrumentation", 6, "PC", (3, 0, 0, 3)),
        ("CHEM", "CH23331", "Fluid Mechanics for Chemical Engineers", 3, "PC", (3, 0, 2, 4)),
        ("CHEM", "CH23723", "Artificial Intelligence and Machine Learning for Chemical Engineers", 7, "PC", (0, 0, 4, 2)),
        ("CHEM", "EC23527", "Microfluidics Laboratory", 5, "PE", (0, 0, 2, 1)),
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


def test_shared_codes_keep_each_departments_own_category(catalogue):
    """The same code is filed differently by different departments.

    GE23627 is Professional Core in CSBS and EEC in Chemical Engineering, which
    is why one is stored and the other is not. EC23527 is PE here and ES in
    Biotechnology. Each syllabus is the authority for its own department.
    """
    csbs = subjects_for(catalogue, "CSBS").get(course_code="GE23627")
    assert csbs.category == "PC"
    assert not subjects_for(catalogue, "CHEM").filter(course_code="GE23627").exists()

    assert subjects_for(catalogue, "CHEM").get(course_code="EC23527").category == "PE"
    assert subjects_for(catalogue, "BT").get(course_code="EC23527").category == "ES"


def test_electives_carry_no_invented_code(catalogue):
    for code, expected in [("CSBS", 8), ("CHEM", 7)]:
        blank = subjects_for(catalogue, code).filter(course_code__isnull=True)
        assert blank.count() == expected
        assert all(
            row.startswith(("Professional Elective", "Open Elective"))
            for row in blank.values_list("course_title", flat=True)
        )


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
        ("CSBS", "Indian Constitution and Freedom Movement"),
        ("CSBS", "Environmental Sciences"),
        ("CSBS", "Introduction to Innovation, IP Management and Entrepreneurship"),
        ("CSBS", "Internship"),
        ("CSBS", "Project Evaluation I"),
        ("CSBS", "Project Evaluation II"),
        ("CHEM", "Environmental Science and Engineering"),
        ("CHEM", "Industrial Training (2 Weeks)"),
        ("CHEM", "Professional Training for Chemical Engineers"),
        ("CHEM", "Project Work"),
        ("CHEM", "Design Thinking and Innovation"),
    ],
)
def test_named_excluded_titles_are_absent(catalogue, code, title):
    assert not subjects_for(catalogue, code).filter(course_title=title).exists()


@pytest.mark.parametrize("code", NEW)
def test_no_zero_credit_course_reached_the_database(catalogue, code):
    assert not subjects_for(catalogue, code).filter(credits=0).exists()


def test_no_zero_credit_course_exists_anywhere(catalogue):
    """The exclusion rule holds across the whole completed catalogue."""
    assert not Subject.objects.filter(credits=0).exists()


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #
def test_semester_three_still_differs_across_all_nineteen(catalogue):
    per_department = {
        code: frozenset(
            subjects_for(catalogue, code, 3).values_list("course_code", "course_title")
        )
        for code in CURRICULA
    }
    for code, rows in per_department.items():
        assert rows, f"{code} Semester III is empty"
    assert len(set(per_department.values())) == 19


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
        ("CSBS", "CH23613"),   # Chemical's Process Control and Instrumentation
        ("CSBS", "CH23331"),   # Chemical's Fluid Mechanics
        ("CHEM", "CB23333"),   # CSBS's Database Technology
        ("CHEM", "BA23612"),   # CSBS's Business Strategy
    ],
)
def test_no_foreign_course_is_reachable(catalogue, code, foreign_code):
    assert not subjects_for(catalogue, code).filter(course_code=foreign_code).exists()


def test_api_isolates_the_two_new_departments(student_api, catalogue):
    for code, expected in [("CSBS", 47), ("CHEM", 51)]:
        department = catalogue[code]
        rows = student_api.get(
            "/api/subjects/", {"department": department.id, "page_size": 200}
        ).data
        assert rows["count"] == expected
        assert all(row["department"] == department.id for row in rows["results"])


# --------------------------------------------------------------------------- #
# Search and the cascade
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "term,code,title",
    [
        ("CB23333", "CSBS", "Database Technology"),
        ("Database Technology", "CSBS", "Database Technology"),
        ("CH23613", "CHEM", "Process Control and Instrumentation"),
        ("Process Control and Instrumentation", "CHEM", "Process Control and Instrumentation"),
        ("Business Strategy", "CSBS", "Business Strategy"),
    ],
)
def test_search_finds_the_new_courses(student_api, catalogue, term, code, title):
    rows = student_api.get("/api/subjects/", {"search": term, "page_size": 200}).data
    found = [r for r in rows["results"] if r["course_title"] == title]
    assert found, f"{term!r} did not find {title}"
    assert any(r["department_code"] == code for r in found)


@pytest.mark.parametrize(
    "term,code,expected",
    [("Business Systems", "CSBS", 47), ("Chemical", "CHEM", 51)],
)
def test_department_search_reaches_the_new_departments(
    student_api, catalogue, term, code, expected
):
    rows = student_api.get(
        "/api/subjects/", {"department_search": term, "page_size": 200}
    ).data
    assert rows["count"] == expected
    assert {r["department_code"] for r in rows["results"]} == {code}


def test_the_briefs_cascade_paths(student_api, catalogue):
    """CSBS -> Semester III -> Database Technology, and
    CHEM -> Semester VI -> Process Control and Instrumentation."""
    for code, number, title, course_code in [
        ("CSBS", 3, "Database Technology", "CB23333"),
        ("CHEM", 6, "Process Control and Instrumentation", "CH23613"),
    ]:
        semester = catalogue[code].semesters.get(semester_number=number)
        rows = student_api.get(
            "/api/subjects/",
            {"department": catalogue[code].id, "semester": semester.id, "page_size": 200},
        ).data
        assert rows["count"] == semester.subjects.count()
        assert all(r["department"] == catalogue[code].id for r in rows["results"])
        match = [r for r in rows["results"] if r["course_title"] == title]
        assert len(match) == 1
        assert match[0]["course_code"] == course_code

        # And the course offers the full set of unit containers, all empty.
        counts = student_api.get(
            f"/api/subjects/{match[0]['id']}/resource-counts/"
        ).data
        assert len(counts) == 8
        assert set(counts.values()) == {0}


def test_facets_offer_all_nineteen_departments(student_api, catalogue):
    data = student_api.get("/api/subjects/facets/").data
    by_code = {d["code"]: d for d in data["departments"]}
    assert len(by_code) == 19
    for code in NEW:
        assert by_code[code]["total"] == SUBJECT_COUNTS[code]
    assert data["total"] == sum(SUBJECT_COUNTS.values())


# --------------------------------------------------------------------------- #
# Regression
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("code,expected", list(EXISTING.items()))
def test_previously_populated_departments_are_untouched(catalogue, code, expected):
    assert subjects_for(catalogue, code).count() == expected


def test_every_department_reports_curriculum(student_api, catalogue):
    rows = student_api.get("/api/departments/").data
    assert len(rows) == 19
    assert all(row["has_curriculum"] for row in rows)
    for row in rows:
        assert row["semester_count"] == 8
        assert row["subject_count"] == SUBJECT_COUNTS[row["code"]]


def test_seed_is_idempotent_across_all_departments(catalogue):
    from django.core.management import call_command

    from academics.models import Semester

    call_command("seed_departments", verbosity=0)
    call_command("seed_academics", verbosity=0)
    call_command("seed_academics", verbosity=0)

    assert Department.objects.count() == 19
    assert Subject.objects.count() == sum(SUBJECT_COUNTS.values())
    assert Semester.objects.count() == 8 * 19
    for code in NEW:
        assert subjects_for(catalogue, code).count() == SUBJECT_COUNTS[code]


def test_verify_curriculum_passes_for_all(catalogue):
    from django.core.management import call_command

    call_command("verify_curriculum", verbosity=0)


def test_resources_stay_within_the_new_departments(admin_api, student_api, catalogue):
    from conftest import pdf_upload

    dbtech = subjects_for(catalogue, "CSBS").get(course_code="CB23333")
    control = subjects_for(catalogue, "CHEM").get(course_code="CH23613")

    for subject, title in [(dbtech, "Database Technology Unit 2"), (control, "Process Control Unit 3")]:
        response = admin_api.post(
            "/api/resources/",
            {
                "subject": subject.id,
                "resource_type": "UNIT_2" if subject == dbtech else "UNIT_3",
                "title": title,
                "file": pdf_upload(),
            },
            format="multipart",
        )
        assert response.status_code == 201, response.data

    csbs_rows = student_api.get("/api/resources/", {"department": catalogue["CSBS"].id}).data
    assert [r["title"] for r in csbs_rows["results"]] == ["Database Technology Unit 2"]

    chem_rows = student_api.get("/api/resources/", {"department": catalogue["CHEM"].id}).data
    assert [r["title"] for r in chem_rows["results"]] == ["Process Control Unit 3"]

    assert (
        student_api.get("/api/resources/", {"department": catalogue["CSE"].id}).data["count"] == 0
    )


def test_student_cannot_write_to_the_new_departments(student_api, catalogue):
    from conftest import pdf_upload

    for code, course_code in [("CSBS", "CB23333"), ("CHEM", "CH23613")]:
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
