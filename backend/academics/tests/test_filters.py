"""The catalogue filter system.

Covers the multi-value filters, the cross-field search, the facets endpoint and
— most importantly — that every single-value URL the portal used before still
returns exactly what it did.
"""

from __future__ import annotations

import pytest

from academics.curricula import CURRICULA, SUBJECT_COUNTS
from academics.models import CourseCategory, CourseType, Department, Subject

pytestmark = pytest.mark.django_db

SUBJECTS_URL = "/api/subjects/"
FACETS_URL = "/api/subjects/facets/"


@pytest.fixture
def catalogue(db):
    from django.core.management import call_command

    call_command("seed_departments", verbosity=0)
    call_command("seed_academics", verbosity=0)
    return {d.code: d for d in Department.objects.all()}


def ids(response):
    return {row["id"] for row in response.data["results"]}


def count(api, **query):
    response = api.get(SUBJECTS_URL, {"page_size": 500, **query})
    assert response.status_code == 200, response.data
    return response.data["count"]


# --------------------------------------------------------------------------- #
# Backward compatibility — the single-value URLs the portal already sends
# --------------------------------------------------------------------------- #
def test_single_value_department_still_scopes(student_api, catalogue):
    for code, expected in SUBJECT_COUNTS.items():
        assert count(student_api, department=catalogue[code].id) == expected


@pytest.mark.parametrize(
    "query",
    [
        {"semester_number": 3},
        {"course_type": "THEORY"},
        {"category": "PC"},
        {"search": "Data Structures"},
        {"department_code": "CSE"},
    ],
)
def test_legacy_single_value_filters_are_unchanged(student_api, catalogue, query):
    """Each of these was a working URL before the filter system was added."""
    response = student_api.get(SUBJECTS_URL, {"page_size": 500, **query})
    assert response.status_code == 200
    assert response.data["count"] > 0

    field = {
        "semester_number": lambda s: s["semester_number"],
        "course_type": lambda s: s["course_type"],
        "category": lambda s: s["category"],
    }
    for key, getter in field.items():
        if key in query:
            assert all(str(getter(s)) == str(query[key]) for s in response.data["results"])


def test_subject_by_semester_primary_key_still_works(student_api, catalogue):
    semester = catalogue["CSE"].semesters.get(semester_number=5)
    response = student_api.get(SUBJECTS_URL, {"semester": semester.id, "page_size": 500})
    assert response.data["count"] == semester.subjects.count()
    assert all(s["semester"] == semester.id for s in response.data["results"])


# --------------------------------------------------------------------------- #
# Combining filters — the example from the brief
# --------------------------------------------------------------------------- #
def test_the_briefs_worked_example(student_api, catalogue):
    """department=CSE & semester=V & category=PC & credits=4."""
    cse = catalogue["CSE"]
    response = student_api.get(
        SUBJECTS_URL,
        {"department": cse.id, "semester_number": 5, "category": "PC", "credits": 4, "page_size": 500},
    )
    assert response.status_code == 200
    assert response.data["count"] > 0
    for row in response.data["results"]:
        assert row["department"] == cse.id
        assert row["semester_number"] == 5
        assert row["category"] == "PC"
        assert row["credits"] == 4

    # And it really is a narrowing of each looser query.
    assert response.data["count"] <= count(student_api, department=cse.id, semester_number=5)
    assert response.data["count"] <= count(student_api, category="PC", credits=4)


def test_filters_are_conjunctive_not_disjunctive(student_api, catalogue):
    """Adding a filter can only ever shrink the result set."""
    cumulative: dict = {}
    previous = count(student_api)
    for extra in [
        {"department": catalogue["FT"].id},
        {"semester_number": 3},
        {"category": "PC"},
        {"course_type": "THEORY"},
    ]:
        cumulative.update(extra)
        current = count(student_api, **cumulative)
        assert current <= previous, f"{cumulative} widened the result set"
        previous = current
    assert previous > 0


def test_an_impossible_combination_returns_zero_not_everything(student_api, catalogue):
    """A filter that matches nothing must return nothing, never fall open."""
    assert count(student_api, department=catalogue["FT"].id, category="OE", credits=5) == 0


