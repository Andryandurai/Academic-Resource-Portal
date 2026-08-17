"""Authentication endpoints."""

from __future__ import annotations

from django.db.models import Count
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.permissions import IsAdminRole

from .models import Role, User
from .serializers import (
    AdminLoginSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserListSerializer,
    UserSerializer,
)


class LoginRateThrottle(AnonRateThrottle):
    """Slows credential stuffing without inconveniencing a real sign-in."""

    scope = "login"
    rate = "20/min"


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — student and administrator sign-in."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]


class AdminLoginView(LoginView):
    """POST /api/auth/admin/login/ — refuses to issue a token to a student."""

    serializer_class = AdminLoginSerializer


class RefreshView(TokenRefreshView):
    """POST /api/auth/token/refresh/"""

    permission_classes = [AllowAny]


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — creates a student account and signs them in."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    """GET /api/auth/me/ — the signed-in user.

    The SPA calls this on boot to confirm a persisted token is still valid and
    that the role in it still matches the account, so a demoted administrator
    loses the admin UI immediately rather than at token expiry.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklists the presented refresh token.

    Without this a "logged out" refresh token stays valid until it expires, so
    signing out on a shared machine would not actually end the session.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = (request.data or {}).get("refresh")
        if not token:
            return Response(
                {"detail": "A refresh token is required to log out."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            # Already expired or already blacklisted. The client's intent is
            # satisfied either way, so this is not an error worth surfacing.
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class UserListView(generics.ListAPIView):
    """GET /api/auth/users/ — administrator's read-only user overview."""

    serializer_class = UserListSerializer
    permission_classes = [IsAdminRole]
    pagination_class = None
    filterset_fields = ["role"]

    def get_queryset(self):
        return User.objects.annotate(upload_count=Count("uploaded_resources")).order_by(
            "role", "-created_at"
        )


class UserStatsView(APIView):
    """GET /api/auth/users/stats/ — counts for the admin dashboard."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(
            {
                "students": User.objects.filter(role=Role.STUDENT).count(),
                "admins": User.objects.filter(role=Role.ADMIN).count(),
                "total": User.objects.count(),
            }
        )
