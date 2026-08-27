"""Shared test fixtures.

Uploads are redirected to a temporary media root so a test run never writes into
the real one, and the database is seeded per-test from the same curriculum
module the application uses.
"""

from __future__ import annotations

import io

import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def isolated_media(tmp_path, settings):  # noqa: F811 - pytest-django's settings fixture
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    return settings.MEDIA_ROOT


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def department(db):
    from academics.models import Department

    return Department.objects.create(name=settings.DEPARTMENT_NAME, code=settings.DEPARTMENT_CODE)


@pytest.fixture
def curriculum(db, department):
    """AI&DS only — 8 semesters, 39 subjects, no resources.

    Scoped to one department on purpose: most tests assert exact counts, and
    seeding every curriculum would make them depend on how many departments
    happen to have a syllabus today.
    """
    from django.core.management import call_command

    call_command("seed_academics", department="AI&DS", verbosity=0)
    return department


@pytest.fixture
def admin_user(db, department):
    from accounts.models import Role, User

    return User.objects.create_user(
        email="admin@rec.test",
        password="AdminPass!2026",
        name="Test Administrator",
        role=Role.ADMIN,
        department=department,
    )


@pytest.fixture
def student_user(db, department):
    from accounts.models import Role, User

    return User.objects.create_user(
        email="student@rec.test",
        password="StudentPass!2026",
        name="Test Student",
        role=Role.STUDENT,
        department=department,
    )


def authenticate(api: APIClient, user) -> APIClient:
    """Attach a real access token — not force_authenticate.

    Going through the token machinery means these tests exercise the same
    authentication path a browser does, so a broken JWT configuration fails the
    suite instead of passing it.
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api


# Each role gets its own client. Sharing one would mean the second fixture's
# `credentials()` call silently re-authenticated the first, so a test that used
# both would exercise one identity twice — and a permission test would pass for
# the wrong reason.
@pytest.fixture
def admin_api(admin_user):
    return authenticate(APIClient(), admin_user)


@pytest.fixture
def student_api(student_user):
    return authenticate(APIClient(), student_user)


def make_pdf(text: str = "Unit 1 Notes") -> bytes:
    """A minimal but structurally valid single-page PDF."""
    body = (
        "%PDF-1.4\n"
        "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 100]/Contents 4 0 R>>endobj\n"
        f"4 0 obj<</Length {len(text) + 40}>>stream\n"
        f"BT /F1 12 Tf 20 50 Td ({text}) Tj ET\n"
        "endstream endobj\n"
        "trailer<</Root 1 0 R>>\n"
        "%%EOF"
    )
    return body.encode("latin-1")


def pdf_upload(name: str = "unit1.pdf", text: str = "Unit 1 Notes"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, make_pdf(text), content_type="application/pdf")


def upload(name: str, data: bytes, content_type: str):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, data, content_type=content_type)


@pytest.fixture
def empty_department(db):
    """A department that holds no curriculum.

    Several scoping tests need a department that is genuinely empty, to prove
    that asking for it returns nothing rather than someone else's rows.

    This used to pick whichever canonical department had no syllabus yet. All
    nineteen now have one, so there is nothing left to pick and the fixture
    creates its own. It still prefers a real empty department when the
    surrounding fixture seeded only part of the catalogue.
    """
    from academics.models import Department, Subject

    unseeded = Department.objects.exclude(
        id__in=Subject.objects.values("semester__department_id")
    ).first()
    if unseeded is not None:
        return unseeded
    return Department.objects.create(name="Unseeded Department (test)", code="NO-SYLLABUS")


@pytest.fixture
def data_structures(curriculum):
    """AI&DS CS23231 Data Structures — used across the resource tests.

    Scoped to the department: CS23231 exists in AI&DS, AI&ML and EEE, so an
    unscoped lookup now matches three rows.
    """
    from academics.models import Subject

    return Subject.objects.get(course_code="CS23231", semester__department=curriculum)


# Re-exported so test modules can import them from conftest.
__all__ = ["authenticate", "make_pdf", "pdf_upload", "upload", "io"]