# --------------------------------------------------------------------------- #
# Multi-value filters
# --------------------------------------------------------------------------- #
def test_multi_value_category_is_the_union(student_api, catalogue):
    pc = count(student_api, category="PC")
    pe = count(student_api, category="PE")
    assert count(student_api, category="PC,PE") == pc + pe


def test_multi_value_credits_is_the_union(student_api, catalogue):
    assert count(student_api, credits="4,5") == count(student_api, credits=4) + count(
        student_api, credits=5
    )


def test_multi_value_department_is_the_union(student_api, catalogue):
    a, b = catalogue["CSE-CS"], catalogue["FT"]
    assert count(student_api, department=f"{a.id},{b.id}") == (
        SUBJECT_COUNTS["CSE-CS"] + SUBJECT_COUNTS["FT"]
    )


def test_multi_value_course_type_and_semester(student_api, catalogue):
    assert count(student_api, course_type="THEORY,LABORATORY") == count(
        student_api, course_type="THEORY"
    ) + count(student_api, course_type="LABORATORY")
    assert count(student_api, semester_number="1,2") == count(
        student_api, semester_number=1
    ) + count(student_api, semester_number=2)


def test_credit_range_filters(student_api, catalogue):
    assert count(student_api, credits_min=4) == count(student_api, credits="4,5")
    assert count(student_api, credits_max=2) == count(student_api, credits="1,2")
    assert count(student_api, credits_min=3, credits_max=3) == count(student_api, credits=3)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "query,field",
    [
        ({"category": "EEC"}, "category"),
        ({"category": "PC,NOPE"}, "category"),
        ({"course_type": "PROJECT"}, "course_type"),
        ({"credits": "abc"}, "credits"),
        ({"department": "not-a-number"}, "department"),
        ({"semester_number": "five"}, "semester_number"),
    ],
)
def test_invalid_filter_values_are_rejected(student_api, catalogue, query, field):
    """A bad filter is a 400 with a named field, not a silent empty page.

    Silently returning zero rows would look identical to "no courses match",
    which is the one answer a filter bug must never be able to imitate.
    """
    response = student_api.get(SUBJECTS_URL, query)
    assert response.status_code == 400, response.data
    assert field in response.data


def test_excluded_course_categories_are_not_filterable(student_api, catalogue):
    """EEC has no model choice because no EEC course is ever stored.

    The portal excludes non-credit, employability and project courses by design,
    so offering them as filter values would be a control that always answers
    zero. The API rejects them rather than pretending they are empty.
    """
    assert "EEC" not in dict(CourseCategory.choices)
    assert student_api.get(SUBJECTS_URL, {"category": "EEC"}).status_code == 400
    assert not Subject.objects.filter(credits=0).exists()


# --------------------------------------------------------------------------- #
# Department search
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "term,expected_codes",
    [
        ("cyber", {"CSE-CS"}),
        ("food", {"FT"}),
        ("robotics", {"RA"}),
        ("mechatronics", {"MCT"}),
        ("artificial", {"AI&DS", "AI&ML"}),
    ],
)
def test_department_search_matches_names_and_is_case_insensitive(
    student_api, catalogue, term, expected_codes
):
    for value in (term, term.upper(), term.capitalize()):
        response = student_api.get(SUBJECTS_URL, {"department_search": value, "page_size": 500})
        assert response.status_code == 200
        found = {row["department_code"] for row in response.data["results"]}
        assert found == expected_codes, f"{value!r} matched {found}"


def test_department_search_matches_the_code_too(student_api, catalogue):
    response = student_api.get(SUBJECTS_URL, {"department_search": "CSE-CS", "page_size": 500})
    assert {row["department_code"] for row in response.data["results"]} == {"CSE-CS"}


def test_department_search_combines_with_every_other_filter(student_api, catalogue):
    response = student_api.get(
        SUBJECTS_URL,
        {"department_search": "food", "category": "PC", "credits": 3, "page_size": 500},
    )
    assert response.status_code == 200
    assert response.data["count"] > 0
    for row in response.data["results"]:
        assert row["department_code"] == "FT"
        assert row["category"] == "PC"
        assert row["credits"] == 3


# --------------------------------------------------------------------------- #
# Global search
# --------------------------------------------------------------------------- #
def test_search_matches_a_course_code(student_api, catalogue):
    response = student_api.get(SUBJECTS_URL, {"search": "CR23531"})
    assert response.data["count"] == 1
    assert response.data["results"][0]["course_title"] == "Ethical Hacking"


