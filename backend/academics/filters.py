"""Subject filtering.

Filtering runs in the database so the SPA never has to pull the whole catalogue
to narrow it down.
"""

from __future__ import annotations

import django_filters as filters
from django.db.models import Q

from .models import CourseCategory, CourseType, Subject


class SubjectFilter(filters.FilterSet):
    # Scoping runs in the database, through the Semester -> Department foreign
    # key. A client asking for department 5 cannot be served department 1's
    # subjects, whatever it sends.
    department = filters.NumberFilter(field_name="semester__department_id")
    department_code = filters.CharFilter(
        field_name="semester__department__code", lookup_expr="iexact"
    )
    # Accepts either the semester's primary key or its ordinal (1-8): the
    # student UI knows subjects by "Semester V", not by a database id.
    semester = filters.NumberFilter(field_name="semester_id")
    semester_number = filters.NumberFilter(field_name="semester__semester_number")
    course_type = filters.ChoiceFilter(choices=CourseType.choices)
    category = filters.ChoiceFilter(choices=CourseCategory.choices)
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Subject
        fields = [
            "department",
            "department_code",
            "semester",
            "semester_number",
            "course_type",
            "category",
        ]

    def filter_search(self, queryset, name, value):
        """Match a course code or a course title, case-insensitively."""
        term = (value or "").strip()
        if not term:
            return queryset
        return queryset.filter(
            Q(course_code__icontains=term) | Q(course_title__icontains=term)
        )
