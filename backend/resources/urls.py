"""Resource routes, mounted at /api/."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ResourceViewSet

router = DefaultRouter()
router.register("resources", ResourceViewSet, basename="resource")

urlpatterns = [path("", include(router.urls))]
