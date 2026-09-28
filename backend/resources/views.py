"""Resource endpoints: browse, upload, replace, delete and download."""

from __future__ import annotations

import unicodedata
from urllib.parse import quote

import django_filters as filters
from django.http import FileResponse, Http404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions import IsAdminOrReadOnly

from .models import Resource, ResourceType
from .serializers import ResourceSerializer, ResourceWriteSerializer


class ResourceFilter(filters.FilterSet):
    subject = filters.NumberFilter(field_name="subject_id")
    # Resources reach a department through Subject -> Semester -> Department, so
    # scoping happens in the database. A resource published under AI&DS cannot
    # be surfaced under another department by any combination of query
    # parameters.
    department = filters.NumberFilter(field_name="subject__semester__department_id")
    semester = filters.NumberFilter(field_name="subject__semester_id")
    semester_number = filters.NumberFilter(field_name="subject__semester__semester_number")
    resource_type = filters.ChoiceFilter(choices=ResourceType.choices)
    uploaded_from = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    uploaded_to = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Resource
        fields = ["subject", "department", "semester", "resource_type"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        term = (value or "").strip()
        if not term:
            return queryset
        return queryset.filter(
            Q(title__icontains=term)
            | Q(subject__course_title__icontains=term)
            | Q(subject__course_code__icontains=term)
        )


class ResourceViewSet(viewsets.ModelViewSet):
    """CRUD for academic resources.

    Students may list, retrieve and download. Every write verb is refused for
    them by ``IsAdminOrReadOnly`` â€” the check runs on the request, so a
    hand-crafted POST is rejected exactly like a click on a hidden button would
    be.
    """

    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ResourceFilter
    # multipart for the upload itself; form data so a metadata-only edit can be
    # submitted without a file part.
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # `-id` breaks ties: two uploads can land in the same microsecond, and
        # ordering on the timestamp alone then leaves "most recent" undefined —
        # which showed up as an intermittently wrong first row on the dashboards.
        return Resource.objects.select_related(
            "subject", "subject__semester", "subject__semester__department", "uploaded_by"
        ).order_by("-created_at", "-id")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ResourceWriteSerializer
        return ResourceSerializer

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def download(self, request, pk=None):
        """Stream the stored file to any signed-in user.

        This is the only route to the bytes. MEDIA_ROOT is not served
        statically and sits outside both `frontend/` and `STATIC_ROOT`, so there
        is no public URL to guess and no unauthenticated path to the file.

        `?inline=1` renders a PDF in the browser's viewer; everything else is
        sent as an attachment.
        """
        resource = self.get_object()

        if not resource.file:
            raise Http404("The stored file for this resource is unavailable.")

        try:
            handle = resource.file.open("rb")
        except (FileNotFoundError, OSError) as exc:
            # Metadata exists but the file is gone. Reported honestly rather
            # than answered with an empty download.
            raise Http404("The stored file for this resource is unavailable.") from exc

        inline = request.query_params.get("inline") == "1" and resource.inline_viewable

        response = FileResponse(handle, content_type=resource.file_type)
        response["Content-Disposition"] = _content_disposition(
            "inline" if inline else "attachment", resource.file_name
        )
        response["Content-Length"] = str(resource.file_size or resource.file.size)
        # A document must never be sniffed into something executable, and this
        # is authenticated content so no shared cache may hold it.
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Security-Policy"] = "default-src 'none'; object-src 'none'"
        response["Cache-Control"] = "private, max-age=0, must-revalidate"
        return response

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def recent(self, request):
        """The latest uploads, for the dashboards.

        Honours `?department=<id>` so a student's dashboard shows their own
        department's activity rather than the whole college's.
        """
        try:
            limit = min(int(request.query_params.get("limit", 8)), 50)
        except (TypeError, ValueError):
            limit = 8

        queryset = self.get_queryset()
        department = request.query_params.get("department")
        if department:
            queryset = queryset.filter(subject__semester__department_id=department)

        return Response(
            ResourceSerializer(queryset[:limit], many=True, context={"request": request}).data
        )

    @action(detail=False, methods=["get"], permission_classes=[AllowAny], url_path="types")
    def types(self, request):
        """The eight categories, so the UI never hard-codes the vocabulary."""
        from .models import EXAM_RESOURCE_TYPES, LEARNING_RESOURCE_TYPES

        return Response(
            {
                "all": [{"value": v, "label": l} for v, l in ResourceType.choices],
                "learning": [str(t) for t in LEARNING_RESOURCE_TYPES],
                "examination": [str(t) for t in EXAM_RESOURCE_TYPES],
            }
        )


def _content_disposition(disposition: str, filename: str) -> str:
    """RFC 6266 header with an ASCII fallback and a UTF-8 form.

    Both are sent so a Tamil or otherwise non-Latin filename survives the round
    trip in browsers that read only one of them.
    """
    ascii_name = (
        unicodedata.normalize("NFKD", filename or "download")
        .encode("ascii", "ignore")
        .decode("ascii")
        .replace('"', "_")
        .replace("\\", "_")
    ) or "download"
    return f"{disposition}; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename or 'download')}"

