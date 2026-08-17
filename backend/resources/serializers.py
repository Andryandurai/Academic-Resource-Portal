"""Resource serializers.

Uploads are validated here — extension, declared media type, file signature and
size — before anything is written to disk.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.validators import sanitize_display_name, validate_upload

from .models import Resource, ResourceType


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
    file = serializers.FileField(required=False, write_only=True)

    class Meta:
        model = Resource
        fields = ["id", "subject", "resource_type", "title", "description", "file"]

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
        if self.instance is None and "file" not in attrs:
            raise serializers.ValidationError({"file": "A file is required to publish a resource."})
        return attrs

    def _file_fields(self, upload) -> dict:
        return {
            "file_name": sanitize_display_name(upload.name),
            "file_ext": self._validated_ext,
            "file_type": self._validated_media_type,
            "file_size": upload.size,
        }

    def create(self, validated_data):
        upload = validated_data["file"]
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
        if previous and previous.name != instance.file.name:
            previous.delete(save=False)
        return instance

    def to_representation(self, instance):
        return ResourceSerializer(instance, context=self.context).data
