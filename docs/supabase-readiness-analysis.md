# Supabase Readiness Analysis

**Scope:** make the existing REC-Academic project technically ready to connect
to Supabase PostgreSQL (and, later, Supabase Storage) without rebuilding,
redesigning, or changing any existing behaviour. This document is the record
of what was inspected, what already works, what changed, and what deliberately
did not.

---

## 1. Current architecture

| Layer | Technology | Notes |
| --- | --- | --- |
| Frontend | React 19 + TypeScript, Vite 6 | Built as a static SPA (`frontend/dist`) |
| Routing | React Router 7 | Client-side |
| State | Zustand 5 | Session + UI only, persisted to `localStorage` |
| Backend | Django 5.2 | Monolith serving both the API and the built SPA |
| API | Django REST Framework 3.15 | `ViewSet` + `DefaultRouter` per app |
| Auth | SimpleJWT (access/refresh bearer tokens) | Custom `accounts.User` model, **not** Django sessions, **not** Supabase Auth |
| DB (dev) | SQLite | `backend/rec_aids.sqlite3` |
| DB (prod) | PostgreSQL | Already wired via `REC_DATABASE_URL` / `DATABASE_URL` — see §2 |
| File storage | Local disk (`MEDIA_ROOT`) by default | S3-compatible backend (django-storages) already available behind `REC_S3_*` env vars — unused today |
| Deployment | Docker → Render (see `Dockerfile`) | Single container: Django serves the built SPA via WhiteNoise |
| Tests | pytest + pytest-django, 280 tests | No database-engine-specific tests |

Request flow, unchanged by this phase:

```
Browser (React SPA)
    │  fetch("/api/...", { Authorization: Bearer <JWT> })
    ▼
Django REST Framework (ViewSets)
    │  Django ORM
    ▼
PostgreSQL or SQLite (DATABASES["default"])
```

The frontend never talks to the database, or to Supabase, directly — every
read and write goes through the Django API. That did not change.

## 2. Current database configuration — already Supabase-ready

`backend/config/settings.py` already implements exactly the pattern this
phase asked for, before any change was made:

```python
DATABASE_URL = os.environ.get("REC_DATABASE_URL") or os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres"):
    # parses postgresql://user:pass@host:port/name?sslmode=require
    # into ENGINE=django.db.backends.postgresql, with percent-decoded
    # credentials and an honoured sslmode.
    ...
else:
    # SQLite, either the DATABASE_URL="sqlite://..." form or the
    # backend/rec_aids.sqlite3 default.
    ...
```

- `psycopg[binary]>=3.2` is already in `backend/requirements.txt` (production
  extras section).
