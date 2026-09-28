"""Resources: upload validation, the read/write split, download and deletion."""

from __future__ import annotations

import pytest

from conftest import make_pdf, pdf_upload, upload
from resources.models import Resource

pytestmark = pytest.mark.django_db


def create_resource(
    admin_api, subject, *, resource_type="UNIT_1", title="Unit 1 Notes", name="unit1.pdf", expect=201
):
    """Upload a resource as the administrator.

    Asserts the expected status by default: a helper that silently swallowed a
    400 would let a later "count is zero" assertion fail for an unrelated reason,
    which is exactly how this suite once misreported a working endpoint.
    """
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": subject.id,
            "resource_type": resource_type,
            "title": title,
            "description": "",
            "file": pdf_upload(name),
        },
        format="multipart",
    )
    if expect is not None:
        assert response.status_code == expect, response.data
    return response


# --------------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------------- #
def test_admin_can_upload_a_pdf(admin_api, data_structures):
    response = create_resource(admin_api, data_structures)
    assert response.status_code == 201
    assert response.data["file_ext"] == "pdf"
    assert response.data["file_type"] == "application/pdf"
    assert response.data["file_size"] > 0
    assert response.data["inline_viewable"] is True
    # The stored path is never disclosed to a client.
    assert "file" not in response.data


def test_a_category_holds_multiple_resources(admin_api, data_structures):
    for index in range(3):
        assert (
            create_resource(
                admin_api,
                data_structures,
                title=f"Unit 1 Document {index}",
                name=f"unit1-{index}.pdf",
            ).status_code
            == 201
        )
    assert Resource.objects.filter(subject=data_structures, resource_type="UNIT_1").count() == 3


@pytest.mark.parametrize(
    "resource_type",
    ["UNIT_1", "UNIT_2", "UNIT_3", "UNIT_4", "UNIT_5", "CAT_1", "CAT_2", "SEMESTER_EXAM"],
)
def test_every_resource_category_accepts_an_upload(admin_api, data_structures, resource_type):
    response = create_resource(
        admin_api, data_structures, resource_type=resource_type, title=f"{resource_type} material"
    )
    assert response.status_code == 201
    assert response.data["resource_type"] == resource_type


def test_stored_filename_is_server_generated(admin_api, data_structures):
    create_resource(admin_api, data_structures, name="../../etc/passwd.pdf")
    resource = Resource.objects.get()
    # The uploader's name is kept for display only; the path is a fresh UUID.
    assert ".." not in resource.file.name
    assert "passwd" not in resource.file.name
    assert resource.file.name.startswith(f"resources/subject-{data_structures.id}/")


def test_missing_file_is_rejected_on_create(admin_api, data_structures):
    response = admin_api.post(
        "/api/resources/",
        {"subject": data_structures.id, "resource_type": "UNIT_1", "title": "No file"},
        format="multipart",
    )
    assert response.status_code == 400
    assert "file" in response.data


def test_executable_upload_is_rejected(admin_api, data_structures):
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": data_structures.id,
            "resource_type": "UNIT_1",
            "title": "Payload",
            "file": upload("payload.exe", b"MZ\x90\x00 fake", "application/x-msdownload"),
        },
        format="multipart",
    )
    assert response.status_code == 400
    assert Resource.objects.count() == 0


def test_renamed_executable_is_caught_by_the_signature_check(admin_api, data_structures):
    """Extension and content type both claim PDF; the bytes do not."""
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": data_structures.id,
            "resource_type": "UNIT_1",
            "title": "Disguised",
            "file": upload("notes.pdf", b"MZ\x90\x00 this is not a pdf", "application/pdf"),
        },
        format="multipart",
    )
    assert response.status_code == 400
    assert "valid PDF" in str(response.data)
    assert Resource.objects.count() == 0


def test_oversized_upload_is_rejected(admin_api, data_structures, settings):
    settings.MAX_UPLOAD_BYTES = 512
    settings.MAX_UPLOAD_MB = 512 / (1024 * 1024)
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": data_structures.id,
            "resource_type": "UNIT_1",
            "title": "Large",
            "file": upload("big.pdf", make_pdf("x" * 4096), "application/pdf"),
        },
        format="multipart",
    )
    assert response.status_code == 400
    assert "too large" in str(response.data).lower()