def test_search_matches_a_course_title(student_api, catalogue):
    response = student_api.get(SUBJECTS_URL, {"search": "Food Microbiology", "page_size": 500})
    titles = {row["course_title"] for row in response.data["results"]}
    assert "Food Microbiology" in titles


def test_search_is_case_insensitive_and_partial(student_api, catalogue):
    baseline = count(student_api, search="Ethical Hacking")
    for variant in ["ethical hacking", "ETHICAL HACKING", "ethical", "hack", "HaCk"]:
        assert count(student_api, search=variant) >= baseline > 0


def test_search_matches_a_department(student_api, catalogue):
    response = student_api.get(SUBJECTS_URL, {"search": "Cyber Security", "page_size": 500})
    assert response.data["count"] == SUBJECT_COUNTS["CSE-CS"]
    assert {row["department_code"] for row in response.data["results"]} == {"CSE-CS"}


def test_search_matches_a_semester(student_api, catalogue):
    by_search = count(student_api, search="Semester VIII")
    by_filter = count(student_api, semester_number=8)
    assert by_search == by_filter > 0

    # A bare ordinal works too.
    assert count(student_api, search="8") >= by_filter


def test_search_matches_a_category_code_and_its_label(student_api, catalogue):
    assert count(student_api, search="PC") >= count(student_api, category="PC")
    assert count(student_api, search="Professional Core") >= count(student_api, category="PC")


def test_search_and_filters_narrow_each_other(student_api, catalogue):
    """Search must AND with the filters, never replace them."""
    loose = count(student_api, search="laboratory")
    scoped = count(student_api, search="laboratory", department=catalogue["FT"].id)
    assert 0 < scoped < loose

    response = student_api.get(
        SUBJECTS_URL,
        {"search": "laboratory", "department": catalogue["FT"].id, "page_size": 500},
    )
    assert all(row["department_code"] == "FT" for row in response.data["results"])


def test_search_does_not_leak_across_departments(student_api, catalogue):
    """The brief's isolation rule, expressed through the search box."""
    assert count(student_api, search="Ethical Hacking", department=catalogue["FT"].id) == 0
    assert count(student_api, search="Food Microbiology", department=catalogue["CSE-CS"].id) == 0


def test_a_blank_search_is_not_a_filter(student_api, catalogue):
    assert count(student_api, search="") == count(student_api)
    assert count(student_api, search="   ") == count(student_api)


def test_search_returns_no_duplicate_rows(student_api, catalogue):
    """A term matching several OR-clauses at once must still yield one row each."""
    response = student_api.get(SUBJECTS_URL, {"search": "Computer", "page_size": 500})
    returned = [row["id"] for row in response.data["results"]]
    assert len(returned) == len(set(returned))
    assert response.data["count"] == len(returned)


# --------------------------------------------------------------------------- #
# Facets
# --------------------------------------------------------------------------- #
def test_facets_require_authentication(api, catalogue):
    assert api.get(FACETS_URL).status_code == 401


def test_facets_describe_the_whole_catalogue(student_api, catalogue):
    data = student_api.get(FACETS_URL).data
    assert data["total"] == Subject.objects.count() == sum(SUBJECT_COUNTS.values())
    assert data["count"] == data["total"]
    assert {d["code"] for d in data["departments"]} == set(CURRICULA)
    assert [s["value"] for s in data["semesters"]] == [1, 2, 3, 4, 5, 6, 7, 8]


def test_facet_options_are_derived_from_the_data_not_hardcoded(student_api, catalogue):
    """Every offered option is a value some course actually has."""
    data = student_api.get(FACETS_URL).data

    assert {c["value"] for c in data["credits"]} == set(
        Subject.objects.values_list("credits", flat=True)
    )
    assert {c["value"] for c in data["categories"]} == set(
        Subject.objects.values_list("category", flat=True)
    )
    assert {c["value"] for c in data["course_types"]} == set(
        Subject.objects.values_list("course_type", flat=True)
    )
    # No option may be a dead end.
    for group in ["credits", "categories", "course_types", "semesters", "departments"]:
        assert all(option["total"] > 0 for option in data[group]), group


