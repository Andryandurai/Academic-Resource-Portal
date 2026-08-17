"""Upload formats, portal isolation and the full category hierarchy.

Complements test_resources.py: this module covers the file formats the portal
promises (PDF and DOCX in particular), the "student can never reach an admin
operation" boundary across every write verb, and the semester → subject →
category → resource walk a student actually performs.
"""

from __future__ import annotations

import io
import zipfile

import pytest

from academics.models import Semester, Subject
from conftest import make_pdf, upload
from resources.models import Resource, ResourceType

pytestmark = pytest.mark.django_db


# --------------------------------------------------------------------------- #
# Fixtures for the Office formats
# --------------------------------------------------------------------------- #
def make_ooxml(kind: str = "docx") -> bytes:
    """A real OOXML container.

    docx/pptx/xlsx are ZIP archives, so this builds an actual archive with the
    parts Office writes. A hand-rolled `PK` header would pass the signature
    check without proving the check accepts genuine documents.
    """
    content_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }[kind]

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            f'<Default Extension="xml" ContentType="{content_types}"/>'
            "</Types>",
        )
        archive.writestr("word/document.xml", "<document>Unit 2 notes</document>")
    return buffer.getvalue()


def make_legacy_office() -> bytes:
    """An OLE compound-file header, as .doc/.ppt/.xls carry."""
    return b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 512


MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "doc": "application/msword",
    "ppt": "application/vnd.ms-powerpoint",
    "xls": "application/vnd.ms-excel",
}


def bytes_for(ext: str) -> bytes:
    if ext == "pdf":
        return make_pdf("Notes")
    if ext in ("docx", "pptx", "xlsx"):
        return make_ooxml(ext)
    return make_legacy_office()


def post_resource(client, subject, ext, *, resource_type="UNIT_1", title=None):
    return client.post(
        "/api/resources/",
        {
            "subject": subject.id,
            "resource_type": resource_type,
            "title": title or f"{ext.upper()} material",
            "description": "",
            "file": upload(f"material.{ext}", bytes_for(ext), MEDIA_TYPES[ext]),
        },
        format="multipart",
    )


# --------------------------------------------------------------------------- #
# Every supported format
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("ext", ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx"])
def test_every_supported_format_uploads(admin_api, data_structures, ext):
    response = post_resource(admin_api, data_structures, ext)
    assert response.status_code == 201, response.data
    assert response.data["file_ext"] == ext
    assert response.data["file_type"] == MEDIA_TYPES[ext]


def test_pdf_is_previewable_and_docx_is_not(admin_api, data_structures):
    """The UI must not offer an in-browser preview it cannot deliver."""
    pdf = post_resource(admin_api, data_structures, "pdf", resource_type="UNIT_1")
    docx = post_resource(admin_api, data_structures, "docx", resource_type="UNIT_2")

    assert pdf.data["inline_viewable"] is True
    assert docx.data["inline_viewable"] is False
    assert docx.data["file_type_label"] == "Word"


def test_docx_round_trips_to_the_student(admin_api, student_api, data_structures):
    """The DOCX flow end to end: admin publishes, student sees and downloads."""
    created = post_resource(
        admin_api,
        data_structures,
        "docx",
        resource_type="UNIT_2",
        title="Unit 2 Revision Material",
    )
    assert created.status_code == 201
    resource_id = created.data["id"]

    listing = student_api.get(
        "/api/resources/", {"subject": data_structures.id, "resource_type": "UNIT_2"}
    )
    assert listing.data["count"] == 1
    assert listing.data["results"][0]["title"] == "Unit 2 Revision Material"

    download = student_api.get(f"/api/resources/{resource_id}/download/")
    assert download.status_code == 200
    body = b"".join(download.streaming_content)
    # A genuine ZIP container, not a stub.
    assert body[:2] == b"PK"
    assert zipfile.ZipFile(io.BytesIO(body)).namelist()

    # Even asking for inline, a DOCX is sent as an attachment.
    inline = student_api.get(f"/api/resources/{resource_id}/download/", {"inline": "1"})
    assert inline["Content-Disposition"].startswith("attachment")


def test_pdf_round_trips_to_the_student(admin_api, student_api, data_structures):
    created = post_resource(
        admin_api, data_structures, "pdf", resource_type="UNIT_1", title="Unit 1 Complete Notes"
    )
    resource_id = created.data["id"]

    listing = student_api.get(
        "/api/resources/", {"subject": data_structures.id, "resource_type": "UNIT_1"}
    )
    assert listing.data["count"] == 1

    download = student_api.get(f"/api/resources/{resource_id}/download/")
    assert b"".join(download.streaming_content).startswith(b"%PDF-")


@pytest.mark.parametrize(
    "name,data,declared",
    [
        ("script.js", b"alert(1)", "application/javascript"),
        ("payload.exe", b"MZ\x90\x00", "application/x-msdownload"),
        ("archive.zip", b"PK\x03\x04rest", "application/zip"),
        ("page.html", b"<html></html>", "text/html"),
        ("notes.docx", b"MZ\x90\x00 not really a docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("notes.pdf", make_ooxml("docx"), "application/pdf"),
    ],
)
def test_dangerous_or_mislabelled_files_are_rejected(
    admin_api, data_structures, name, data, declared
):
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": data_structures.id,
            "resource_type": "UNIT_1",
            "title": "Rejected upload",
            "file": upload(name, data, declared),
        },
        format="multipart",
    )
    assert response.status_code == 400, f"{name} was accepted"
    assert Resource.objects.count() == 0


