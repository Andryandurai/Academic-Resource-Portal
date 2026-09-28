"""Role-based permissions.

Authorisation is decided here and nowhere else, so a new endpoint cannot
accidentally invent its own rule. Hiding a control in the React app is never the
mechanism that protects a mutation — these classes are.
"""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """Only an authenticated user whose role is ADMIN."""

    message = "Administrator privileges are required for this action."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)


class IsAdminOrReadOnly(BasePermission):
    """Anyone may read; only an administrator (faculty) may write.

    This is the rule behind the whole portal: the catalogue and published
    material are open to every student with no sign-in, while creating, editing
    or deleting either takes a faculty login.
    """

    message = "Faculty sign-in is required for this action."

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)
