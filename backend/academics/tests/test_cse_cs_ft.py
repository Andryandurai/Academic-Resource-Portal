"""CSE (Cyber Security) and Food Technology curricula.

Asserts both syllabi were seeded exactly, that every non-credit / EEC /
internship / project course stayed out, that Food Technology's deliberately
empty final semester exists as an empty semester rather than as a missing one,
and that the twelve previously populated departments were not disturbed.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, EXCLUDED, SUBJECT_COUNTS
from academics.models import CourseType, Department, Subject

pytestmark = pytest.mark.django_db

# The Cyber Security department has carried the code CSE-CS since the
# departments were first seeded. The syllabus header prints CYS; the stored code
# is the established one, so the existing record is reused, not duplicated.
NEW = ["CSE-CS", "FT"]
EXISTING = {
    "AI&DS": 39, "AI&ML": 45, "EEE": 51, "BME": 50,
    "CIVIL": 51, "CSE": 44, "ECE": 46, "CSD": 43,
    "ME": 50, "IT": 45, "MCT": 52, "RA": 49,
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
    return set(subjects_for(catalogue, code, semester_number).values_list("course_title", flat=True))


# --------------------------------------------------------------------------- #
# Departments and totals
# --------------------------------------------------------------------------- #
def test_both_departments_exist_and_were_reused(catalogue):
    assert catalogue["CSE-CS"].name == "Computer Science and Engineering (Cyber Security)"
    assert catalogue["FT"].name == "Food Technology"
    assert Department.objects.count() == 19


def test_no_duplicate_department_was_created_for_cyber_security(catalogue):
    """Only one record may answer to the Cyber Security name, whatever its code."""
    matching = Department.objects.filter(name__icontains="Cyber Security")
    assert matching.count() == 1
    assert matching.first().code == "CSE-CS"
    # A separate CYS record would mean the seed forked the department in two.
    assert not Department.objects.filter(code="CYS").exists()


@pytest.mark.parametrize("code", NEW)
def test_eight_semesters_each(catalogue, code):
    assert catalogue[code].semesters.count() == 8
    assert sorted(
        catalogue[code].semesters.values_list("semester_number", flat=True)
    ) == [1, 2, 3, 4, 5, 6, 7, 8]


@pytest.mark.parametrize("code,expected", [("CSE-CS", 43), ("FT", 52)])
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
# Per-semester contents, exactly as the brief lists them
# --------------------------------------------------------------------------- #
CSE_CS_SEMESTERS = {
    1: {
        "Technical Communication I",
        "Linear Algebra and Calculus",
        "Heritage of Tamils",
        "Programming using C",
        "Basic Electrical and Electronics Engineering",
        "Physics for Information Science",
        "Engineering Practices-Civil and Mechanical",
    },
    2: {
        "Discrete Mathematical Structures",
        "Tamils and Technology",
        "Digital Logic and Microprocessor",
        "Engineering Graphics",
        "Data Structures",
        "Technical Communication II / English for Professional Competence",
        "Engineering Practices-Electrical and Electronics",
        "Python Programming Lab",
    },
    3: {
        "Fourier Series and Number Theory",
        "Database Management Systems",
        "Object Oriented Programming Using Java",
        "Computer Networks",
        "Cryptography",
    },
    4: {
        "Open Elective-I",
        "Probability, Statistics and Simulation",
        "Operating Systems",
        "Network Security",
        "Design and Analysis of Algorithms",
    },
    5: {
        "Professional Elective-I",
        "Web Programming",
        "Foundations of Artificial Intelligence",
        "Ethical Hacking",
        "Cyber and Digital Forensics",
        "Software Construction",
    },
    6: {
        "Cyber Laws and Security Policies",
        "Professional Elective-II",
        "Malware Analysis",
        "Blockchain Technologies",
        "Fundamentals of Machine Learning",
        "Mobile Application Development Laboratory",
    },
    7: {
        "Professional Elective-III",
        "Professional Elective-IV",
        "Professional Elective-V",
        "Open Elective-II",
        "Blockchain Development in Hyperledger Fabric",
    },
    8: {"Professional Elective-VI"},
}

FT_SEMESTERS = {
    1: {
        "Technical Communication I",
        "Algebra and Calculus",
        "Chemistry for Technologists",
        "Engineering Graphics",
        "Engineering Practices - Civil and Mechanical",
        "Heritage of Tamils",
    },
    2: {
        "Technical Communication II / English for Professional Competence",
        "Differential Equation and Complex Variables",
        "Basic Electrical and Electronics Engineering",
        "Physics for Bioscience",
        "Problem Solving and Python Programming",
        "Food Chemistry",
        "Tamils and Technology",
        "Food Chemistry Laboratory",
    },
    3: {
        "Transforms and Applied Partial Differential Equations",
        "Food Microbiology",
        "Biochemistry and Nutrition",
        "Thermodynamics for Food Technologists",
        "Food Process Calculations",
        "Food Additives",
        "Food Microbiology Laboratory",
        "Biochemistry and Nutrition Laboratory",
    },
    4: {
        "Probability, Statistics and Reliability",
        "Unit Operations in Food Industries",
        "Food Processing and Preservation Technology",
        "Fluid Mechanics in Food Processes",
        "Refrigeration and Cold Chain Management",
        "Open Elective-I",
        "Unit Operations in Food Industries Laboratory",
        "Food Processing and Preservation Laboratory-I",
    },
    5: {
        "Food Analysis",
        "Food Process Engineering",
        "Heat and Mass Transfer in Food Processing",
        "Professional Elective I",
        "Professional Elective II",
        "Fundamentals of Management for Engineers",
        "Food Analysis Laboratory",
        "Food Processing and Preservation Laboratory-II",
    },
    6: {
        "Food Product Technology",
        "Food Packaging Technology",
        "Start-up Ecosystems for Food Technologists",
        "Professional Elective III",
        "Professional Elective IV",
        "Food Packaging Technology Laboratory",
        "Food Product Technology Laboratory",
        "Microfluidics Laboratory for Food Technology",
    },
    7: {
        "Food Quality, Safety Standards and Certification",
        "Comprehension and Communication for Food Technologists",
        "Functional Foods and Nutraceuticals",
        "Open Elective-II",
        "Professional Elective V",
        "Professional Elective VI",
    },
    8: set(),
}


@pytest.mark.parametrize("number,expected", sorted(CSE_CS_SEMESTERS.items()))
def test_cyber_security_semester_contents(catalogue, number, expected):
    assert titles(catalogue, "CSE-CS", number) == expected


@pytest.mark.parametrize("number,expected", sorted(FT_SEMESTERS.items()))
def test_food_technology_semester_contents(catalogue, number, expected):
    assert titles(catalogue, "FT", number) == expected


def test_food_technology_semester_eight_exists_but_is_empty(catalogue):
    """The final term holds only FT23811 Project Work, which is an EEC course.

    The semester is still created: an eight-semester programme with an empty
    final term is the truth, and dropping the record would misreport it as a
    seven-semester one.
    """
    semester = catalogue["FT"].semesters.get(semester_number=8)
    assert semester.name == "Semester VIII"
    assert semester.subjects.count() == 0
    assert not subjects_for(catalogue, "FT").filter(course_title="Project Work").exists()


def test_cyber_security_course_codes_are_exact(catalogue):
    """Spot-check the codes the brief names, including the CR-series."""
    stored = dict(
        subjects_for(catalogue, "CSE-CS")
        .exclude(course_code__isnull=True)
        .values_list("course_title", "course_code")
    )
    for title, code in [
        ("Cryptography", "CR23331"),
        ("Network Security", "CR23431"),
        ("Ethical Hacking", "CR23531"),
        ("Cyber and Digital Forensics", "CR23532"),
        ("Cyber Laws and Security Policies", "CR23611"),
        ("Malware Analysis", "CR23631"),
        ("Blockchain Technologies", "CR23632"),
        ("Blockchain Development in Hyperledger Fabric", "CR23731"),
    ]:
        assert stored[title] == code


def test_food_technology_course_codes_are_exact(catalogue):
    stored = dict(
        subjects_for(catalogue, "FT")
        .exclude(course_code__isnull=True)
        .values_list("course_title", "course_code")
    )
    for title, code in [
        ("Food Chemistry", "FT23201"),
        ("Food Microbiology", "FT23301"),
        ("Food Additives", "FT23305"),
        ("Unit Operations in Food Industries", "FT23401"),
        ("Food Analysis", "FT23501"),
        ("Food Packaging Technology", "FT23602"),
        ("Microfluidics Laboratory for Food Technology", "FT23613"),
        ("Functional Foods and Nutraceuticals", "FT23703"),
    ]:
        assert stored[title] == code


@pytest.mark.parametrize(
    "code,title,ltpc",
    [
        ("CSE-CS", "Ethical Hacking", (3, 0, 2, 4)),
        ("CSE-CS", "Data Structures", (3, 0, 4, 5)),
        ("CSE-CS", "Object Oriented Programming Using Java", (1, 0, 6, 4)),
        ("CSE-CS", "Blockchain Development in Hyperledger Fabric", (2, 0, 2, 3)),
        ("FT", "Food Microbiology", (3, 0, 0, 3)),
        ("FT", "Chemistry for Technologists", (3, 0, 2, 4)),
        ("FT", "Microfluidics Laboratory for Food Technology", (0, 0, 2, 1)),
        ("FT", "Probability, Statistics and Reliability", (3, 0, 2, 4)),
    ],
)
def test_ltpc_is_taken_from_the_syllabus_not_computed(catalogue, code, title, ltpc):
    subject = subjects_for(catalogue, code).get(course_title=title)
    assert (subject.l, subject.t, subject.p, subject.credits) == ltpc


def test_electives_carry_no_invented_code(catalogue):
    for code, expected in [("CSE-CS", 8), ("FT", 8)]:
        blank = subjects_for(catalogue, code).filter(course_code__isnull=True)
        assert blank.count() == expected
        assert all(
            row.startswith(("Professional Elective", "Open Elective"))
            for row in blank.values_list("course_title", flat=True)
        )


def test_cyber_security_reuses_shared_first_year_codes(catalogue):
    """HS23111 and GE23131 also run in other departments; separate records."""
    for shared in ["HS23111", "GE23117", "GE23131", "EE23133", "PH23132"]:
        holders = Subject.objects.filter(course_code=shared).values_list(
            "semester__department__code", flat=True
        )
        assert "CSE-CS" in set(holders)
        assert len(set(holders)) > 1, f"{shared} was expected to be shared"


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
        ("CSE-CS", "Indian Constitution and Freedom Movement"),
        ("CSE-CS", "Environmental Science and Engineering"),
        ("CSE-CS", "Soft Skills-I"),
        ("CSE-CS", "Internship"),
        ("CSE-CS", "Soft Skills-II"),
        ("CSE-CS", "Design Thinking and Innovation"),
        ("CSE-CS", "Problem Solving Techniques"),
        ("CSE-CS", "Project Phase I"),
        ("CSE-CS", "Project Phase II"),
        ("FT", "Environmental Science and Engineering"),
        ("FT", "Indian Constitution and Freedom Movement"),
        ("FT", "Soft Skills-I"),
        ("FT", "Soft Skills-II"),
        ("FT", "Design Thinking and Innovation"),
        ("FT", "Problem Solving Techniques"),
        ("FT", "Problem Solving using AI-ML for Food Technologists"),
        ("FT", "Internship"),
        ("FT", "Project Work"),
    ],
)
def test_named_excluded_titles_are_absent(catalogue, code, title):
    assert not subjects_for(catalogue, code).filter(course_title=title).exists()


def test_no_zero_credit_course_reached_either_department(catalogue):
    """Non-credit courses are the thing the exclusion rule exists to keep out."""
    for code in NEW:
        assert not subjects_for(catalogue, code).filter(credits=0).exists()


# --------------------------------------------------------------------------- #
# Cross-department tests from the brief
# --------------------------------------------------------------------------- #
CYBER_SIGNATURE = [
    ("Ethical Hacking", 5),
    ("Network Security", 4),
    ("Cyber and Digital Forensics", 5),
    ("Malware Analysis", 6),
    ("Blockchain Technologies", 6),
]

FOOD_SIGNATURE = [
    ("Food Microbiology", 3),
    ("Food Chemistry", 2),
    ("Food Analysis", 5),
    ("Food Process Engineering", 5),
    ("Food Packaging Technology", 6),
    ("Food Product Technology", 6),
]


@pytest.mark.parametrize("title,number", CYBER_SIGNATURE)
def test_cyber_signature_subjects_sit_in_the_right_semester(catalogue, title, number):
    subject = subjects_for(catalogue, "CSE-CS").get(course_title=title)
    assert subject.semester.semester_number == number


@pytest.mark.parametrize("title,number", FOOD_SIGNATURE)
def test_food_signature_subjects_sit_in_the_right_semester(catalogue, title, number):
    subject = subjects_for(catalogue, "FT").get(course_title=title)
    assert subject.semester.semester_number == number


@pytest.mark.parametrize("title,_number", CYBER_SIGNATURE)
def test_cyber_subjects_appear_in_no_other_department(catalogue, title, _number):
    holders = set(
        Subject.objects.filter(course_title=title).values_list(
            "semester__department__code", flat=True
        )
    )
    assert holders == {"CSE-CS"}, f"{title} also appears under {sorted(holders - {'CSE-CS'})}"


@pytest.mark.parametrize("title,_number", FOOD_SIGNATURE)
def test_food_subjects_appear_in_no_other_department(catalogue, title, _number):
    holders = set(
        Subject.objects.filter(course_title=title).values_list(
            "semester__department__code", flat=True
        )
    )
    assert holders == {"FT"}, f"{title} also appears under {sorted(holders - {'FT'})}"


def test_the_two_departments_share_no_subject_title(catalogue):
    assert titles(catalogue, "CSE-CS") & titles(catalogue, "FT") == {
        # The only overlaps are the first-year courses both programmes run and
        # the unnumbered electives — asserted explicitly so a real leak, such as
        # Ethical Hacking turning up in Food Technology, cannot hide in here.
        "Technical Communication I",
        "Technical Communication II / English for Professional Competence",
        "Basic Electrical and Electronics Engineering",
        "Engineering Graphics",
        "Heritage of Tamils",
        "Tamils and Technology",
        "Open Elective-I",
        "Open Elective-II",
    }


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #
def test_semester_three_differs_across_every_populated_department(catalogue):
    # On (course code, title) pairs: Mechatronics and Robotics and Automation
    # publish an identical Semester III apart from one course code.
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
        ("CSE-CS", "FT23301"),   # Food Microbiology
        ("CSE-CS", "FT23602"),   # Food Packaging Technology
        ("FT", "CR23531"),       # Ethical Hacking
        ("FT", "CR23631"),       # Malware Analysis
        ("FT", "CS23231"),       # Data Structures — CSE-CS Semester II
    ],
)
def test_no_foreign_course_is_reachable(catalogue, code, foreign_code):
    assert not subjects_for(catalogue, code).filter(course_code=foreign_code).exists()


def test_api_isolates_the_new_departments(student_api, catalogue):
    for code, expected in [("CSE-CS", 43), ("FT", 52)]:
        department = catalogue[code]
        rows = student_api.get(
            "/api/subjects/", {"department": department.id, "page_size": 200}
        ).data
        assert rows["count"] == expected
        assert all(row["department"] == department.id for row in rows["results"])

    # The brief's Test E, at the API level.
    assert (
        student_api.get(
            "/api/subjects/",
            {"department": catalogue["FT"].id, "search": "Ethical Hacking"},
        ).data["count"]
        == 0
    )
    assert (
        student_api.get(
            "/api/subjects/",
            {"department": catalogue["CSE-CS"].id, "search": "Food Microbiology"},
        ).data["count"]
        == 0
    )


def test_semesters_endpoint_is_department_scoped(student_api, catalogue):
    for code in NEW:
        rows = student_api.get("/api/semesters/", {"department": catalogue[code].id}).data
        results = rows["results"] if isinstance(rows, dict) else rows
        assert len(results) == 8
        assert all(row["department"] == catalogue[code].id for row in results)


def test_stats_are_per_department(student_api, catalogue):
    for code, expected in SUBJECT_COUNTS.items():
        stats = student_api.get("/api/stats/", {"department": catalogue[code].id}).data
        assert stats["semesters"] == 8
        assert stats["subjects"] == expected


# --------------------------------------------------------------------------- #
# Resources
# --------------------------------------------------------------------------- #
def test_every_subject_offers_all_eight_resource_categories(student_api, catalogue):
    """The eight containers are derived, not rows — every subject reports all."""
    from academics.models import Subject as SubjectModel

    for code in NEW:
        subject = SubjectModel.objects.filter(semester__department=catalogue[code]).first()
        counts = student_api.get(f"/api/subjects/{subject.id}/resource-counts/").data
        assert sorted(counts) == [
            "CAT_1", "CAT_2", "SEMESTER_EXAM",
            "UNIT_1", "UNIT_2", "UNIT_3", "UNIT_4", "UNIT_5",
        ]
        assert set(counts.values()) == {0}


def test_resources_stay_within_their_department(admin_api, student_api, catalogue):
    """The brief's three isolation uploads, and no leakage between them."""
    from conftest import pdf_upload

    hacking = subjects_for(catalogue, "CSE-CS").get(course_code="CR23531")
    microbiology = subjects_for(catalogue, "FT").get(course_code="FT23301")
    packaging = subjects_for(catalogue, "FT").get(course_code="FT23602")

    uploads = [
        (hacking, "UNIT_1", "ethical-hacking-unit1.pdf"),
        (microbiology, "UNIT_1", "food-microbiology-unit1.pdf"),
        (packaging, "CAT_2", "food-packaging-cat2.pdf"),
    ]
    for subject, resource_type, name in uploads:
        response = admin_api.post(
            "/api/resources/",
            {
                "subject": subject.id,
                "resource_type": resource_type,
                "title": name,
                "file": pdf_upload(name=name),
            },
            format="multipart",
        )
        assert response.status_code == 201, response.data

    cyber = student_api.get("/api/resources/", {"department": catalogue["CSE-CS"].id}).data
    assert [r["title"] for r in cyber["results"]] == ["ethical-hacking-unit1.pdf"]

    food = student_api.get("/api/resources/", {"department": catalogue["FT"].id}).data
    assert sorted(r["title"] for r in food["results"]) == [
        "food-microbiology-unit1.pdf",
        "food-packaging-cat2.pdf",
    ]

    # Each file resolves to exactly one subject and one resource category.
    unit1 = student_api.get(
        "/api/resources/", {"subject": microbiology.id, "resource_type": "UNIT_1"}
    ).data
    assert unit1["count"] == 1
    assert unit1["results"][0]["title"] == "food-microbiology-unit1.pdf"

    assert (
        student_api.get(
            "/api/resources/", {"subject": microbiology.id, "resource_type": "CAT_2"}
        ).data["count"]
        == 0
    )
    assert (
        student_api.get("/api/resources/", {"subject": hacking.id}).data["count"] == 1
    )

    # No department other than the two under test sees any of the three files.
    for code in EXISTING:
        rows = student_api.get("/api/resources/", {"department": catalogue[code].id}).data
        assert rows["count"] == 0, f"{code} can see a Cyber Security or Food Technology upload"