def test_contradicting_content_type_is_rejected(admin_api, data_structures):
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": data_structures.id,
            "resource_type": "UNIT_1",
            "title": "Wrong type",
            "file": upload("notes.pdf", make_pdf(), "text/html"),
        },
        format="multipart",
    )
    assert response.status_code == 400


def test_invalid_resource_type_is_rejected(admin_api, data_structures):
    response = admin_api.post(
        "/api/resources/",
        {
            "subject": data_structures.id,
            "resource_type": "UNIT_9",
            "title": "Nope",
            "file": pdf_upload(),
        },
        format="multipart",
    )
    assert response.status_code == 400
    assert "resource_type" in response.data


# --------------------------------------------------------------------------- #
# Permissions
# --------------------------------------------------------------------------- #
def test_student_cannot_upload(student_api, data_structures):
    response = student_api.post(
        "/api/resources/",
        {
            "subject": data_structures.id,
            "resource_type": "UNIT_1",
            "title": "Forged",
            "file": pdf_upload(),
        },
        format="multipart",
    )
    assert response.status_code == 403
    assert Resource.objects.count() == 0


def test_student_cannot_edit_replace_or_delete(admin_api, student_api, data_structures):
    resource_id = create_resource(admin_api, data_structures).data["id"]

    assert (
        student_api.patch(
            f"/api/resources/{resource_id}/", {"title": "Hijacked"}, format="multipart"
        ).status_code
        == 403
    )
    assert (
        student_api.put(
            f"/api/resources/{resource_id}/",
            {
                "subject": data_structures.id,
                "resource_type": "UNIT_1",
                "title": "Hijacked",
                "file": pdf_upload("replacement.pdf"),
            },
            format="multipart",
        ).status_code
        == 403
    )
    assert student_api.delete(f"/api/resources/{resource_id}/").status_code == 403

    resource = Resource.objects.get(id=resource_id)
    assert resource.title == "Unit 1 Notes"


def test_anonymous_can_read_but_never_write(api, admin_api, data_structures):
    resource_id = create_resource(admin_api, data_structures).data["id"]
    # `api` carries no Authorization header: it is a separate, unauthenticated
    # client rather than a de-authenticated copy of the admin one.
    assert api.get("/api/resources/").status_code == 200
    assert api.get(f"/api/resources/{resource_id}/").status_code == 200
    assert api.get(f"/api/resources/{resource_id}/download/").status_code == 200

    # Publishing, editing and deleting stay faculty-only.
    assert api.post("/api/resources/", {"title": "Forged"}, format="multipart").status_code == 401
    assert api.patch(f"/api/resources/{resource_id}/", {"title": "x"}, format="multipart").status_code == 401
    assert api.delete(f"/api/resources/{resource_id}/").status_code == 401


# --------------------------------------------------------------------------- #
# Reading and downloading
# --------------------------------------------------------------------------- #
def test_student_sees_published_resources(admin_api, student_api, data_structures):
    create_resource(admin_api, data_structures)
    response = student_api.get("/api/resources/", {"subject": data_structures.id})
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_filter_by_subject_and_category(admin_api, student_api, data_structures):
    create_resource(admin_api, data_structures, resource_type="UNIT_1", title="Unit 1 notes")
    create_resource(admin_api, data_structures, resource_type="CAT_1", title="CAT 1 paper")

    response = student_api.get(
        "/api/resources/", {"subject": data_structures.id, "resource_type": "CAT_1"}
    )
    assert response.data["count"] == 1
    assert response.data["results"][0]["title"] == "CAT 1 paper"


def test_student_can_download_the_bytes(admin_api, student_api, data_structures):
    resource_id = create_resource(admin_api, data_structures).data["id"]
    response = student_api.get(f"/api/resources/{resource_id}/download/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"].startswith("attachment")
    assert response["X-Content-Type-Options"] == "nosniff"
    assert b"".join(response.streaming_content).startswith(b"%PDF-")


