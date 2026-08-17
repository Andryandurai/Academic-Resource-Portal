"""Academic catalogue routes, mounted at /api/."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("departments", views.DepartmentViewSet, basename="department")
router.register("semesters", views.SemesterViewSet, basename="semester")
router.register("subjects", views.SubjectViewSet, basename="subject")

urlpatterns = [
    path("stats/", views.CatalogueStatsView.as_view(), name="stats"),
    path("", include(router.urls)),
]
