"""Authentication routes, mounted at /api/auth/."""

from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("admin/login/", views.AdminLoginView.as_view(), name="admin-login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("token/refresh/", views.RefreshView.as_view(), name="token-refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/stats/", views.UserStatsView.as_view(), name="user-stats"),
]
