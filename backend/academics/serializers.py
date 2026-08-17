"""Academic catalogue serializers.

Every rule that protects the curriculum lives here rather than in the React
forms: the frontend validates for the operator's convenience, this validates for
correctness.
"""

from __future__ import annotations

import re

from rest_framework import serializers

from .models import CourseCategory, CourseType, Department, Semester, Subject

# Real syllabi carry codes like "HS23221 / HS23222" for a paired course, so the
# separator and spaces are permitted alongside the usual alphanumerics.
COURSE_CODE_RE = re.compile(r"^[A-Za-z0-9 /-]{2,20}$")


class DepartmentSerializer(serializers.ModelSerializer):
    """A department as the selection page needs it.

    `has_curriculum` lets the UI tell a department that is ready from one that
    is still awaiting its syllabus without a second request per card — and
    without the frontend guessing from a zero count.
    """

    has_curriculum = serializers.BooleanField(read_only=True)
    semester_count = serializers.IntegerField(read_only=True, default=0)
    subject_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "is_active",
            "has_curriculum",
            "semester_count",
            "subject_count",
        ]
        read_only_fields = fields


class SemesterSerializer(serializers.ModelSerializer):
    subject_count = serializers.IntegerField(read_only=True)
    department_code = serializers.CharField(source="department.code", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Semester
        fields = [
            "id",
            "semester_number",
            "name",
            "subject_count",
            "department",
            "department_code",
            "department_name",
        ]
        read_only_fields = fields


class SubjectSerializer(serializers.ModelSerializer):
    """Read and write shape for a subject.

    `course_code` accepts null and empty string, both stored as NULL — the
    syllabus publishes no code for electives and one must never be invented to
    fill the column.
    """

    semester_number = serializers.IntegerField(source="semester.semester_number", read_only=True)
    semester_name = serializers.CharField(source="semester.name", read_only=True)
    # Surfaced so a client can assert the subject it rendered belongs to the
    # department it thinks it is showing, rather than inferring it.
    department = serializers.IntegerField(source="semester.department_id", read_only=True)
    department_code = serializers.CharField(source="semester.department.code", read_only=True)
    resource_count = serializers.IntegerField(read_only=True, default=0)
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    course_type_label = serializers.CharField(source="get_course_type_display", read_only=True)

    class Meta:
        model = Subject
        fields = [
            "id",
            "semester",
            "semester_number",
            "semester_name",
            "department",
            "department_code",
            "course_code",
            "course_title",
            "category",
            "category_label",
            "course_type",
            "course_type_label",
            "l",
            "t",
            "p",
            "credits",
            "resource_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_course_code(self, value):
        if value is None:
            return None
        value = value.strip().upper()
        if not value:
            return None
        if not COURSE_CODE_RE.match(value):
            raise serializers.ValidationError(
                "A course code may contain only letters, numbers and hyphens (2-20 characters)."
            )
        # Scoped to the semester, matching the database constraint. Course codes
        # legitimately repeat across departments — the same HS23111 runs in
        # AI&DS, AI&ML and EEE — so a global check would reject valid data.
        semester = self.initial_data.get("semester") or getattr(
            self.instance, "semester_id", None
        )
        existing = Subject.objects.filter(course_code=value, semester_id=semester)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError(
                "A subject with this course code already exists in this semester."
            )
        return value

    def validate_course_title(self, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("A course title is required.")
        return value

    def validate(self, attrs):
        # A course filed as pure theory must not carry practical periods — that
        # is a lab-oriented theory course (L>0, P>0) or a standalone laboratory
        # (L=0, P>0), and mislabelling it hides it from the wrong filter.
        course_type = attrs.get("course_type", getattr(self.instance, "course_type", None))
        practical = attrs.get("p", getattr(self.instance, "p", 0))
        if course_type == CourseType.THEORY and practical:
            raise serializers.ValidationError(
                {
                    "p": "A theory course has no practical periods. "
                    "Set the course type to Lab-Oriented Theory instead."
                }
            )
        return attrs


class SubjectWriteSerializer(SubjectSerializer):
    """Explicit choice fields so an invalid value is a 400, never a stored row."""

    category = serializers.ChoiceField(choices=CourseCategory.choices)
    course_type = serializers.ChoiceField(choices=CourseType.choices)
    course_code = serializers.CharField(
        max_length=20, required=False, allow_null=True, allow_blank=True
    )
