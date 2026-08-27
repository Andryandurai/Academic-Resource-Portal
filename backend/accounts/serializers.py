"""Authentication and user serializers."""

from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """The signed-in user, as the SPA needs them.

    Deliberately narrow: no password field, no permission flags. Everything the
    UI uses to decide what to render is derived from `role`, which the API
    re-checks on every request anyway.
    """

    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "is_admin", "department_name", "created_at"]
        read_only_fields = fields


class LoginSerializer(TokenObtainPairSerializer):
    """Email + password in exchange for an access/refresh pair.

    Extends SimpleJWT's serializer so the response carries the user object as
    well as the tokens: without it the SPA would have to make a second `/me/`
    call before it could render anything, and the login screen would flash.
    """

    username_field = User.USERNAME_FIELD

    default_error_messages = {
        # One message for every failure mode. A distinct "no such account"
        # response would let anyone enumerate registered addresses.
        "no_active_account": "Incorrect email or password. Please check your credentials and try again."
    }

    def validate(self, attrs):
        attrs[self.username_field] = attrs.get(self.username_field, "").strip().lower()
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class AdminLoginSerializer(LoginSerializer):
    """The administrator login form.

    A student's credentials are correct but are refused here, with the same
    generic message — so this endpoint cannot be used to discover which accounts
    hold administrator rights.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_admin:
            raise serializers.ValidationError(
                {"detail": self.error_messages["no_active_account"]}, code="no_active_account"
            )
        return data


class UserListSerializer(serializers.ModelSerializer):
    """Administrator's read-only user overview."""

    upload_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "is_active", "created_at", "upload_count"]
        read_only_fields = fields
