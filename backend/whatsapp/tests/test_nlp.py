"""Alias extraction and the LLM-fallback contract.

`GROQ_API_KEY` is unset in every test (the conftest never sets it), so
`_llm_subject` short-circuits without a network call — these tests exercise
the free, offline path every deployment falls back to when the key is absent
or Groq's free tier is rate-limited.
"""

from __future__ import annotations

from resources.models import ContentKind, ResourceType

from whatsapp.services import nlp


def test_direct_form_needs_no_llm():
    intent = nlp.extract_intent("unit 1 data structure notes")
    assert intent.unit == ResourceType.UNIT_1
    assert intent.kind == ContentKind.NOTES
    assert "data structure" in intent.subject_query


def test_bare_subject_only():
    intent = nlp.extract_intent("Data structures")
    assert intent.unit is None
    assert intent.kind is None
    assert intent.subject_query.lower() == "data structures"


def test_cat_and_reference_aliases():
    intent = nlp.extract_intent("cat 2 reference links for operating systems")
    assert intent.unit == ResourceType.CAT_2
    assert intent.kind == ContentKind.REFERENCE
    assert "operating systems" in intent.subject_query


def test_semester_exam_alias_variants():
    for phrase, expected_remainder in [
        ("end sem question paper for dbms", "question paper for dbms"),
        ("semester exam dbms", "dbms"),
    ]:
        intent = nlp.extract_intent(phrase)
        assert intent.unit == ResourceType.SEMESTER_EXAM
        assert expected_remainder in intent.subject_query


def test_youtube_alias():
    intent = nlp.extract_intent("youtube videos unit 3 python")
    assert intent.unit == ResourceType.UNIT_3
    assert intent.kind == ContentKind.YOUTUBE


def test_no_alias_present():
    unit, kind, remainder = nlp._extract_aliases("just the subject name")
    assert unit is None
    assert kind is None
    assert remainder == "just the subject name"


def test_llm_skipped_without_api_key(settings):
    settings.GROQ_API_KEY = ""
    assert nlp._llm_subject("anything") is None
