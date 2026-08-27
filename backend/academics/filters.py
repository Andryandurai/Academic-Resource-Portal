"""Subject filtering.

Filtering runs in the database so the SPA never has to pull the whole catalogue
to narrow it down.

Every filter accepts a comma-separated list as well as a single value, so
``?category=PC`` and ``?category=PC,PE`` are both valid and the older
single-value URLs keep working unchanged. Values are validated against the
model's own choices, so a bad filter is a 400 rather than a silent empty page.
"""

from __future__ import annotations

import django_filters as filters
from django.db.models import Q

from .models import CourseCategory, CourseType, Subject

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


def roman(number: int) -> str:
    return ROMAN[number - 1] if 1 <= number <= len(ROMAN) else str(number)


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    """`?credits=3,4` — a CSV of numbers, or a single number."""


class ChoiceInFilter(filters.BaseInFilter, filters.ChoiceFilter):
    """`?category=PC,PE` — a CSV of choices, each validated against the model."""


class SubjectFilter(filters.FilterSet):
    # Scoping runs in the database, through the Semester -> Department foreign
    # key. A client asking for department 5 cannot be served department 1's
    # subjects, whatever it sends.
    department = NumberInFilter(field_name="semester__department_id", lookup_expr="in")
    department_code = filters.CharFilter(
        field_name="semester__department__code", lookup_expr="iexact"
    )
    # Type-to-find, for the department picker: "cyber" finds CSE (Cyber
    # Security), "CS" finds every computing department. Combines with the rest
    # of the filters like any other clause.
    department_search = filters.CharFilter(method="filter_department_search")
    # Accepts either the semester's primary key or its ordinal (1-8): the
    # student UI knows subjects by "Semester V", not by a database id.
    semester = NumberInFilter(field_name="semester_id", lookup_expr="in")
    semester_number = NumberInFilter(field_name="semester__semester_number", lookup_expr="in")
    course_type = ChoiceInFilter(field_name="course_type", lookup_expr="in", choices=CourseType.choices)
    category = ChoiceInFilter(field_name="category", lookup_expr="in", choices=CourseCategory.choices)
    credits = NumberInFilter(field_name="credits", lookup_expr="in")
    # Range variants, for "4 credits and above" style questions. Both optional
    # and independent of the exact-value list above.
    credits_min = filters.NumberFilter(field_name="credits", lookup_expr="gte")
    credits_max = filters.NumberFilter(field_name="credits", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Subject
        fields = [
            "department",
            "department_code",
            "department_search",
            "semester",
            "semester_number",
            "course_type",
            "category",
            "credits",
        ]

    def filter_department_search(self, queryset, name, value):
        term = (value or "").strip()
        if not term:
            return queryset
        return queryset.filter(
            Q(semester__department__name__icontains=term)
            | Q(semester__department__code__icontains=term)
        )

    def filter_search(self, queryset, name, value):
        """One box across course code, title, department, semester and category.

        Case-insensitive and partial throughout — `icontains` on every clause —
        because a student types "crypto" or "cyber", not an exact title. The
        clauses are OR-ed with each other and AND-ed with every other filter, so
        search narrows a filtered set rather than replacing it.
        """
        term = (value or "").strip()
        if not term:
            return queryset

        clauses = (
            Q(course_code__icontains=term)
            | Q(course_title__icontains=term)
            | Q(semester__department__name__icontains=term)
            | Q(semester__department__code__icontains=term)
            | Q(semester__name__icontains=term)
            | Q(category__icontains=term)
        )

        # "5" should find Semester V, and "V" already does through the semester
        # name. Guarded so a course code like "CS23531" is not read as an
        # ordinal and matched against every fifth-semester subject.
        if term.isdigit() and 1 <= int(term) <= 8:
            clauses |= Q(semester__semester_number=int(term))

        # The category's printed label, so "professional core" works as well as
        # "PC" — the label is what the UI shows, so it is what people type.
        matching_categories = [
            code for code, label in CourseCategory.choices if term.lower() in label.lower()
        ]
        if matching_categories:
            clauses |= Q(category__in=matching_categories)

        matching_types = [
            code for code, label in CourseType.choices if term.lower() in label.lower()
        ]
        if matching_types:
            clauses |= Q(course_type__in=matching_types)

        return queryset.filter(clauses).distinct()
