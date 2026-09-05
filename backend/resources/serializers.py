"""Resource serializers.

Uploads are validated here — extension, declared media type, file signature and
size — before anything is written to disk.
"""

from __future__ import annotations

from urllib.parse import urlparse

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.validators import sanitize_display_name, validate_upload

from .models import ContentKind, LINK_KINDS, Resource, ResourceType


def _is_youtube(url: str) -> bool:
    """Accept the host forms YouTube actually issues, and nothing else."""
    host = urlparse(url).netloc.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    return host in {"youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


class ResourceSerializer(serializers.ModelSerializer):
    """Read shape.

    Note there is no `file` URL: the stored file is not publicly addressable.
    Clients fetch bytes from `/api/resources/<id>/download/`, which requires a
    valid token.
    """

    subject_code = serializers.CharField(source="subject.course_code", read_only=True)
    subject_title = serializers.CharField(source="subject.course_title", read_only=True)
    semester_id = serializers.IntegerField(source="subject.semester_id", read_only=True)
    semester_number = serializers.IntegerField(
        source="subject.semester.semester_number", read_only=True
    )
    resource_type_label = serializers.CharField(source="get_resource_type_display", read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    is_link = serializers.BooleanField(read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.name", read_only=True, default=None)
    file_type_label = serializers.CharField(read_only=True)
    inline_viewable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Resource
        fields = [
            "id",
            "subject",
            "subject_code",
            "subject_title",
            "semester_id",
            "semester_number",
            "resource_type",
            "resource_type_label",
            "kind",
            "kind_label",
            "is_link",
            "url",
            "title",
            "description",
            "file_name",
            "file_type",
            "file_type_label",
            "file_ext",
            "file_size",
            "inline_viewable",
            "uploaded_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ResourceWriteSerializer(serializers.ModelSerializer):
    """Create and update.

    `file` is required on create and optional on update: submitting the form
    without one edits the metadata and leaves the stored document alone, which is
    what "edit" means to an administrator fixing a typo in a title.
    """

    resource_type = serializers.ChoiceField(choices=ResourceType.choices)
    kind = serializers.ChoiceField(choices=ContentKind.choices, default=ContentKind.NOTES)
    file = serializers.FileField(required=False, write_only=True)
    url = serializers.URLField(required=False, allow_blank=True, max_length=500)

    class Meta:
        model = Resource
        fields = ["id", "subject", "resource_type", "kind", "title", "description", "file", "url"]

    def validate_title(self, value: str) -> str:
        value = (value or "").strip()
        if len(value) < 2:
            raise serializers.ValidationError("A resource title is required.")
        return value

    def validate_description(self, value: str) -> str:
        return (value or "").strip()

    def validate_file(self, upload):
        try:
            ext, media_type = validate_upload(upload)
        except DjangoValidationError as exc:
            # Django's ValidationError carries a list; DRF wants the message.
            raise serializers.ValidationError(exc.messages[0]) from exc
        # Stashed for create/update so the checks run exactly once per request.
        self._validated_ext = ext
        self._validated_media_type = media_type
        return upload

    def validate(self, attrs):
        # `kind` decides which of the two payloads is legal, so resolve it
        # first — on update it may be absent and inherited from the row.
        kind = attrs.get("kind") or (self.instance.kind if self.instance else ContentKind.NOTES)
        is_link = kind in LINK_KINDS
        url = (attrs.get("url") or "").strip()
        has_file = attrs.get("file") is not None

        if is_link:
            if has_file:
                raise serializers.ValidationError(
                    {"file": "A reference or video is a link, not a file."}
                )
            if not url and (self.instance is None or not self.instance.url):
                raise serializers.ValidationError({"url": "A link is required for this kind."})
            if kind == ContentKind.YOUTUBE and url and not _is_youtube(url):
                raise serializers.ValidationError(
                    {"url": "That is not a YouTube link. Use a youtube.com or youtu.be URL."}
                )
            attrs["url"] = url or (self.instance.url if self.instance else "")
        else:
            if url:
                raise serializers.ValidationError({"url": "Notes carry a file, not a link."})
            if self.instance is None and not has_file:
                raise serializers.ValidationError(
                    {"file": "A file is required to publish notes."}
                )
            attrs["url"] = ""
        return attrs

    def _file_fields(self, upload) -> dict:
        return {
            "file_name": sanitize_display_name(upload.name),
            "file_ext": self._validated_ext,
            "file_type": self._validated_media_type,
            "file_size": upload.size,
        }

    def create(self, validated_data):
        upload = validated_data.get("file")
        if upload is not None:
            validated_data.update(self._file_fields(upload))
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        upload = validated_data.get("file")
        previous = instance.file if upload else None

        if upload:
            validated_data.update(self._file_fields(upload))

        instance = super().update(instance, validated_data)

        # The replaced file is removed only after the row points at the new one,
        # so a failure mid-update never leaves a record referencing nothing.
        if previous and previous.name != (instance.file.name if instance.file else ""):
            previous.delete(save=False)
        return instance

    def to_representation(self, instance):
        return ResourceSerializer(instance, context=self.context).data