- No credentials are hardcoded anywhere in the codebase (verified by search).
- `DATABASE_URL` (the plain, provider-agnostic name Supabase's own docs use)
  was **already read as a fallback** behind `REC_DATABASE_URL`. Nothing here
  needed to be built — it needed to be **documented**, which was the gap: the
  root `.env.example` only mentioned `REC_DATABASE_URL`. Fixed in §"Changes
  made" below.
- `sslmode` from the connection string's query string is honoured, which
  matters because Supabase requires TLS.

**Conclusion:** pointing `REC_DATABASE_URL` (or `DATABASE_URL`) at a Supabase
Postgres connection string is a configuration change only — no code change is
required for the database layer to work.

## 3. Current authentication — untouched

Custom `accounts.User` (`AbstractBaseUser` + `PermissionsMixin`), issued and
verified with `djangorestframework-simplejwt`. Login endpoints:
`/api/auth/login/`, `/api/auth/admin/login/`, refresh at
`/api/auth/token/refresh/`, logout blacklists the refresh token. This is
**not** Supabase Auth and this phase did not touch it, per the task's explicit
instruction. Nothing about moving to Postgres requires any change here —
SimpleJWT and the custom user model are entirely independent of which
database engine is behind the ORM.

## 4. Current file/media storage

Three apps hold user-facing files or file-like data:

- `resources.Resource.file` — the only real upload target: a `FileField`
  (`resources/models.py`), written through `resource.file.save(...)` and read
  through `resource.file.open("rb")` in the authenticated download view
  (`resources/views.py::download`). Never a public URL — `MEDIA_ROOT` is not
  served statically; every byte is streamed through that one authenticated
  endpoint.
- `resources.Resource.url` — the other half of the same model: link-kind
  resources (`REFERENCE`, `YOUTUBE`) store a plain URL instead of a file
  (`kind` + a `CheckConstraint` enforce this is XOR, not both).
- Static assets (`STATIC_ROOT`) and the built SPA (`frontend/dist`) — served
  by WhiteNoise, unrelated to Supabase.

Storage backend is selected by `STORAGES["default"]` in `settings.py`,
already conditional:

```python
if REC_S3_ACCESS_KEY_ID:
    ...  # storages.backends.s3.S3Storage, boto3-backed
else:
    ...  # django.core.files.storage.FileSystemStorage (today's default)
```

The `S3Storage` branch already targets *any* S3-compatible endpoint via
`REC_S3_ENDPOINT_URL`, and the settings file's own comments already name
Supabase Storage as one of the intended targets (it speaks the S3 API). There
is even a pre-existing workaround for a real Supabase Storage limitation:
multipart upload isn't supported by its S3 compatibility layer, so the
transfer threshold is raised past the app's own upload size cap so every
upload is sent as a single `PUT`.

**This phase left that branch exactly as it was** — it works, but the
`REC_S3_*` variables were previously undocumented in `.env.example`. That's
fixed (see below); nothing else changed. No files were migrated. Local disk
is still the default with every `REC_S3_*` variable unset.

See `docs/SUPABASE_SETUP.md` §13 for the concrete future steps to actually
switch storage backends when that phase begins.

## 5. Existing models (for reference — none were changed)

```
Department ──< Semester ──< Subject ──< Resource
User (accounts.User) ─FK→ Department (student's own), ─FK→ Resource (uploaded_by)
WaContact / WaMessageLog (whatsapp app — bot conversation state)
```

All fields are plain Django ORM types: `CharField`, `TextField`,
`ForeignKey`, `BooleanField`, `DateTimeField`, `PositiveSmallIntegerField`,
`FileField`, `URLField`, one `JSONField` (`WaContact.context`, used for
short-lived bot conversation scratch space). Every constraint
(`UniqueConstraint`, `CheckConstraint`) is expressed through the Django ORM,
not raw SQL — Django translates these to the correct dialect for whichever
engine is configured.

## 6. Existing environment variables (before this phase)

All already read via `os.environ.get(...)` with safe defaults — none
hardcoded. Full list was in `.env.example` already, missing only the S3
storage and frontend-Supabase placeholders (added this phase): `REC_SECRET_KEY`,
`REC_DEBUG`, `REC_ALLOWED_HOSTS`, `REC_DATABASE_URL`, `REC_MEDIA_ROOT`,
`REC_MAX_UPLOAD_MB`, `REC_ACCESS_TOKEN_MINUTES`, `REC_REFRESH_TOKEN_DAYS`,
`REC_ALLOWED_STUDENT_EMAIL_DOMAIN`, `REC_CORS_ORIGINS`,
`WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`,
`WHATSAPP_APP_SECRET`, `WHATSAPP_DRY_RUN`, `GROQ_API_KEY`,
`VITE_API_BASE_URL`.

## 7. What had to change for Supabase readiness

Very little — this codebase was already built by someone anticipating this
exact move. Changes made this phase:

1. `.env.example` — documented the already-supported `DATABASE_URL` fallback
   and the already-supported `REC_S3_*` storage variables (both existed in
   code, neither was documented), and added commented-out
   `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` placeholders for a
   *future* phase.
2. `.gitignore` — tightened `.env` handling to the requested
   `.env` / `.env.*` / `!.env.example` pattern (previously `.env`,
   `.env.local`, `.env.*.local` — narrower, but nothing was actually at risk;
   see §Security).
3. Added `backend/academics/management/commands/check_db.py` — a new,
   read-only management command (`python manage.py check_db`) that verifies
   whatever database `DATABASE_URL`/`REC_DATABASE_URL` resolves to is
   reachable, without ever printing the host, user or password.
4. This document and `docs/SUPABASE_SETUP.md`.

Nothing else needed to change. No model changed, no migration was written, no
existing route or view was touched, no dependency was removed.

## 8. What deliberately did NOT change

- Authentication stayed on SimpleJWT + the custom `accounts.User` model. No
  Supabase Auth code was added.
- File storage stayed on local disk. The S3-compatible branch that would let
  it point at Supabase Storage already existed and was left as-is —
  documented, not activated.
- No frontend code was made to depend on Supabase. `@supabase/supabase-js`
  was **not** installed and no `src/lib/supabase.ts` client was created.
  Reasoning: the existing architecture is React → Django REST API → database;
  the frontend never queries a database directly today, so a Supabase client
  in the frontend would have nothing to do yet and would be dead code. The
  placeholder env vars are there so wiring one in later is a small, isolated
  change instead of a scramble to figure out naming conventions.
- No existing migration was altered, squashed, or deleted.
- No destructive command was run (`flush`, `migrate zero`, dropping the
  database, deleting a migration file).

## 9. Database compatibility audit (SQLite → PostgreSQL)

| Concern | Finding |
| --- | --- |
| Raw SQL / `cursor.execute` / `.raw()` / `.extra()` | None found anywhere in the backend |
| Data migrations with `RunSQL` / `RunPython` | None — every migration is a plain auto-generated schema migration |
| `JSONField` | One use (`WaContact.context`). Supported natively by both SQLite (json1) and PostgreSQL (`jsonb`); Django handles the column-type difference automatically |
| Case-insensitive search (`icontains`) | Used throughout (`academics/filters.py`, search endpoints). Portable: Django compiles it to `LIKE`+`UPPER()` on SQLite and `ILIKE` on PostgreSQL — same semantics, PostgreSQL's is actually more correct for non-ASCII text |
| Auto-increment / primary keys | `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` — portable; PostgreSQL uses a real sequence, SQLite an integer rowid, both transparent to the ORM |
| Unique / check constraints | All via `models.UniqueConstraint` / `models.CheckConstraint` (see `resources/models.py`'s file-XOR-url constraint, `academics/models.py`'s per-semester course code uniqueness). Both engines enforce these; PostgreSQL enforces `CheckConstraint` more strictly than SQLite, which is a strict improvement, not a risk |
| Nullable / blank fields | Standard, no engine-dependent defaults |
| Date/time handling | `USE_TZ = True`, all `DateTimeField`s — PostgreSQL stores these as `timestamptz` natively; SQLite stores ISO-8601 text. No custom formatting or engine-specific comparison found |
| Indexes | All declared via `models.Index` / `db_index=True` — portable |
| File fields | `FileField` — storage-backend-dependent, not database-engine-dependent (see §4) |

**Conclusion: no compatibility changes were required.** Every model, filter,
and query in this codebase was already written in a database-portable way.

## 10. Migration safety — verified, unchanged

```
$ python manage.py makemigrations --check --dry-run
No changes detected

$ python manage.py migrate --plan
No planned migration operations.

$ python manage.py check
System check identified no issues (0 silenced).
```

All migrations were already applied and no model has pending changes. No
migration was added, edited, or removed by this phase.

## 11. Potential migration risks (for when data actually moves)

These are risks for a *future* phase (moving real data into Supabase), not
things this phase needed to fix:

1. **Test database privileges.** `pytest-django` creates and drops a
   throwaway test database on every run. If the backend is pointed at a
   Supabase connection string, the test suite will try to `CREATE DATABASE`
   /`DROP DATABASE` against Supabase using whatever role `DATABASE_URL`
   authenticates as — the pooled Supabase connection (port 6543) is not
   guaranteed to allow this. **Recommendation:** keep running the test suite
   against local SQLite (the default with no `DATABASE_URL` set); only point
   `DATABASE_URL` at Supabase for the running application, not for `pytest`.
2. **Existing SQLite data.** This repo's `rec_aids.sqlite3` has real seeded
   department/subject data and possibly uploaded files. Moving to Supabase
   means either re-running the seed commands (`seed_departments`,
   `seed_academics`, `createadmin`) against the new database, or a one-time
   data export/import (`dumpdata`/`loaddata`) — the latter needs care because
   `dumpdata` output isn't guaranteed byte-identical across engines for every
   field type, though nothing unusual (see §9) was found here.
3. **Connection pooling.** Supabase's pooled connection (PgBouncer, port
   6543) runs in transaction mode, which does not support all PostgreSQL
   session-level features. This app's queries are all standard ORM
   read/writes with no session-level features (advisory locks, prepared
   statements outside a transaction, etc.) observed, so this is a low risk —
   flagged for awareness, not because a problem was found.
