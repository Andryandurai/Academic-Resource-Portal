"""Academic catalogue endpoints.

Read access for any authenticated user; write access for administrators only,
enforced by ``IsAdminOrReadOnly`` on the viewset itself.
"""

from __future__ import annotations

import django_filters as filters
from django.db.models import BooleanField, Case, Count, Q, Value, When
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdminOrReadOnly

from .filters import SubjectFilter, roman
from .models import (
    CourseCategory,
    CourseType,
    Department,
    Semester,
    Subject,
)
from .serializers import (
    DepartmentSerializer,
    SemesterSerializer,
    SubjectSerializer,
    SubjectWriteSerializer,
)


class DepartmentFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    is_active = filters.BooleanFilter()

    class Meta:
        model = Department
        fields = ["is_active"]

    def filter_search(self, queryset, name, value):
        """Match a department name or its code, case-insensitively.

        Searching "CSE" has to find "Computer Science and Engineering", and
        "Artificial" has to find both AI departments — so the code and the name
        are both searched rather than one or the other.
        """
        term = (value or "").strip()
        if not term:
            return queryset
        return queryset.filter(Q(name__icontains=term) | Q(code__icontains=term))


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """The college's departments — the root of the academic hierarchy.

    Read-only over the API: departments are seeded and are not user-generated
    content, so there is no endpoint through which one could be invented.
    """

    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_class = DepartmentFilter

    def get_queryset(self):
        # `has_curriculum` is computed in one query for the whole list rather
        # than per card, so the selection page costs a single round trip.
        return (
            Department.objects.annotate(
                semester_count=Count("semesters", distinct=True),
                subject_count=Count("semesters__subjects", distinct=True),
            )
            .annotate(has_curriculum=Case(
                When(subject_count__gt=0, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ))
            .order_by("name")
        )


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    """Semesters for a department, with their subject counts.

    Read-only by design: semesters are structural, not editable content.
    Filter with `?department=<id>` — a department with no curriculum yet
    correctly returns an empty list rather than another department's semesters.
    """

    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_fields = ["department"]

    def get_queryset(self):
        return (
            Semester.objects.select_related("department")
            .annotate(subject_count=Count("subjects"))
            .order_by("department__name", "semester_number")
        )


class SubjectViewSet(viewsets.ModelViewSet):
    """The subject catalogue.

    GET is open to every signed-in user; POST/PUT/PATCH/DELETE return 403 for a
    student regardless of what the client sends.
    """

    permission_classes = [IsAdminOrReadOnly]
    filterset_class = SubjectFilter

    def get_queryset(self):
        return (
            Subject.objects.select_related("semester", "semester__department")
            .annotate(resource_count=Count("resources"))
            .order_by("semester__semester_number", "course_type", "course_code", "course_title")
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SubjectWriteSerializer
        return SubjectSerializer

    def destroy(self, request, *args, **kwargs):
        """Refuse to delete a subject that still holds resources.

        Cascading would silently destroy uploaded files along with the row. The
        administrator is asked to deal with the material first — losing a
        semester of notes to one click is not a recoverable mistake.
        """
        subject = self.get_object()
        attached = subject.resources.count()
        if attached:
            return Response(
                {
                    "detail": (
                        f'"{subject.course_title}" still has {attached} resource'
                        f'{"" if attached == 1 else "s"}. Delete or reassign them '
                        "before removing the subject."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="resource-counts")
    def resource_counts(self, request, pk=None):
        """Published resource count for each of the eight categories.

        Returned as a complete map with zeros included, so the subject page can
        render all eight cards from one response without inventing the gaps.
        """
        from resources.models import ResourceType

        subject = self.get_object()
        counts = {choice: 0 for choice, _ in ResourceType.choices}

        # `.order_by()` clears Resource's default ordering. Without it Django
        # adds `created_at` to the GROUP BY, which splits every row into its own
        # group and the counts come back wrong.
        rows = subject.resources.order_by().values("resource_type").annotate(total=Count("id"))
        for row in rows:
            counts[row["resource_type"]] = row["total"]

        return Response(counts)

    @action(detail=False, methods=["get"])
    def facets(self, request):
        """GET /api/subjects/facets/ — the filter options, and how many match.

        Every option is derived from the catalogue itself, so the filter bar can
        never offer a credit value, category or course type that no course has.
        That matters here: the portal deliberately excludes non-credit, EEC and
        project courses, so offering those as filters would give a dead option
        that always answers "0 results".

        Each facet is counted with *its own* filter lifted but every other
        filter still applied — the standard faceted-search rule. Having picked
        Professional Core, the category counts still show what switching to
        Professional Elective would give, instead of zero for everything.
        """
        filtered = self.filter_queryset(self.get_queryset())

        def counts_for(param: str, *fields: str) -> dict:
            """Group counts over the catalogue with `param`'s own filter removed."""
            params = request.query_params.copy()
            params.pop(param, None)
            filterset = self.filterset_class(
                params, queryset=self.get_queryset(), request=request
            )
            queryset = filterset.qs if filterset.is_valid() else filtered
            rows = queryset.order_by().values(*fields).annotate(total=Count("id", distinct=True))
            return {tuple(row[f] for f in fields): row["total"] for row in rows}

        # Options come from the whole catalogue so a facet never disappears
        # mid-search; the count beside it comes from the filtered set.
        catalogue = self.get_queryset().order_by()

        department_rows = (
            catalogue.values(
                "semester__department_id",
                "semester__department__code",
                "semester__department__name",
            )
            .annotate(total=Count("id", distinct=True))
            .order_by("semester__department__name")
        )
        department_counts = counts_for("department", "semester__department_id")
        departments = [
            {
                "value": row["semester__department_id"],
                "code": row["semester__department__code"],
                "label": row["semester__department__name"],
                "total": row["total"],
                "count": department_counts.get((row["semester__department_id"],), 0),
            }
            for row in department_rows
        ]

        semester_counts = counts_for("semester_number", "semester__semester_number")
        semesters = [
            {
                "value": row["semester__semester_number"],
                "label": f"Semester {roman(row['semester__semester_number'])}",
                "total": row["total"],
                "count": semester_counts.get((row["semester__semester_number"],), 0),
            }
            for row in catalogue.values("semester__semester_number")
            .annotate(total=Count("id", distinct=True))
            .order_by("semester__semester_number")
        ]

        category_counts = counts_for("category", "category")
        categories = [
            {
                "value": row["category"],
                "label": CourseCategory(row["category"]).label,
                "total": row["total"],
                "count": category_counts.get((row["category"],), 0),
            }
            for row in catalogue.values("category")
            .annotate(total=Count("id", distinct=True))
            .order_by("category")
        ]

        type_counts = counts_for("course_type", "course_type")
        course_types = [
            {
                "value": row["course_type"],
                "label": CourseType(row["course_type"]).label,
                "total": row["total"],
                "count": type_counts.get((row["course_type"],), 0),
            }
            for row in catalogue.values("course_type")
            .annotate(total=Count("id", distinct=True))
            .order_by("course_type")
        ]

        credit_counts = counts_for("credits", "credits")
        credits = [
            {
                "value": row["credits"],
                "label": str(row["credits"]),
                "total": row["total"],
                "count": credit_counts.get((row["credits"],), 0),
            }
            for row in catalogue.values("credits")
            .annotate(total=Count("id", distinct=True))
            .order_by("credits")
        ]

        return Response(
            {
                "count": filtered.count(),
                "total": Subject.objects.count(),
                "departments": departments,
                "semesters": semesters,
                "categories": categories,
                "course_types": course_types,
                "credits": credits,
            }
        )


class CatalogueStatsView(APIView):
    """GET /api/stats/ — the dashboard counters.

    Computed from the database on every call. Nothing here is hard-coded, and a
    portal with no uploads reports zero rather than a decorative number.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from resources.models import EXAM_RESOURCE_TYPES, Resource

        # `?department=<id>` scopes every counter to that department, so the
        # student dashboard reports its own department's totals rather than the
        # whole college's. Omitted, the numbers are college-wide.
        department = request.query_params.get("department")
        semesters = Semester.objects.all()
        subjects = Subject.objects.all()
        resources = Resource.objects.all()

        if department:
            try:
                department_id = int(department)
            except (TypeError, ValueError):
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"department": "Must be a numeric department id."})
            semesters = semesters.filter(department_id=department_id)
            subjects = subjects.filter(semester__department_id=department_id)
            resources = resources.filter(subject__semester__department_id=department_id)

        payload = {
            "department": int(department) if department else None,
            "semesters": semesters.count(),
            "subjects": subjects.count(),
            "resources": resources.count(),
            "exam_resources": resources.filter(
                resource_type__in=EXAM_RESOURCE_TYPES
            ).count(),
        }

        if request.user.is_admin:
            from django.utils import timezone

            from accounts.models import Role, User

            month_start = timezone.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            payload.update(
                {
                    "students": User.objects.filter(role=Role.STUDENT).count(),
                    "admins": User.objects.filter(role=Role.ADMIN).count(),
                    "departments": Department.objects.filter(is_active=True).count(),
                    "uploaded_this_month": resources.filter(
                        created_at__gte=month_start
                    ).count(),
                }
            )

        return Response(payload)
