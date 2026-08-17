"""Biomedical Engineering and Civil Engineering curricula.

Asserts the two new syllabi were seeded exactly, that every excluded
(non-credit / EEC / soft-skills / internship / project) course stayed out, and
that the three existing departments were not disturbed.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseType, Department, Subject

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogue(db):
    """Every department, with all five populated curricula."""
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
# Both departments exist and are populated
# --------------------------------------------------------------------------- #
def test_both_departments_exist_with_the_expected_codes(catalogue):
    assert catalogue["BME"].name == "Biomedical Engineering"
    assert catalogue["CIVIL"].name == "Civil Engineering"
    # Reused, never duplicated.
    assert Department.objects.filter(name="Civil Engineering").count() == 1
    assert Department.objects.filter(name="Biomedical Engineering").count() == 1
    assert Department.objects.count() == 19


@pytest.mark.parametrize("code", ["BME", "CIVIL"])
def test_eight_semesters_each(catalogue, code):
    assert catalogue[code].semesters.count() == 8


@pytest.mark.parametrize("code,expected", [("BME", 50), ("CIVIL", 51)])
def test_subject_totals(catalogue, code, expected):
    assert subjects_for(catalogue, code).count() == SUBJECT_COUNTS[code] == expected


@pytest.mark.parametrize("code", ["BME", "CIVIL"])
def test_every_ltpc_value_matches_the_syllabus(catalogue, code):
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


@pytest.mark.parametrize("code", ["BME", "CIVIL"])
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
@pytest.mark.parametrize("code", ["BME", "CIVIL"])
def test_no_excluded_course_was_seeded(catalogue, code):
    for excluded_code, title, reason in EXCLUDED[code]:
        assert not subjects_for(catalogue, code).filter(course_code=excluded_code).exists(), (
            f"{code}: excluded {reason} course {excluded_code} ({title}) was seeded"
        )


@pytest.mark.parametrize(
    "code,semester,absent_code",
    [
        ("BME", 1, "MC23112"),   # Environmental Science — non-credit
        ("BME", 2, "MC23111"),   # Indian Constitution — non-credit
        ("BME", 4, "GE23421"),   # Soft Skills-I
        ("BME", 5, "GE23521"),   # Soft Skills-II
        ("BME", 6, "BM23621"),   # Medical Industrial Training
        ("BME", 7, "BM23722"),   # Project Phase-I
        ("BME", 7, "BM23723"),   # Hospital Training
        ("BME", 8, "BM23821"),   # Project Phase-II
        ("CIVIL", 1, "MC23112"),
        ("CIVIL", 2, "MC23111"),
        ("CIVIL", 4, "GE23421"),
        ("CIVIL", 5, "GE23521"),
        ("CIVIL", 6, "GE23621"),
        ("CIVIL", 7, "CE23724"),  # Internship
        ("CIVIL", 8, "CE23821"),  # Project Work
    ],
)
def test_specific_excluded_courses_are_absent(catalogue, code, semester, absent_code):
    assert not subjects_for(catalogue, code, semester).filter(course_code=absent_code).exists()


def test_bme_ai_ml_course_is_excluded_but_civil_one_is_included(catalogue):
    """The two look alike; only the Civil one sits under Laboratory Courses."""
    assert not subjects_for(catalogue, "BME").filter(course_code="BM23721").exists()

    civil = subjects_for(catalogue, "CIVIL").get(course_code="CE23723")
    assert civil.course_title == (
        "Artificial Intelligence and Machine Learning for Civil Engineers"
    )
    # Included despite a BS category, because the syllabus groups it as a lab.
    assert civil.category == "BS"
    assert civil.course_type == CourseType.LABORATORY
    assert civil.semester.semester_number == 7


# --------------------------------------------------------------------------- #
# Spot checks from the brief
# --------------------------------------------------------------------------- #
def test_civil_semester_three_contents(catalogue):
    titles = set(subjects_for(catalogue, "CIVIL", 3).values_list("course_title", flat=True))
    assert titles == {
        "Strength of Materials I",
        "Fluid Mechanics",
        "Construction Techniques, Equipment and Practice",
        "Surveying",
        "Transforms and Statistics",
        "Construction Materials Laboratory",
        "Python Programming for Machine Learning",
    }


def test_civil_semester_seven_contents(catalogue):
    titles = set(subjects_for(catalogue, "CIVIL", 7).values_list("course_title", flat=True))
    assert titles == {
        "Estimation, Costing and Valuation Engineering",
        "Hydrology",
        "Professional Elective III",
        "Professional Elective IV",
        "Building Information Modelling",
        "Artificial Intelligence and Machine Learning for Civil Engineers",
    }


def test_bme_semester_three_contents(catalogue):
    titles = set(subjects_for(catalogue, "BME", 3).values_list("course_title", flat=True))
    assert titles == {
        "Fourier Series and Number Theory",
        "Human Anatomy and Physiology",
        "Biomedical Instrumentation",
        "Biological Science",
        "Electronic Devices and Circuits",
        "Sensors and Measurements",
        "Biochemistry and Physiology Laboratory",
        "Biomedical Instrumentation Laboratory",
    }


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #
def test_the_same_semester_differs_across_every_department(catalogue):
    """Semester III of each department must be a distinct subject list.

    Compared on (course code, title) pairs rather than titles alone: Mechatronics
    and Robotics and Automation publish an identical third semester apart from a
    single course code, so a title-only comparison reports a false clash.
    """
    per_department = {
        code: set(subjects_for(catalogue, code, 3).values_list("course_code", "course_title"))
        for code in CURRICULA
    }
    for code, rows in per_department.items():
        assert rows, f"{code} Semester III is empty"

    for a in per_department:
        for b in per_department:
            if a < b:
                assert per_department[a] != per_department[b], f"{a} and {b} share Semester III"


@pytest.mark.parametrize(
    "title,owner",
    [
        ("Human Anatomy and Physiology", "BME"),
        ("Strength of Materials I", "CIVIL"),
        ("Power System Analysis", "EEE"),
        ("Social and Ethical Issues in AI", "AI&ML"),
        ("Framework for Data and Visual Analytics", "AI&DS"),
    ],
)
def test_signature_subjects_belong_to_exactly_one_department(catalogue, title, owner):
    """Each of these titles appears in exactly one department's syllabus.

    Note the AI&DS signature is a final-year course, not a first-year one:
    first-year courses such as PH23132 are legitimately shared across
    departments, so they can never serve as an ownership signature. The general
    isolation rule is asserted in `test_no_department_holds_a_foreign_subject`.
    """
    holders = set(
        Subject.objects.filter(course_title=title).values_list(
            "semester__department__code", flat=True
        )
    )
    assert holders == {owner}


def test_no_department_holds_a_foreign_subject(catalogue):
    """Every stored subject appears in its own department's syllabus.

    Derived from the curricula rather than from hand-picked titles, so shared
    first-year courses are correctly allowed and genuine leakage is still caught.
    """
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


def test_api_isolates_the_new_departments(student_api, catalogue):
    bme, civil = catalogue["BME"], catalogue["CIVIL"]

    bme_rows = student_api.get(
        "/api/subjects/", {"department": bme.id, "page_size": 200}
    ).data
    assert bme_rows["count"] == 50
    assert all(row["department"] == bme.id for row in bme_rows["results"])

    # A Civil course code must not be reachable through the BME department.
    assert (
        student_api.get(
            "/api/subjects/", {"department": bme.id, "search": "CE23311"}
        ).data["count"]
        == 0
    )
    assert (
        student_api.get(
            "/api/subjects/", {"department": civil.id, "search": "BM23312"}
        ).data["count"]
        == 0
    )


def test_stats_are_per_department(student_api, catalogue):
    for code, expected in SUBJECT_COUNTS.items():
        stats = student_api.get("/api/stats/", {"department": catalogue[code].id}).data
        assert stats["semesters"] == 8
        assert stats["subjects"] == expected


def test_existing_departments_are_untouched(catalogue):
    """AI&DS, AI&ML and EEE keep their exact subject counts."""
    assert subjects_for(catalogue, "AI&DS").count() == 39
    assert subjects_for(catalogue, "AI&ML").count() == 45
    assert subjects_for(catalogue, "EEE").count() == 51

    data_structures = subjects_for(catalogue, "AI&DS").get(course_code="CS23231")
    assert (data_structures.l, data_structures.t, data_structures.p, data_structures.credits) == (
        3, 0, 4, 5,
    )


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
    """A BME upload must not surface under Civil, and vice versa."""
    from conftest import pdf_upload

    bme_subject = subjects_for(catalogue, "BME").get(course_code="BM23312")
    civil_subject = subjects_for(catalogue, "CIVIL").get(course_code="CE23311")

    for subject, title in [
        (bme_subject, "BME Unit 1 Notes"),
        (civil_subject, "Civil Unit 1 Notes"),
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

    bme_id, civil_id = catalogue["BME"].id, catalogue["CIVIL"].id

    bme_resources = student_api.get("/api/resources/", {"department": bme_id}).data
    assert bme_resources["count"] == 1
    assert bme_resources["results"][0]["title"] == "BME Unit 1 Notes"

    civil_resources = student_api.get("/api/resources/", {"department": civil_id}).data
    assert civil_resources["count"] == 1
    assert civil_resources["results"][0]["title"] == "Civil Unit 1 Notes"

    # And nothing at all for a department that has no curriculum.
    assert (
        student_api.get(
            "/api/resources/", {"department": catalogue["ME"].id}
        ).data["count"]
        == 0
    )
