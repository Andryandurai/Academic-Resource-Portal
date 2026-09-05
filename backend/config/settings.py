"""Django settings for the REC AI&DS Academic Resource Portal.

SQLite by default so the portal runs with zero infrastructure; point
``REC_DATABASE_URL`` (or a provider-supplied ``DATABASE_URL``) at PostgreSQL for
deployment without a code change.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

# Loads backend/.env into the process environment if one exists (never
# overwriting a variable the shell already set). Optional: a managed host sets
# these directly and ships no .env file at all.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(BASE_DIR / ".env")

# Hosting platforms export a marker into every build and running service. Using
# it to pick the *default* means a deployment cannot accidentally ship a debug
# build because someone forgot an environment variable, while local development
# keeps its zero-configuration default of DEBUG on. An explicit REC_DEBUG still
# wins in both directions.
IS_MANAGED_HOST = bool(os.environ.get("RENDER") or os.environ.get("DYNO"))
DEBUG = os.environ.get("REC_DEBUG", "0" if IS_MANAGED_HOST else "1") == "1"

DEV_SECRET_KEY = "dev-only-insecure-key-change-me-in-production"
SECRET_KEY = os.environ.get("REC_SECRET_KEY", DEV_SECRET_KEY)
if not DEBUG and SECRET_KEY == DEV_SECRET_KEY:
    # Refusing to boot is the right failure here rather than a warning nobody
    # reads: SimpleJWT signs access tokens with SECRET_KEY, so a deployment
    # running on the published development key lets anyone mint an administrator
    # token and publish or delete departmental material.
    raise ImproperlyConfigured(
        "REC_SECRET_KEY must be set to a unique secret when DEBUG is off. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("REC_ALLOWED_HOSTS", "*" if DEBUG else "").split(",") if h.strip()
]
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOSTNAME and RENDER_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "accounts",
    "academics",
    "resources",
    "whatsapp",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Directly after SecurityMiddleware, as WhiteNoise requires: it answers
    # requests for the built SPA and for Django's collected static files without
    # waking the rest of the stack.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------------------------------- #
# Transport security
# --------------------------------------------------------------------------- #
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Overridable so production settings can be exercised locally over plain HTTP
# (REC_DEBUG=0 REC_SSL_REDIRECT=0) without every request bouncing to an https
# URL that nothing is listening on.
SECURE_SSL_REDIRECT = os.environ.get("REC_SSL_REDIRECT", "0" if DEBUG else "1") == "1"
SECURE_REDIRECT_EXEMPT = [r"^api/health/?$"]
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
# No `preload`: that directive asks for inclusion in the browsers' hardcoded
# preload list, which is irreversible and not ours to request for a hostname
# under the institution's domain.
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# `manage.py check --deploy` raises this and it is deliberate. Silenced rather
# than tolerated so the command stays a clean pass and a *new* warning is visible
# the moment it appears.
SILENCED_SYSTEM_CHECKS = [
    # W003: no CsrfViewMiddleware. Authentication is a bearer token read from the
    # Authorization header — there are no sessions and no auth cookies, so a
    # cross-site request carries no ambient credential to abuse.
    "security.W003",
    # W021: SECURE_HSTS_PRELOAD is off on purpose. See the comment above it.
    "security.W021",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

# --------------------------------------------------------------------------- #
# Database — SQLite for development, PostgreSQL for production
# --------------------------------------------------------------------------- #
# Managed Postgres providers inject a plain `DATABASE_URL`. Reading it as a
# fallback means attaching a database is a one-click operation with no
# environment variable to copy across by hand.
DATABASE_URL = os.environ.get("REC_DATABASE_URL") or os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres"):
    # postgresql://user:pass@host:port/name[?sslmode=require]
    from urllib.parse import parse_qs, unquote, urlparse

    parsed = urlparse(DATABASE_URL)
    options: dict[str, str] = {}
    # Honouring whatever the URL says keeps one code path for providers that
    # mandate TLS and those that do not.
    sslmode = parse_qs(parsed.query).get("sslmode", [None])[0]
    if sslmode:
        options["sslmode"] = sslmode

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": (parsed.path or "/rec_aids").lstrip("/"),
            # Credentials are percent-encoded in a URL; a password containing
            # `@` or `/` arrives mangled unless it is decoded back.
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "localhost",
            "PORT": str(parsed.port or 5432),
            "CONN_MAX_AGE": 60,
            "OPTIONS": options,
        }
    }
else:
    if DATABASE_URL.startswith("sqlite"):
        raw = DATABASE_URL.split("://", 1)[-1].lstrip("/") or "rec_aids.sqlite3"
        sqlite_path = Path(raw) if Path(raw).is_absolute() else BASE_DIR / raw
    else:
        sqlite_path = BASE_DIR / "rec_aids.sqlite3"

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
            "OPTIONS": {
                # WAL keeps concurrent reads from blocking the writer, so the
                # development database behaves like the production Postgres.
                "init_command": "PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;",
                "transaction_mode": "IMMEDIATE",
            },
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

# PBKDF2 is Django's default and what every new password is hashed with. The
# bcrypt hashers follow it only so accounts carried over from the previous
# bcryptjs-based stack can still sign in; Django transparently upgrades such a
# hash to PBKDF2 on the owner's next successful login.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "accounts.hashers.LegacyBCryptPasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
# Static files and the built SPA
# --------------------------------------------------------------------------- #
# The API and the single-page app are served from one origin by one process.
# That removes cross-origin requests from the deployment entirely: no CORS
# allow-list to maintain, no second service URL baked in at build time, and no
# preflight round-trip on every API call.
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploaded resource files live on local disk by default. A free host's disk is
# usually ephemeral (Render's free tier wipes it on every restart/redeploy), so
# setting REC_S3_ACCESS_KEY_ID switches to any S3-compatible bucket instead —
# Supabase Storage, Cloudflare R2, or AWS S3 itself all work unchanged, since
# they all speak the same S3 API django-storages targets.
REC_S3_ACCESS_KEY_ID = os.environ.get("REC_S3_ACCESS_KEY_ID", "")
if REC_S3_ACCESS_KEY_ID:
    INSTALLED_APPS.append("storages")
    AWS_ACCESS_KEY_ID = REC_S3_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = os.environ.get("REC_S3_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("REC_S3_BUCKET_NAME", "resources")
    AWS_S3_ENDPOINT_URL = os.environ.get("REC_S3_ENDPOINT_URL", "")
    AWS_S3_REGION_NAME = os.environ.get("REC_S3_REGION_NAME", "us-east-1")
    # Path style ("endpoint/bucket/key") rather than virtual-hosted style
    # ("bucket.endpoint/key") — the form third-party S3-compatible providers
    # expect; AWS itself accepts both.
    AWS_S3_ADDRESSING_STYLE = "path"
    # The bucket is private (see whatsapp/README.md and resources/views.py):
    # every file is read server-side and streamed through the authenticated
    # download endpoint, so no object ever needs a public ACL or a signed URL.
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    _default_storage_backend = "storages.backends.s3.S3Storage"
else:
    _default_storage_backend = "django.core.files.storage.FileSystemStorage"

STORAGES = {
    "default": {"BACKEND": _default_storage_backend},
    "staticfiles": {
        # Hashed filenames let assets be cached forever, but the manifest they
        # rely on only exists after collectstatic. Requiring that in development
        # would break `python manage.py runserver` for anyone who has not run it.
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# Serve the Vite build at the site root so `/assets/index-*.js` — the absolute
# paths Vite writes into index.html — resolve without rewriting the bundle.
# Guarded on existence because a checkout that has not run `npm run build` yet is
# a normal state, and WhiteNoise raises on a missing root.
if FRONTEND_DIST.is_dir():
    WHITENOISE_ROOT = str(FRONTEND_DIST)
WHITENOISE_INDEX_FILE = True
# Vite fingerprints every asset it emits, so a long max-age is safe: a changed
# file is a changed URL. index.html is served by config.spa, which sets its own
# no-cache headers.
WHITENOISE_MAX_AGE = 0 if DEBUG else 31536000

# --------------------------------------------------------------------------- #
# Media — uploaded academic resources
# --------------------------------------------------------------------------- #
# Deliberately NOT under STATIC_ROOT and never inside frontend/. Resource files
# are readable only through the authenticated download endpoint in
# resources/views.py, so there is no public URL to guess. MEDIA_URL is set for
# Django's internal machinery only; no URL pattern serves MEDIA_ROOT.
MEDIA_ROOT = Path(os.environ.get("REC_MEDIA_ROOT") or (BASE_DIR / "media"))
MEDIA_URL = "/media/"

# Maximum accepted upload size, in megabytes.
MAX_UPLOAD_MB = float(os.environ.get("REC_MAX_UPLOAD_MB", "25"))
MAX_UPLOAD_BYTES = int(MAX_UPLOAD_MB * 1024 * 1024)
# Anything larger than this is streamed to a temporary file instead of being
# held in memory. Kept below MAX_UPLOAD_BYTES so a large upload cannot pin a
# worker's memory while it is being validated.
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_BYTES + (1024 * 1024)

# Optional domain restriction for student self-registration.
ALLOWED_STUDENT_EMAIL_DOMAIN = (
    os.environ.get("REC_ALLOWED_STUDENT_EMAIL_DOMAIN", "").strip().lstrip("@").lower() or None
)

# --------------------------------------------------------------------------- #
# REST framework
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Authenticated by default: an endpoint has to opt *out* of authentication,
    # so a new view cannot be accidentally public.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.DefaultPagination",
    "PAGE_SIZE": 50,
    "UNAUTHENTICATED_USER": None,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("REC_ACCESS_TOKEN_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("REC_REFRESH_TOKEN_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Token blacklisting backs the logout endpoint: without it a "logged out" refresh
# token stays valid until it expires.
INSTALLED_APPS.append("rest_framework_simplejwt.token_blacklist")

# --------------------------------------------------------------------------- #
# CORS — the SPA is served separately in development
# --------------------------------------------------------------------------- #
# In production the SPA is same-origin (see the static files section above), so
# nothing here is exercised. It stays for the Vite dev server, and for a
# deployment that chooses to host the frontend elsewhere — set REC_CORS_ORIGINS
# to a comma-separated list of full origins for that.
#
# The localhost regex is applied only in DEBUG: leaving it on in production would
# let any page served from a developer's machine call the deployed API with a
# stolen token.
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://(localhost|127\.0\.0\.1):\d+$"] if DEBUG else []
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("REC_CORS_ORIGINS", "").split(",") if o.strip()
]
# Authentication is a bearer token, not a cookie, so credentialed cross-origin
# requests are never needed.
CORS_ALLOW_CREDENTIALS = False
# Content-Disposition is not a CORS-safelisted response header, so without this
# the SPA's fetch-based downloader cannot read the server's filename and every
# download would fall back to a generic name.
CORS_EXPOSE_HEADERS = ["Content-Disposition"]

APP_NAME = "REC AI&DS Academic Resource Portal"
API_VERSION = "1.0.0"
COLLEGE_NAME = "Rajalakshmi Engineering College"
# Canonical name — must match academics/departments.py, or `seed_academics`
# would rename the department back on every run.
DEPARTMENT_NAME = "Artificial Intelligence and Data Science"
DEPARTMENT_CODE = "AI&DS"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}
    },
}

# --------------------------------------------------------------------------- #
# WhatsApp bot (Meta Cloud API)
# --------------------------------------------------------------------------- #
# Every credential is optional at import time so the rest of the site (and the
# test suite) never needs them; the webhook view raises ImproperlyConfigured on
# first real use if one is missing. See whatsapp/README.md for how to obtain
# each value from the free Meta developer console.
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
# Validates X-Hub-Signature-256 on every inbound webhook so a forged POST to a
# guessed URL cannot pretend to be Meta. Required to run for real; the test
# suite exercises the webhook with signing disabled explicitly.
WHATSAPP_APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")
# Explicit, off-by-default escape hatch for a real local test session that
# cannot yet retrieve its App secret from Meta. Never set this outside a
# throwaway local .env — see meta_client.verify_signature.
WHATSAPP_INSECURE_SKIP_SIGNATURE = os.environ.get("WHATSAPP_INSECURE_SKIP_SIGNATURE", "0") == "1"
WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v21.0")
WHATSAPP_GRAPH_BASE = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"
# Logs outgoing messages instead of calling Meta. On by DEBUG default so a
# developer with no WhatsApp credentials yet can still drive the whole
# conversation through the /api/whatsapp/dev-send/ helper endpoint.
WHATSAPP_DRY_RUN = os.environ.get("WHATSAPP_DRY_RUN", "1" if DEBUG else "0") == "1"

# Free-tier LLM used only to turn a loose sentence ("unit 1 data structure
# notes") into {subject, unit, kind}. Groq's OpenAI-compatible endpoint needs no
# extra SDK. When GROQ_API_KEY is unset the bot falls back to a regex-based
# extractor automatically — see whatsapp/services/nlp.py.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_BASE = "https://api.groq.com/openai/v1"
