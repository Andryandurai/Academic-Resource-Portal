"""Mechatronics and Robotics and Automation curricula.

These two syllabi overlap heavily — same first year, same RO-prefixed third-year
courses — which makes them the sharpest test of department isolation the
catalogue has. Every shared course must be a separate record per department.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseType, Department, Subject

pytestmark = pytest.mark.django_db

NEW = ["MCT", "RA"]


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


def titles(catalogue, code, semester_number):
    return set(
        subjects_for(catalogue, code, semester_number).values_list(
            "course_title", flat=True
        )
    )


# --------------------------------------------------------------------------- #
# Departments and totals
# --------------------------------------------------------------------------- #
def test_both_departments_exist_and_were_reused(catalogue):
    assert catalogue["MCT"].name == "Mechatronics"
    assert catalogue["RA"].name == "Robotics and Automation"
    assert Department.objects.count() == 19


@pytest.mark.parametrize("code", NEW)
def test_eight_semesters_each(catalogue, code):
    assert catalogue[code].semesters.count() == 8


@pytest.mark.parametrize("code,expected", [("MCT", 52), ("RA", 49)])
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


def test_the_new_category_codes_are_stored_verbatim(catalogue):
    """HSMC, HSM and MC are preserved rather than normalised to HS."""
    assert subjects_for(catalogue, "MCT").get(course_code="HS23111").category == "HSMC"
    assert subjects_for(catalogue, "MCT").get(course_code="GE23311").category == "HSM"
    # MC is a *category* here; the course is included because the syllabus
    # lists it under Theory Courses, not excluded because of the code.
    heritage = subjects_for(catalogue, "MCT").get(course_code="GE23117")
    assert heritage.category == "MC"
    assert heritage.course_type == CourseType.THEORY
    assert subjects_for(catalogue, "RA").get(course_code="RO23713").category == "HSMC"


# --------------------------------------------------------------------------- #
# Exclusions
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("code", NEW)
def test_no_excluded_course_was_seeded(catalogue, code):
    for excluded_code, title, reason in EXCLUDED[code]:
        assert not subjects_for(catalogue, code).filter(course_code=excluded_code).exists(), (
            f"{code}: excluded {reason} course {excluded_code} ({title}) was seeded"
        )


@pytest.mark.parametrize("code", NEW)
@pytest.mark.parametrize(
    "title",
    [
        "Environmental Science and Engineering",
        "Indian Constitution and Freedom Movement",
        "Heritage of Tamils and Technology",
        "Soft Skills-I",
        "Soft Skills-II",
        "Internship",
        "Problem Solving Techniques",
        "Design Thinking and Innovation",
    ],
)
def test_named_exclusions_are_absent(catalogue, code, title):
    assert not subjects_for(catalogue, code).filter(course_title=title).exists()


def test_project_courses_are_absent(catalogue):
    for code in ("MT23724", "MT23821", "RO23722", "RO23821"):
        assert not Subject.objects.filter(course_code=code).exists()


# --------------------------------------------------------------------------- #
# Semester contents from the brief
# --------------------------------------------------------------------------- #
def test_mct_semester_one(catalogue):
    assert titles(catalogue, "MCT", 1) == {
        "Technical Communication I",
        "Algebra and Calculus",
        "Engineering Graphics",
        "Introduction to Mechanical Systems",
        "Heritage of Tamils",
        "Basic Electrical Engineering",
        "Engineering Practices – Civil and Mechanical",
        "Engineering Practices – Electrical and Electronics",
        "Computer Aided Drawing Laboratory",
    }


def test_mct_semester_seven(catalogue):
    assert titles(catalogue, "MCT", 7) == {
        "Professional Elective-III",
        "Professional Elective-IV",
        "Industrial Automation",
        "Machine Vision",
        "Computer Aided Engineering Laboratory",
        "Industrial Automation Laboratory",
        "Mechatronics Engineering Problem Solving Using AI, ML and DL",
    }


def test_ra_semester_one_has_no_cad_laboratory(catalogue):
    """RA's first semester is MCT's minus the CAD laboratory."""
    ra = titles(catalogue, "RA", 1)
    mct = titles(catalogue, "MCT", 1)
    assert mct - ra == {"Computer Aided Drawing Laboratory"}
    assert ra - mct == set()


def test_ra_semester_four(catalogue):
    assert titles(catalogue, "RA", 4) == {
        "Fluid Power Systems",
        "Industrial Automation and Control",
        "Microcontrollers and Real Time Embedded Systems",
        "Robot Kinematics",
        "Statistics and Numerical Methods",
        "Mechanisms and Robotics Laboratory",
        "Industrial Automation Laboratory-I",
    }


def test_ra_semester_seven(catalogue):
    assert titles(catalogue, "RA", 7) == {
        "Aerial Robotics",
        "Humanoid Robotics",
        "Resource Management Techniques",
        "Professional Elective-IV",
        "Open Elective-II",
        "Robotics and Automation Problem Solving Using AI, ML and DL",
    }


# --------------------------------------------------------------------------- #
# Isolation — the hard case
# --------------------------------------------------------------------------- #
def test_mct_and_ra_semester_three_are_separate_records(catalogue):
    """The two syllabi list near-identical third semesters.

    Six of the seven titles are shared, so this is the case where a
    department-blind implementation would collapse the two into one. Every
    shared course must still be its own row under its own department.
    """
    mct = subjects_for(catalogue, "MCT", 3)
    ra = subjects_for(catalogue, "RA", 3)

    assert mct.count() == ra.count() == 7
    # Every title is shared — the two syllabi list an identical third semester,
    # differing only in one course code. Nothing but the department foreign key
    # separates these rows, which is exactly the case worth pinning.
    assert titles(catalogue, "MCT", 3) == titles(catalogue, "RA", 3)

    # Same titles, entirely disjoint primary keys.
    assert set(mct.values_list("id", flat=True)).isdisjoint(ra.values_list("id", flat=True))
    assert all(s.semester.department.code == "MCT" for s in mct)
    assert all(s.semester.department.code == "RA" for s in ra)

    # The one course the two syllabi code differently.
    assert mct.get(course_title="Theory of Mechanisms and Machines-I").course_code == "MT23312"
    assert ra.get(course_title="Theory of Mechanisms and Machines-I").course_code == "RO23312"


def test_shared_course_codes_are_separate_rows(catalogue):
    """RO23311 and CS23422 exist in both departments as distinct records."""
    for code in ("RO23311", "RO23313", "RO23331", "RO23332", "CS23422"):
        holders = set(
            Subject.objects.filter(course_code=code).values_list(
                "semester__department__code", flat=True
            )
        )
        assert {"MCT", "RA"} <= holders, f"{code} missing from one of the two"


def test_cs23422_appears_twice_within_mechatronics(catalogue):
    """MCT lists the course in Semester III and again in Semester V."""
    semesters = sorted(
        subjects_for(catalogue, "MCT")
        .filter(course_code="CS23422")
        .values_list("semester__semester_number", flat=True)
    )
    assert semesters == [3, 5]


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
        ("MCT", "RO23414"),   # RA's Robot Kinematics
        ("MCT", "RO23632"),   # RA's Robot Vision
        ("RA", "MT23431"),    # MCT's Microcontrollers and Embedded Systems
        ("RA", "MT23712"),    # MCT's Machine Vision
    ],
)
def test_no_foreign_course_is_reachable(catalogue, code, foreign_code):
    assert not subjects_for(catalogue, code).filter(course_code=foreign_code).exists()


def test_api_isolates_the_new_departments(student_api, catalogue):
    for code, expected in [("MCT", 52), ("RA", 49)]:
        department = catalogue[code]
        rows = student_api.get(
            "/api/subjects/", {"department": department.id, "page_size": 200}
        ).data
        assert rows["count"] == expected
        assert all(row["department"] == department.id for row in rows["results"])

    assert (
        student_api.get(
            "/api/subjects/", {"department": catalogue["MCT"].id, "search": "RO23414"}
        ).data["count"]
        == 0
    )
    # The shared code resolves to one row per department, never both.
    assert (
        student_api.get(
            "/api/subjects/", {"department": catalogue["RA"].id, "search": "RO23311"}
        ).data["count"]
        == 1
    )


def test_stats_are_per_department(student_api, catalogue):
    for code, expected in SUBJECT_COUNTS.items():
        stats = student_api.get("/api/stats/", {"department": catalogue[code].id}).data
        assert stats["semesters"] == 8
        assert stats["subjects"] == expected


# --------------------------------------------------------------------------- #
# Regression and resources
# --------------------------------------------------------------------------- #
def test_all_previously_populated_departments_are_untouched(catalogue):
    for code, expected in {
        "AI&DS": 39, "AI&ML": 45, "EEE": 51, "BME": 50, "CIVIL": 51,
        "CSE": 44, "ECE": 46, "CSD": 43, "ME": 50, "IT": 45,
    }.items():
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
    """The brief's isolation test, on the two near-identical departments."""
    from conftest import pdf_upload

    mct_subject = subjects_for(catalogue, "MCT").get(course_code="MT23431")
    ra_subject = subjects_for(catalogue, "RA").get(course_code="RO23413")

    for subject, title in [
        (mct_subject, "MCT Microcontrollers Unit 1"),
        (ra_subject, "RA Microcontrollers Unit 1"),
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

    mct_rows = student_api.get("/api/resources/", {"department": catalogue["MCT"].id}).data
    ra_rows = student_api.get("/api/resources/", {"department": catalogue["RA"].id}).data

    assert [r["title"] for r in mct_rows["results"]] == ["MCT Microcontrollers Unit 1"]
    assert [r["title"] for r in ra_rows["results"]] == ["RA Microcontrollers Unit 1"]


def test_student_still_cannot_write_to_the_new_departments(student_api, catalogue):
    from conftest import pdf_upload

    subject = subjects_for(catalogue, "RA").get(course_code="RO23414")
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