def test_facet_totals_add_up(student_api, catalogue):
    data = student_api.get(FACETS_URL).data
    for group in ["credits", "categories", "course_types", "semesters", "departments"]:
        assert sum(o["total"] for o in data[group]) == data["total"], group


def test_facet_counts_track_the_applied_filters(student_api, catalogue):
    cse = catalogue["CSE"]
    data = student_api.get(FACETS_URL, {"department": cse.id}).data
    assert data["count"] == SUBJECT_COUNTS["CSE"]
    assert data["total"] == sum(SUBJECT_COUNTS.values())

    # Options still list every department, but only CSE counts anything.
    by_code = {d["code"]: d for d in data["departments"]}
    assert len(by_code) == len(CURRICULA)
    assert by_code["CSE"]["count"] == SUBJECT_COUNTS["CSE"]

    # Semester counts are now CSE's semesters, not the college's.
    for row in data["semesters"]:
        assert row["count"] == cse.semesters.get(semester_number=row["value"]).subjects.count()


def test_a_facet_is_counted_with_its_own_filter_lifted(student_api, catalogue):
    """Choosing PC must not zero every other category.

    Faceted search counts each dimension as though only the *other* filters
    applied — otherwise the moment you pick one value, every alternative reads
    "0" and the control becomes a dead end you cannot see out of.
    """
    cse = catalogue["CSE"]
    data = student_api.get(FACETS_URL, {"department": cse.id, "category": "PC"}).data

    by_category = {c["value"]: c["count"] for c in data["categories"]}
    assert by_category["PC"] == data["count"]
    # PE is still counted, because the category filter is lifted for this facet.
    assert by_category["PE"] == count(student_api, department=cse.id, category="PE")
    assert by_category["PE"] > 0

    # Other dimensions keep the category filter applied.
    for row in data["credits"]:
        assert row["count"] == count(
            student_api, department=cse.id, category="PC", credits=row["value"]
        )


def test_facet_count_agrees_with_the_list_endpoint(student_api, catalogue):
    for query in [
        {},
        {"department": catalogue["FT"].id},
        {"category": "PC", "credits": 3},
        {"search": "laboratory"},
        {"department_search": "cyber", "course_type": "THEORY"},
        {"semester_number": "1,2", "credits": "4,5"},
    ]:
        facets = student_api.get(FACETS_URL, query).data
        assert facets["count"] == count(student_api, **query), query


def test_facets_reject_the_same_invalid_values_as_the_list(student_api, catalogue):
    assert student_api.get(FACETS_URL, {"credits": "abc"}).status_code == 400
    assert student_api.get(FACETS_URL, {"category": "EEC"}).status_code == 400


def test_facets_never_offer_a_department_without_a_syllabus(student_api, catalogue):
    """A department with no courses is not a filter option.

    It could only ever return an empty page, and the department selector already
    shows it with its own empty state. Every canonical department now carries a
    syllabus, so the counterexample is created here rather than found.
    """
    data = student_api.get(FACETS_URL).data
    offered = {d["code"] for d in data["departments"]}
    assert offered == set(CURRICULA)

    Department.objects.create(name="Unseeded Department", code="NO-SYLLABUS")
    after = student_api.get(FACETS_URL).data
    assert {d["code"] for d in after["departments"]} == offered
    assert Department.objects.count() > len(offered)


# --------------------------------------------------------------------------- #
# Permissions are unchanged by any of this
# --------------------------------------------------------------------------- #
def test_filtering_does_not_grant_write_access(student_api, catalogue):
    subject = Subject.objects.filter(semester__department=catalogue["CSE-CS"]).first()
    assert student_api.delete(f"{SUBJECTS_URL}{subject.id}/").status_code == 403
    assert student_api.post(SUBJECTS_URL, {"course_title": "Forged"}).status_code == 403


def test_anonymous_cannot_filter_the_catalogue(api, catalogue):
    assert api.get(SUBJECTS_URL).status_code == 401
    assert api.get(SUBJECTS_URL, {"department": catalogue["CSE"].id}).status_code == 401


def test_admin_sees_the_same_filtered_catalogue(admin_api, student_api, catalogue):
    query = {"department": catalogue["FT"].id, "category": "PC", "page_size": 500}
    assert ids(admin_api.get(SUBJECTS_URL, query)) == ids(student_api.get(SUBJECTS_URL, query))