def test_admin_can_upload_a_docx_to_the_new_departments(admin_api, catalogue):
    """Test B from the brief: Malware Analysis, CAT 2, DOCX."""
    import io
    import zipfile

    from conftest import upload

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")

    subject = subjects_for(catalogue, "CSE-CS").get(course_code="CR23631")
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": subject.id,
            "resource_type": "CAT_2",
            "title": "Malware Analysis CAT 2",
            "file": upload(
                "malware-cat2.docx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        },
        format="multipart",
    )
    assert response.status_code == 201, response.data
    assert response.data["file_ext"] == "docx"
    assert response.data["subject"] == subject.id


def test_student_cannot_write_to_either_new_department(student_api, catalogue):
    from conftest import pdf_upload

    for code, course_code in [("CSE-CS", "CR23531"), ("FT", "FT23301")]:
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


def test_both_new_departments_appear_in_the_selector(student_api, catalogue):
    rows = student_api.get("/api/departments/").data
    listed = {row["code"]: row for row in rows}
    for code in NEW:
        assert listed[code]["is_active"] is True
        assert listed[code]["has_curriculum"] is True
        assert listed[code]["semester_count"] == 8
        assert listed[code]["subject_count"] == SUBJECT_COUNTS[code]


def test_seed_is_idempotent_across_all_departments(catalogue):
    from django.core.management import call_command

    call_command("seed_departments", verbosity=0)
    call_command("seed_academics", verbosity=0)
    call_command("seed_academics", verbosity=0)

    assert Department.objects.count() == 19
    assert Subject.objects.count() == sum(SUBJECT_COUNTS.values())
    from academics.models import Semester

    assert Semester.objects.count() == 8 * len(CURRICULA)
    for code in NEW:
        assert subjects_for(catalogue, code).count() == SUBJECT_COUNTS[code]


def test_verify_curriculum_passes_for_all(catalogue):
    from django.core.management import call_command

    call_command("verify_curriculum", verbosity=0)
