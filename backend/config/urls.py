"""Root URL configuration."""

from django.http import JsonResponse
from django.urls import include, path, re_path

from . import privacy, spa


def health(_request):
    """Liveness probe. Deliberately unauthenticated and cheap."""
    from django.conf import settings

    return JsonResponse({"status": "ok", "app": settings.APP_NAME, "version": settings.API_VERSION})


urlpatterns = [
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("academics.urls")),
    path("api/", include("resources.urls")),
    path("api/whatsapp/", include("whatsapp.urls")),
    path("privacy/", privacy.index, name="privacy-policy"),
    # Everything the API did not claim is a client-side route. `api/` and
    # `static/` are excluded so an unknown endpoint still returns a JSON-shaped
    # 404 rather than the SPA shell with a 200 — a mistyped API path that answers
    # "200 OK, here is some HTML" is a genuinely hard bug to read.
    re_path(r"^(?!api/|static/).*$", spa.index, name="spa"),
]