4. **`CONN_MAX_AGE = 60`** is already set for the PostgreSQL branch
   (persistent connections for 60s) — reasonable for a pooled connection, no
   change made.
5. **Uploaded files on disk today** stay on disk; they are not automatically
   in Supabase after switching only the database. Storage is a separate,
   later migration (see `docs/SUPABASE_SETUP.md` §13).

## 12. Security review for this phase

- `DATABASE_URL` / `REC_DATABASE_URL`: never hardcoded, never logged, never
  returned by any endpoint. `check_db` (new) reports engine + database name
  only, never host/user/password, and reports connection failures by
  exception *class name* only (not the driver's own error string, which for
  some drivers can echo back connection details).
- `.env` files: confirmed none has ever been committed to this repository's
  git history (checked `git log --all` across all branches, including the
  newly-merged `rec-academic` remote) and none exists in the working tree
  except `.env.example`. **No secret was found that needs rotating.**
- `.gitignore` now matches the requested `.env` / `.env.*` / `!.env.example`
  pattern.
- No hardcoded API keys, passwords, or tokens were found anywhere in the
  Python or TypeScript source (checked by pattern search).
- The new `VITE_SUPABASE_*` placeholders are commented out and documented as
  anon/publishable-key-only — the doc explicitly warns never to put a
  service-role key or a database URL behind a `VITE_` name, since Vite bakes
  anything with that prefix into the shipped JavaScript bundle.