def test_multiple_formats_coexist_in_one_category(admin_api, student_api, data_structures):
    """A category is a folder, not a slot: uploading does not overwrite."""
    for index, ext in enumerate(["pdf", "docx", "pdf"]):
        assert (
            post_resource(
                admin_api, data_structures, ext, resource_type="UNIT_1", title=f"Unit 1 item {index}"
            ).status_code
            == 201
        )

    listing = student_api.get(
        "/api/resources/", {"subject": data_structures.id, "resource_type": "UNIT_1"}
    )
    assert listing.data["count"] == 3
    assert Resource.objects.filter(subject=data_structures, resource_type="UNIT_1").count() == 3


# --------------------------------------------------------------------------- #
# Portal isolation — every admin write verb, from a student token
# --------------------------------------------------------------------------- #
def test_student_is_refused_every_resource_write_verb(admin_api, student_api, data_structures):
    resource_id = post_resource(admin_api, data_structures, "pdf").data["id"]

    attempts = {
        "POST": student_api.post(
            "/api/resources/",
            {
                "subject": data_structures.id,
                "resource_type": "UNIT_1",
                "title": "Forged",
                "file": upload("f.pdf", make_pdf(), "application/pdf"),
            },
            format="multipart",
        ),
        "PUT": student_api.put(
            f"/api/resources/{resource_id}/",
            {
                "subject": data_structures.id,
                "resource_type": "UNIT_1",
                "title": "Forged",
                "file": upload("f.pdf", make_pdf(), "application/pdf"),
            },
            format="multipart",
        ),
        "PATCH": student_api.patch(
            f"/api/resources/{resource_id}/", {"title": "Forged"}, format="multipart"
        ),
        "DELETE": student_api.delete(f"/api/resources/{resource_id}/"),
    }

    for verb, response in attempts.items():
        assert response.status_code == 403, f"{verb} was not refused"

    resource = Resource.objects.get(id=resource_id)
    assert resource.title == "PDF material"
    assert Resource.objects.count() == 1


def test_student_is_refused_every_subject_write_verb(student_api, data_structures):
    semester = Semester.objects.get(semester_number=1)
    payload = {
        "semester": semester.id,
        "course_title": "Forged Subject",
        "category": "PC",
        "course_type": "THEORY",
        "l": 3,
        "t": 0,
        "p": 0,
        "credits": 3,
    }

    attempts = {
        "POST": student_api.post("/api/subjects/", payload, format="json"),
        "PUT": student_api.put(f"/api/subjects/{data_structures.id}/", payload, format="json"),
        "PATCH": student_api.patch(
            f"/api/subjects/{data_structures.id}/", {"credits": 99}, format="json"
        ),
        "DELETE": student_api.delete(f"/api/subjects/{data_structures.id}/"),
    }

    for verb, response in attempts.items():
        assert response.status_code == 403, f"{verb} was not refused"

    data_structures.refresh_from_db()
    assert data_structures.credits == 5
    assert not Subject.objects.filter(course_title="Forged Subject").exists()


def test_admin_can_perform_the_same_operations(admin_api, data_structures):
    """The mirror of the two tests above: the verbs work for an administrator."""
    semester = Semester.objects.get(semester_number=1)
    created = admin_api.post(
        "/api/subjects/",
        {
            "semester": semester.id,
            "course_code": "ZZ12345",
            "course_title": "Admin Created Subject",
            "category": "PC",
            "course_type": "THEORY",
            "l": 3,
            "t": 0,
            "p": 0,
            "credits": 3,
        },
        format="json",
    )
    assert created.status_code == 201
    assert admin_api.patch(
        f"/api/subjects/{created.data['id']}/", {"credits": 4}, format="json"
    ).status_code == 200
    assert admin_api.delete(f"/api/subjects/{created.data['id']}/").status_code == 204

    resource_id = post_resource(admin_api, data_structures, "pdf").data["id"]
    assert admin_api.patch(
        f"/api/resources/{resource_id}/", {"title": "Renamed by admin"}, format="multipart"
    ).status_code == 200
    assert admin_api.delete(f"/api/resources/{resource_id}/").status_code == 204


