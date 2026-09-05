"""Uploaded academic resources.

A resource is one file filed under one of eight categories of one subject.
Nothing restricts a category to a single file: `Resource` is a plain child of
`Subject`, so "Unit 1" holds as many documents as the department publishes.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.validators import file_type_label, is_inline_viewable


class ResourceType(models.TextChoices):
    UNIT_1 = "UNIT_1", "Unit 1"
    UNIT_2 = "UNIT_2", "Unit 2"
    UNIT_3 = "UNIT_3", "Unit 3"
    UNIT_4 = "UNIT_4", "Unit 4"
    UNIT_5 = "UNIT_5", "Unit 5"
    CAT_1 = "CAT_1", "CAT 1"
    CAT_2 = "CAT_2", "CAT 2"
    SEMESTER_EXAM = "SEMESTER_EXAM", "Semester Exam"


class ContentKind(models.TextChoices):
    """What a resource *is*, orthogonal to the unit it is filed under.

    `resource_type` says where a resource sits (Unit 1, CAT 2, ...); `kind` says
    what it is. Notes are a stored document; a reference or a video is a URL and
    never reaches MEDIA_ROOT, so the two are mutually exclusive by construction
    rather than by convention — see the check constraint on Resource.
    """

    NOTES = "NOTES", "Notes"
    REFERENCE = "REFERENCE", "Reference link"
    YOUTUBE = "YOUTUBE", "YouTube video"


#: Kinds stored as a URL rather than a file.
LINK_KINDS = (ContentKind.REFERENCE, ContentKind.YOUTUBE)


LEARNING_RESOURCE_TYPES = [
    ResourceType.UNIT_1,
    ResourceType.UNIT_2,
    ResourceType.UNIT_3,
    ResourceType.UNIT_4,
    ResourceType.UNIT_5,
]

EXAM_RESOURCE_TYPES = [
    ResourceType.CAT_1,
    ResourceType.CAT_2,
    ResourceType.SEMESTER_EXAM,
]


def resource_upload_path(instance: "Resource", filename: str) -> str:
    """Where the bytes are written, under MEDIA_ROOT.

    The name is a fresh UUID every time and the extension is the validated one:
    the uploader's filename never reaches the filesystem, which removes path
    traversal and collision as concerns rather than defending against them.
    Foldering by subject keeps the directory browsable for an operator.
    """
    ext = (instance.file_ext or "bin").lower()
    return f"resources/subject-{instance.subject_id}/{uuid.uuid4().hex}.{ext}"


class Resource(models.Model):
    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.CASCADE, related_name="resources"
    )
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices, db_index=True)
    kind = models.CharField(
        max_length=12, choices=ContentKind.choices, default=ContentKind.NOTES, db_index=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True, default="")

    # Set for ContentKind.NOTES only.
    file = models.FileField(upload_to=resource_upload_path, max_length=255, blank=True, default="")
    # The name as uploaded, kept for display only.
    file_name = models.CharField(max_length=200, blank=True, default="")
    file_type = models.CharField(max_length=120, blank=True, default="")
    file_ext = models.CharField(max_length=10, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)

    # Set for the link kinds only.
    url = models.URLField(max_length=500, blank=True, default="")

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_resources",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["subject", "resource_type"]),
            models.Index(fields=["subject", "resource_type", "kind"]),
            models.Index(fields=["-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(kind=ContentKind.NOTES) & ~models.Q(file="") & models.Q(url="")
                )
                | (
                    ~models.Q(kind=ContentKind.NOTES) & models.Q(file="") & ~models.Q(url="")
                ),
                name="resource_file_xor_url",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_resource_type_display()})"

    @property
    def file_type_label(self) -> str:
        return file_type_label(self.file_ext)

    @property
    def inline_viewable(self) -> bool:
        return is_inline_viewable(self.file_ext)

    @property
    def is_link(self) -> bool:
        return self.kind in LINK_KINDS

    def clean(self):
        """Mirror the check constraint with a message a human can act on.

        The constraint is the guarantee; this exists so an administrator gets
        "a link is required" instead of an IntegrityError.
        """
        super().clean()
        if self.is_link:
            if not self.url:
                raise ValidationError({"url": "A link is required for this resource kind."})
            if self.file:
                raise ValidationError({"file": "A link resource cannot also carry a file."})
        else:
            if not self.file:
                raise ValidationError({"file": "A file is required to publish notes."})
            if self.url:
                raise ValidationError({"url": "Notes carry a file, not a link."})

    def delete(self, *args, **kwargs):
        """Remove the stored file along with the row.

        Django stopped doing this automatically in 1.3 because it is unsafe
        during a bulk delete. Doing it explicitly here keeps storage in step with
        the database for the single-object deletes the API performs; the file is
        removed after the row so a failed delete never orphans the record.
        """
        stored = self.file
        super().delete(*args, **kwargs)
        if stored:
            stored.delete(save=False)