def test_inline_view_is_offered_for_pdfs(admin_api, student_api, data_structures):
    resource_id = create_resource(admin_api, data_structures).data["id"]
    response = student_api.get(f"/api/resources/{resource_id}/download/", {"inline": "1"})
    assert response["Content-Disposition"].startswith("inline")


def test_resource_counts_reflect_uploads(admin_api, student_api, data_structures):
    create_resource(admin_api, data_structures, resource_type="UNIT_1", title="Unit 1 part A")
    create_resource(admin_api, data_structures, resource_type="UNIT_1", title="Unit 1 part B")
    create_resource(admin_api, data_structures, resource_type="CAT_1", title="CAT 1 paper")

    counts = student_api.get(f"/api/subjects/{data_structures.id}/resource-counts/").data
    assert counts["UNIT_1"] == 2
    assert counts["CAT_1"] == 1
    assert counts["UNIT_3"] == 0

    stats = student_api.get("/api/stats/").data
    assert stats["resources"] == 3
    assert stats["exam_resources"] == 1


# --------------------------------------------------------------------------- #
# Editing, replacing and deleting
# --------------------------------------------------------------------------- #
def test_admin_can_edit_metadata_without_touching_the_file(admin_api, data_structures):
    resource_id = create_resource(admin_api, data_structures).data["id"]
    stored_before = Resource.objects.get(id=resource_id).file.name

    response = admin_api.patch(
        f"/api/resources/{resource_id}/",
        {"title": "Unit 1 Notes (Revised)", "description": "Second edition."},
        format="multipart",
    )
    assert response.status_code == 200
    assert response.data["title"] == "Unit 1 Notes (Revised)"
    assert Resource.objects.get(id=resource_id).file.name == stored_before


def test_admin_can_replace_the_file(admin_api, student_api, data_structures):
    resource_id = create_resource(admin_api, data_structures).data["id"]
    original_path = Resource.objects.get(id=resource_id).file.path

    response = admin_api.patch(
        f"/api/resources/{resource_id}/",
        {"file": upload("v2.pdf", make_pdf("VERSION TWO"), "application/pdf")},
        format="multipart",
    )
    assert response.status_code == 200

    downloaded = b"".join(
        student_api.get(f"/api/resources/{resource_id}/download/").streaming_content
    )
    assert b"VERSION TWO" in downloaded

    # The superseded file is removed, not left behind as an orphan.
    import os

    assert not os.path.exists(original_path)


def test_admin_can_delete_a_resource_and_its_file(admin_api, student_api, data_structures):
    resource_id = create_resource(admin_api, data_structures).data["id"]
    path = Resource.objects.get(id=resource_id).file.path

    assert admin_api.delete(f"/api/resources/{resource_id}/").status_code == 204
    assert not Resource.objects.filter(id=resource_id).exists()

    import os

    assert not os.path.exists(path)
    assert student_api.get(f"/api/resources/{resource_id}/download/").status_code == 404


def test_deleting_a_resource_leaves_its_siblings_alone(admin_api, data_structures):
    first = create_resource(admin_api, data_structures, title="Keep me", name="a.pdf").data["id"]
    second = create_resource(admin_api, data_structures, title="Delete me", name="b.pdf").data["id"]

    admin_api.delete(f"/api/resources/{second}/")
    assert Resource.objects.filter(id=first).exists()
    assert Resource.objects.count() == 1


def test_subject_holding_resources_cannot_be_deleted(admin_api, data_structures):
    create_resource(admin_api, data_structures)
    response = admin_api.delete(f"/api/subjects/{data_structures.id}/")
    assert response.status_code == 409
    assert "resource" in str(response.data).lower()

    from academics.models import Subject

    assert Subject.objects.filter(id=data_structures.id).exists()


def test_recent_endpoint_lists_latest_uploads(admin_api, student_api, data_structures):
    create_resource(admin_api, data_structures, title="Older", name="a.pdf")
    create_resource(admin_api, data_structures, title="Newer", name="b.pdf")

    response = student_api.get("/api/resources/recent/", {"limit": 5})
    assert response.status_code == 200
    assert response.data[0]["title"] == "Newer"

