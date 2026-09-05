"""Read-only lookups the conversation needs: departments, subjects, resources.

Nothing here is WhatsApp-specific — it is the same `academics`/`resources`
schema the REST API already serves, queried the way a chat turn needs it:
fuzzy, forgiving of typos, and always scoped to one student's own department so
a CSE student can never be handed an ECE department's material by a
near-miss subject name.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from django.db.models import Count

from academics.models import Department, Semester, Subject
from resources.models import (
    EXAM_RESOURCE_TYPES,
    LEARNING_RESOURCE_TYPES,
    ContentKind,
    Resource,
    ResourceType,
)

#: Subject match below this similarity is not offered at all.
MIN_SUBJECT_SCORE = 0.45
#: Above this, a single match is confident enough to act on without asking
#: "did you mean" — picked empirically: two real subjects in one department
#: rarely score this close to a distinctive query like "data structures".
CONFIDENT_SUBJECT_SCORE = 0.72
MAX_SUBJECT_CANDIDATES = 5

RESOURCE_TYPE_LABELS: dict[str, str] = dict(ResourceType.choices)
KIND_LABELS: dict[str, str] = dict(ContentKind.choices)

# Aliases a student actually types, mapped onto the stored choice values.
UNIT_ALIASES: dict[str, str] = {
    "unit 1": ResourceType.UNIT_1, "unit1": ResourceType.UNIT_1, "1": ResourceType.UNIT_1,
    "unit 2": ResourceType.UNIT_2, "unit2": ResourceType.UNIT_2, "2": ResourceType.UNIT_2,
    "unit 3": ResourceType.UNIT_3, "unit3": ResourceType.UNIT_3, "3": ResourceType.UNIT_3,
    "unit 4": ResourceType.UNIT_4, "unit4": ResourceType.UNIT_4, "4": ResourceType.UNIT_4,
    "unit 5": ResourceType.UNIT_5, "unit5": ResourceType.UNIT_5, "5": ResourceType.UNIT_5,
    "cat 1": ResourceType.CAT_1, "cat1": ResourceType.CAT_1, "cat-1": ResourceType.CAT_1,
    "cat 2": ResourceType.CAT_2, "cat2": ResourceType.CAT_2, "cat-2": ResourceType.CAT_2,
    "semester exam": ResourceType.SEMESTER_EXAM,
    "sem exam": ResourceType.SEMESTER_EXAM,
    "end sem": ResourceType.SEMESTER_EXAM,
    "endsem": ResourceType.SEMESTER_EXAM,
    "final exam": ResourceType.SEMESTER_EXAM,
    "university exam": ResourceType.SEMESTER_EXAM,
}

KIND_ALIASES: dict[str, str] = {
    "notes": ContentKind.NOTES, "note": ContentKind.NOTES, "pdf": ContentKind.NOTES,
    "material": ContentKind.NOTES,
    "reference": ContentKind.REFERENCE, "references": ContentKind.REFERENCE,
    "reference link": ContentKind.REFERENCE, "reference links": ContentKind.REFERENCE,
    "link": ContentKind.REFERENCE, "links": ContentKind.REFERENCE,
    "youtube": ContentKind.YOUTUBE, "you tube": ContentKind.YOUTUBE,
    "video": ContentKind.YOUTUBE, "videos": ContentKind.YOUTUBE,
    "youtube video": ContentKind.YOUTUBE, "youtube videos": ContentKind.YOUTUBE,
    "video link": ContentKind.YOUTUBE, "video links": ContentKind.YOUTUBE,
}


def match_unit_alias(text: str) -> str | None:
    """Map a loose phrase like "unit 1" or "cat2" onto a `ResourceType` value."""
    return UNIT_ALIASES.get(_normalize(text))


def match_kind_alias(text: str) -> str | None:
    """Map a loose phrase like "youtube videos" onto a `ContentKind` value."""
    return KIND_ALIASES.get(_normalize(text))


def _normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def departments_with_curriculum():
    """Departments a student can actually be onboarded into.

    A department with no syllabus loaded yet has nothing to search — offering
    it in the menu would only produce "no subjects found" for every query, so
    it is left out until `seed_academics` publishes its curriculum.
    """
    return (
        Department.objects.filter(is_active=True)
        .annotate(subject_count=Count("semesters__subjects"))
        .filter(subject_count__gt=0)
        .order_by("name")
    )


def find_department(query: str) -> Department | None:
    """Resolve a department by name, code, or a close fuzzy match to either."""
    text = _normalize(query)
    if not text:
        return None
    candidates = list(departments_with_curriculum())
    for dept in candidates:
        if _normalize(dept.code) == text or _normalize(dept.name) == text:
            return dept
    best, best_score = None, 0.0
    for dept in candidates:
        score = max(_similarity(text, dept.code), _similarity(text, dept.name))
        if score > best_score:
            best, best_score = dept, score
    return best if best_score >= MIN_SUBJECT_SCORE else None


def semesters_for(department: Department):
    return Semester.objects.filter(department=department).order_by("semester_number")


def _similarity(a: str, b: str) -> float:
    a, b = _normalize(a), _normalize(b)
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    # A query that is a substring of the real title ("data structure" inside
    # "Data Structures and Algorithms") is a strong signal difflib's character
    # ratio alone underweights on a short query against a long title.
    if a in b or b in a:
        ratio = max(ratio, 0.85)
    return ratio


@dataclass
class SubjectMatch:
    subject: Subject
    score: float


def resolve_subjects(semester: Semester, query: str) -> list[SubjectMatch]:
    """Rank every subject of one semester against a free-text query.

    Scoped to a single semester (not the whole department) because course
    titles repeat across years — "Communication Skills" appears in more than
    one semester — and a student is always asking about their own year's
    subject list.
    """
    text = _normalize(query)
    if not text:
        return []
    scored: list[SubjectMatch] = []
    for subject in Subject.objects.filter(semester=semester):
        score = _similarity(text, subject.course_title)
        if subject.course_code:
            score = max(score, _similarity(text, subject.course_code))
        if score >= MIN_SUBJECT_SCORE:
            scored.append(SubjectMatch(subject, score))
    scored.sort(key=lambda m: m.score, reverse=True)
    return scored[:MAX_SUBJECT_CANDIDATES]


def resource_type_menu_sections() -> list[dict]:
    """The eight categories, grouped the way the site already groups them."""
    return [
        {
            "title": "Learning material",
            "rows": [
                {"id": f"unit:{rt}", "title": RESOURCE_TYPE_LABELS[rt]} for rt in LEARNING_RESOURCE_TYPES
            ],
        },
        {
            "title": "Examination resources",
            "rows": [
                {"id": f"unit:{rt}", "title": RESOURCE_TYPE_LABELS[rt]} for rt in EXAM_RESOURCE_TYPES
            ],
        },
    ]


def kind_menu_buttons() -> list[tuple[str, str]]:
    return [(f"kind:{k}", label) for k, label in ContentKind.choices]


def resources_for(subject: Subject, resource_type: str, kind: str):
    return (
        Resource.objects.filter(subject=subject, resource_type=resource_type, kind=kind)
        .order_by("title", "-created_at")
    )


def has_any_resource(subject: Subject, resource_type: str) -> bool:
    return Resource.objects.filter(subject=subject, resource_type=resource_type).exists()