def test_student_token_cannot_reach_admin_only_endpoints(student_api):
    for path in ["/api/auth/users/", "/api/auth/users/stats/"]:
        assert student_api.get(path).status_code == 403, path


def test_stats_hides_administrative_counters_from_students(student_api, admin_api, curriculum):
    student = student_api.get("/api/stats/").data
    assert "students" not in student and "uploaded_this_month" not in student

    admin = admin_api.get("/api/stats/").data
    assert "students" in admin and "uploaded_this_month" in admin


# --------------------------------------------------------------------------- #
# The student's navigation path
# --------------------------------------------------------------------------- #
def test_semester_to_subject_to_category_to_resource(admin_api, student_api, curriculum):
    """Walks exactly the route the student UI takes, one API call per step."""
    semesters = student_api.get("/api/semesters/").data
    semester_two = next(s for s in semesters if s["semester_number"] == 2)
    assert semester_two["subject_count"] == 6

    subjects = student_api.get("/api/subjects/", {"semester": semester_two["id"]}).data
    assert subjects["count"] == 6
    subject = next(s for s in subjects["results"] if s["course_code"] == "CS23231")

    # Both course types are present and distinguishable at this level.
    assert {s["course_type"] for s in subjects["results"]} == {"THEORY", "LAB_ORIENTED_THEORY"}

    detail = student_api.get(f"/api/subjects/{subject['id']}/").data
    assert (detail["l"], detail["t"], detail["p"], detail["credits"]) == (3, 0, 4, 5)

    counts = student_api.get(f"/api/subjects/{subject['id']}/resource-counts/").data
    assert set(counts) == {choice for choice, _ in ResourceType.choices}
    assert all(value == 0 for value in counts.values())

    from academics.models import Subject as SubjectModel

    subject_row = SubjectModel.objects.get(id=subject["id"])
    post_resource(admin_api, subject_row, "pdf", resource_type="CAT_1", title="CAT 1 Paper 2026")

    counts = student_api.get(f"/api/subjects/{subject['id']}/resource-counts/").data
    assert counts["CAT_1"] == 1 and counts["UNIT_1"] == 0

    listing = student_api.get(
        "/api/resources/", {"subject": subject["id"], "resource_type": "CAT_1"}
    ).data
    assert listing["count"] == 1
    assert listing["results"][0]["title"] == "CAT 1 Paper 2026"


@pytest.mark.parametrize(
    "resource_type",
    ["UNIT_1", "UNIT_2", "UNIT_3", "UNIT_4", "UNIT_5", "CAT_1", "CAT_2", "SEMESTER_EXAM"],
)
def test_each_category_is_addressable_and_isolated(
    admin_api, student_api, data_structures, resource_type
):
    """A file published to one category appears in that category and no other."""
    post_resource(
        admin_api, data_structures, "pdf", resource_type=resource_type, title=f"{resource_type} file"
    )

    counts = student_api.get(f"/api/subjects/{data_structures.id}/resource-counts/").data
    assert counts[resource_type] == 1
    assert sum(counts.values()) == 1

    listing = student_api.get(
        "/api/resources/", {"subject": data_structures.id, "resource_type": resource_type}
    ).data
    assert listing["count"] == 1


# --------------------------------------------------------------------------- #
# Session lifecycle
# --------------------------------------------------------------------------- #
def test_logout_invalidates_the_refresh_token(api, student_user):
    login = api.post(
        "/api/auth/login/",
        {"email": "student@rec.test", "password": "StudentPass!2026"},
        format="json",
    )
    access, refresh = login.data["access"], login.data["refresh"]

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code == 205

    # The refresh token is dead, so the session cannot be silently resurrected.
    assert (
        api.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json").status_code == 401
    )


def test_requests_without_a_token_are_refused_after_logout(api, curriculum):
    """What the browser does after the store is cleared: no Authorization header."""
    api.credentials()
    for path in ["/api/subjects/", "/api/semesters/", "/api/resources/", "/api/stats/", "/api/auth/me/"]:
        assert api.get(path).status_code == 401, path
