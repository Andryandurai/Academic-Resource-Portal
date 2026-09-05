"""Department and subject resolution — the fuzzy matching a chat turn needs."""

from __future__ import annotations

import pytest

from whatsapp.services import catalog

pytestmark = pytest.mark.django_db


def test_find_department_by_code(curriculum):
    assert catalog.find_department("AI&DS") is curriculum or catalog.find_department("AI&DS").pk == curriculum.pk


def test_find_department_by_close_name(curriculum):
    dept = catalog.find_department("artificial intelligence and data science")
    assert dept is not None
    assert dept.pk == curriculum.pk


def test_find_department_unmatched_returns_none(curriculum):
    assert catalog.find_department("completely unrelated gibberish xyz") is None


def test_departments_with_curriculum_excludes_empty_department(curriculum, empty_department):
    codes = {d.code for d in catalog.departments_with_curriculum()}
    assert curriculum.code in codes
    assert empty_department.code not in codes


def test_resolve_subjects_confident_match(data_structures):
    matches = catalog.resolve_subjects(data_structures.semester, "data structure")
    assert matches
    assert matches[0].subject.pk == data_structures.pk
    assert matches[0].score >= catalog.CONFIDENT_SUBJECT_SCORE


def test_resolve_subjects_no_match(data_structures):
    assert catalog.resolve_subjects(data_structures.semester, "quantum thermodynamics of whales") == []


def test_resolve_subjects_ambiguous_query_returns_several(ambiguous_semester):
    semester, maths_1, maths_2 = ambiguous_semester
    matches = catalog.resolve_subjects(semester, "engineering mathematics")
    assert len(matches) >= 2
    top_two = {m.subject.pk for m in matches[:2]}
    assert {maths_1.pk, maths_2.pk} == top_two
    # Close enough that a caller should ask "did you mean" rather than guess.
    assert matches[0].score - matches[1].score < 0.08


def test_alias_maps():
    assert catalog.match_unit_alias("Unit 1") == "UNIT_1"
    assert catalog.match_unit_alias("cat2") == "CAT_2"
    assert catalog.match_unit_alias("end sem") == "SEMESTER_EXAM"
    assert catalog.match_unit_alias("not a unit") is None

    assert catalog.match_kind_alias("Notes") == "NOTES"
    assert catalog.match_kind_alias("youtube videos") == "YOUTUBE"
    assert catalog.match_kind_alias("reference links") == "REFERENCE"
    assert catalog.match_kind_alias("gibberish") is None