- Existing authentication behaviour (SimpleJWT, refresh blacklisting, role
  checks) is unchanged.

## 13. Storage migration readiness (for the future phase — not done now)

To later move `resources.Resource.file` uploads to Supabase Storage:

1. Create a bucket in the Supabase dashboard (Storage → New bucket). Keep it
   **private** — this app never generates public URLs for resource files; it
   streams them through `resources/views.py::download` with its own auth
   check, and that must stay true regardless of where the bytes live.
2. Get the S3-compatible connection details: Project Settings → Storage → S3
   Connection (access key, secret key, endpoint URL, region).
3. Set `REC_S3_ACCESS_KEY_ID`, `REC_S3_SECRET_ACCESS_KEY`,
   `REC_S3_BUCKET_NAME`, `REC_S3_ENDPOINT_URL`, `REC_S3_REGION_NAME` (all
   already read by `settings.py`, documented in `.env.example` as of this
   phase).
4. New uploads go to the bucket automatically — no code change, since
   `Resource.file.save()` already goes through Django's storage abstraction.
5. Existing local files would need a one-time copy into the bucket
   (`resource.file` re-`save()`d through the new storage, or a small script
   iterating `Resource.objects.all()`), which is a data migration, not a
   schema one, and was intentionally **not** performed in this phase.

## 14. Summary

The project was already built with Supabase (or any managed PostgreSQL, plus
any S3-compatible storage) in mind — `REC_DATABASE_URL`/`DATABASE_URL`
parsing, `psycopg[binary]`, and an S3 storage backend explicitly naming
Supabase Storage in its own comments all predate this phase. This phase's job
was mostly **verification and documentation**, plus two small, safe additions
(the `check_db` command, and the missing `.env.example` entries). See
`docs/SUPABASE_SETUP.md` for the exact commands to connect a real Supabase
project.
