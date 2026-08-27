"""Authentication: login, refresh, logout, registration and role separation."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_login_returns_tokens_and_user(api, student_user):
    response = api.post(
        "/api/auth/login/",
        {"email": "student@rec.test", "password": "StudentPass!2026"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]
    assert response.data["user"]["email"] == "student@rec.test"
    assert response.data["user"]["role"] == "STUDENT"
    assert response.data["user"]["is_admin"] is False
    # The password must never be echoed back in any form.
    assert "password" not in str(response.data)


def test_login_is_case_insensitive_on_email(api, student_user):
    response = api.post(
        "/api/auth/login/",
        {"email": "Student@REC.test", "password": "StudentPass!2026"},
        format="json",
    )
    assert response.status_code == 200


def test_invalid_password_is_rejected(api, student_user):
    response = api.post(
        "/api/auth/login/",
        {"email": "student@rec.test", "password": "wrong-password"},
        format="json",
    )
    assert response.status_code == 401


def test_unknown_account_gives_the_same_error_as_a_wrong_password(api, student_user):
    unknown = api.post(
        "/api/auth/login/", {"email": "nobody@rec.test", "password": "whatever"}, format="json"
    )
    wrong = api.post(
        "/api/auth/login/", {"email": "student@rec.test", "password": "whatever"}, format="json"
    )
    # Identical responses: the endpoint must not reveal which emails exist.
    assert unknown.status_code == wrong.status_code == 401
    assert str(unknown.data.get("detail")) == str(wrong.data.get("detail"))


def test_admin_login_accepts_an_administrator(api, admin_user):
    response = api.post(
        "/api/auth/admin/login/",
        {"email": "admin@rec.test", "password": "AdminPass!2026"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["user"]["is_admin"] is True


def test_admin_login_refuses_a_student_with_correct_credentials(api, student_user):
    """The credentials are valid; the endpoint still issues no token."""
    response = api.post(
        "/api/auth/admin/login/",
        {"email": "student@rec.test", "password": "StudentPass!2026"},
        format="json",
    )
    assert response.status_code == 400
    assert "access" not in response.data


def test_token_refresh_issues_a_new_access_token(api, student_user):
    login = api.post(
        "/api/auth/login/",
        {"email": "student@rec.test", "password": "StudentPass!2026"},
        format="json",
    )
    response = api.post(
        "/api/auth/token/refresh/", {"refresh": login.data["refresh"]}, format="json"
    )
    assert response.status_code == 200
    assert response.data["access"]


def test_me_requires_authentication(api):
    assert api.get("/api/auth/me/").status_code == 401


def test_me_returns_the_signed_in_user(student_api, student_user):
    response = student_api.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.data["email"] == "student@rec.test"


def test_logout_blacklists_the_refresh_token(api, student_user):
    login = api.post(
        "/api/auth/login/",
        {"email": "student@rec.test", "password": "StudentPass!2026"},
        format="json",
    )
    refresh = login.data["refresh"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    assert api.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code == 205

    # The blacklisted token must not mint another access token.
    replay = api.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
    assert replay.status_code == 401


def test_self_registration_is_not_available(api, department):
    """There is no public path to creating an account.

    Registration was removed: the portal runs on accounts provisioned on the
    server. The endpoint must be gone rather than merely hidden in the UI, so a
    direct POST cannot create a third account.
    """
    response = api.post(
        "/api/auth/register/",
        {"name": "New Student", "email": "new.student@rec.test", "password": "GoodPass!2026"},
        format="json",
    )
    assert response.status_code == 404

    from accounts.models import User

    assert not User.objects.filter(email="new.student@rec.test").exists()


def test_no_registration_route_is_wired(db):
    from django.urls import NoReverseMatch, reverse

    import pytest as _pytest

    with _pytest.raises(NoReverseMatch):
        reverse("register")


def test_accounts_are_created_on_the_server_only(db, department):
    """`create_user` still works — provisioning simply is not a public API."""
    from accounts.models import Role, User

    user = User.objects.create_user(
        email="Provisioned@REC.test",
        password="ServerSide!2026",
        name="Provisioned Student",
        role=Role.STUDENT,
        department=department,
    )
    assert user.email == "provisioned@rec.test"
    assert user.check_password("ServerSide!2026")
    assert user.password != "ServerSide!2026"


def test_legacy_bcrypt_hash_still_authenticates(api, department):
    """An account migrated from the previous bcryptjs stack can still sign in."""
    import bcrypt

    from accounts.models import Role, User

    raw = "LegacyPass!2026"
    legacy = bcrypt.hashpw(raw.encode(), bcrypt.gensalt(rounds=12)).decode()

    user = User(email="legacy@rec.test", name="Legacy User", role=Role.STUDENT)
    user.password = f"bcrypt${legacy}"
    user.save()

    response = api.post(
        "/api/auth/login/", {"email": "legacy@rec.test", "password": raw}, format="json"
    )
    assert response.status_code == 200


def test_user_list_is_admin_only(student_api, admin_api):
    assert student_api.get("/api/auth/users/").status_code == 403
    assert admin_api.get("/api/auth/users/").status_code == 200
