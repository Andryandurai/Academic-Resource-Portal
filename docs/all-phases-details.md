# REC-Academic — All-Phases Implementation Report

This file is the running master record for every implementation phase
performed on this project. New phases are appended below; existing phase
sections are never overwritten or removed.

---

# Phase 1 — Supabase Readiness

## Objective

Prepare the existing REC-Academic project to connect to Supabase PostgreSQL,
and document the path to Supabase Storage, without rebuilding, redesigning,
removing features, changing the UI, or migrating authentication or file
storage yet.

## Initial Architecture

React 19 + TypeScript (Vite 6) frontend → Django 5.2 + DRF 3.15 REST API
(SimpleJWT bearer auth, custom `accounts.User` model) → SQLite in development.
Deployed as a single Docker container (Django serves the built SPA via
WhiteNoise) to Render. Full detail in `docs/supabase-readiness-analysis.md`.

The database layer was found to already be Supabase-ready before this phase
began: `REC_DATABASE_URL` / `DATABASE_URL` parsing (with `sslmode` support),
`psycopg[binary]` as the driver, and an S3-compatible storage backend whose
own code comments already name Supabase Storage as a supported target, all
predate this phase.

## Changes Made

1. Documented the already-working `DATABASE_URL` fallback and the
   already-working `REC_S3_*` storage variables in `.env.example` (neither
   was documented before, though both were already read by
   `backend/config/settings.py`).
2. Added commented-out `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY`
   placeholders to `.env.example` for a future phase — not read by any code
   yet.
3. Tightened `.gitignore`'s environment-file handling from
   `.env` / `.env.local` / `.env.*.local` to the requested
   `.env` / `.env.*` / `!.env.example`.
4. Added `backend/academics/management/commands/check_db.py` — a new,
   read-only `python manage.py check_db` command that verifies database
   connectivity without ever printing host, user, or password.
5. Wrote `docs/supabase-readiness-analysis.md` (full architecture and
   compatibility audit) and `docs/SUPABASE_SETUP.md` (step-by-step connection
   guide).

No application code (models, views, serializers, URLs, frontend components,
routes) was changed. No migration was added, edited, or removed. No existing
environment variable's behaviour changed — only new, additional ones were
documented.

## Files Created

- `docs/supabase-readiness-analysis.md`
- `docs/SUPABASE_SETUP.md`
- `docs/all-phases-details.md` (this file)
- `backend/academics/management/commands/check_db.py`

## Files Modified

- `.env.example` — added `DATABASE_URL` fallback note, `REC_S3_*` storage
  placeholders, `VITE_SUPABASE_*` placeholders.
- `.gitignore` — environment-file ignore pattern tightened.

## Dependencies Added

None. `psycopg[binary]`, `django-storages`, `boto3`, and `python-dotenv` were
already present in `backend/requirements.txt` from prior work on this
project, and were already installed in the local venv used to verify this
phase.

## Environment Variables

New (documented, not yet required — all optional):

- `DATABASE_URL` — plain fallback name for `REC_DATABASE_URL` (was already
  read by settings.py; now documented).
- `REC_S3_ACCESS_KEY_ID`, `REC_S3_SECRET_ACCESS_KEY`, `REC_S3_BUCKET_NAME`,
  `REC_S3_ENDPOINT_URL`, `REC_S3_REGION_NAME` — S3-compatible storage
  (Supabase Storage or otherwise); was already read by settings.py, now
  documented.
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` — reserved for a
  future phase; not read by any code yet.

Unchanged: every variable listed in §6 of `supabase-readiness-analysis.md`.

## Database Changes

None. No model changed. No migration was created, edited, or deleted.
`makemigrations --check --dry-run` reported no changes; `migrate --plan`
reported no planned operations, both before and after this phase.

## Storage Assessment

Uploaded resource files remain on local disk (`MEDIA_ROOT`) — unchanged. The
S3-compatible backend that would let this point at Supabase Storage already
existed in `settings.py` (behind `REC_S3_ACCESS_KEY_ID`) and was left
inactive. Full migration path documented in
`docs/supabase-readiness-analysis.md` §13 and `docs/SUPABASE_SETUP.md` §13.
No file was moved.

## Security Changes

- Verified (via `git log --all` across every branch/remote) that no `.env`
  file has ever been committed to this repository — nothing needed rotating.
- Verified no hardcoded secrets exist anywhere in the Python or TypeScript
  source.
- `.gitignore` tightened as described above.
- New `check_db` command never prints credentials — only engine, database
  name, and (on failure) the exception's class name, never the driver's own
  error string.
- `.env.example` explicitly documents that only a Supabase anon/publishable
  key is ever safe in a `VITE_` variable, and that a service-role key or
  database URL must never go there.

## Tests Performed

```
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py check_db                 (against local SQLite)
python manage.py check_db                 (against a fabricated, unreachable
                                            postgresql:// URL — confirmed
                                            graceful failure, no credential
                                            leakage, exit code 1)
python -m pytest -q                       (backend, full suite)
npm run build                             (frontend)
```

## Test Results

| Check | Result |
| --- | --- |
| `manage.py check` | `System check identified no issues (0 silenced).` |
| `makemigrations --check --dry-run` | `No changes detected` (exit 0) |
| `migrate --plan` | `No planned migration operations.` |
| `check_db` (SQLite) | `Connection OK — the database is reachable.` |
| `check_db` (fake Postgres URL) | Failed as expected, exit 1, no credentials printed |
| `pytest -q` (backend) | All tests passed (280 tests) |
| `npm run build` (frontend) | Built successfully |

## Issues Found

None that blocked this phase. See "Potential migration risks" in
`docs/supabase-readiness-analysis.md` §11 for risks flagged for a *future*
phase (test-database privileges against a pooled Supabase connection,
existing SQLite data migration, connection pooling mode) — none of these are
defects in the current codebase, they are things to be aware of when data
actually moves.

## Issues Not Fixed

None identified that needed fixing within this phase's scope.

## Assumptions

- "Ready to connect" means configuration-only readiness verified against a
  realistic (but fabricated, unreachable) Supabase-shaped connection string,
  not a live connection to a real Supabase project — no real Supabase
  project credentials were available or requested during this phase, per the
  task's explicit instruction not to invent or request credentials.
- The frontend does not need direct Supabase access in this phase, since the
  existing architecture routes every database interaction through the
  Django API. This assumption is documented so it can be revisited if a
  later phase (e.g. Supabase Auth) changes it.
- "Existing seed/sample data" (departments, subjects, the local SQLite file)
  stays on SQLite for local development; moving it to Supabase is a
  deliberate future action (§7 of `SUPABASE_SETUP.md`), not something this
  phase performed.

## Supabase Connection Instructions

See `docs/SUPABASE_SETUP.md` for the full step-by-step guide. Summary:

1. Create a Supabase project; copy its PostgreSQL connection URI.
2. Set `REC_DATABASE_URL` (with `?sslmode=require`) in `backend/.env`.
3. `pip install -r requirements.txt` (dependencies already listed).
4. `python manage.py migrate`.
5. `python manage.py createadmin --email ... --name ...`.
6. `python manage.py check_db` to confirm connectivity.
7. Run the app as usual — no other code or config differs from local
   development.

## Future Phase Recommendations

1. **Phase 2 (if desired): Supabase Storage activation.** Set the five
   `REC_S3_*` variables against a real Supabase Storage bucket; verify
   uploads and the authenticated download endpoint end-to-end; then decide
   whether to migrate existing local files.
2. **Phase 3 (if desired): Supabase Auth.** Only if there's a real reason to
   move off SimpleJWT + the custom `accounts.User` model — the current setup
   works and this was explicitly out of scope here. Would need a plan for
   preserving existing accounts/passwords.
3. **Data migration.** A one-time `dumpdata`/`loaddata` (or a small custom
   script) to move the current SQLite catalogue data into the real Supabase
   database, once a Supabase project actually exists and its credentials are
   available outside of chat/commit history.
4. **CI.** If a CI pipeline is added later, run `pytest` against SQLite (see
   §11 risk about pooled-connection `CREATEDB` privileges) and run
   `check_db` against the real deployment target as a deploy-gate step.

---

# Phase 2 — Supabase PostgreSQL Connection

## Objective

Connect the existing Django backend to a real Supabase PostgreSQL database
— establishing the schema/connection only, per the explicit scope: no data
migration, no Storage activation, no Auth change, no application redesign.

## Supabase Project Configuration

Project: **REC-Academic**. No credentials appear in this document — see
`docs/SUPABASE_SETUP.md` §2 for the project's non-secret connection details
(host, port, database name, username). The database password was entered
directly into `backend/.env` by the user; Claude never viewed, requested,
logged, or wrote it.

## Existing Database Configuration

Unchanged from Phase 1: `backend/config/settings.py` already read
`REC_DATABASE_URL` (preferred) or `DATABASE_URL`, with `psycopg[binary]`
already installed. This phase used that existing mechanism exactly as-is —
no settings.py change.

## Changes Made

1. Created `backend/.env` (gitignored, never committed) with
   `REC_DATABASE_URL` pointed at Supabase. The password was entered by the
   user directly, twice — once for the direct connection, once (after
   switching) for the Session Pooler connection — never by Claude.
2. Diagnosed and worked around **two real, user-caused configuration
   issues** encountered along the way (see "Issues Found" below) without
   ever displaying the password: an unencoded `#` character in the
   Session Pooler password, and a TCP-level connectivity problem with the
   direct connection endpoint.
3. Ran `python manage.py migrate` against Supabase — created the full
   schema (34 migrations across 7 apps).
4. Updated `docs/SUPABASE_SETUP.md` with the real (working) Session Pooler
   procedure, the connectivity finding, and the password-encoding gotcha.
5. Updated `.env.example` with the same encoding warning and a note
   preferring the pooler over the direct connection.
6. No model, view, serializer, URL, or frontend file was changed.

## Files Modified

- `.env.example`
- `docs/SUPABASE_SETUP.md`
- `docs/all-phases-details.md` (this section)

## Files Created

- `backend/.env` (local only — gitignored, not part of the git history)

No application code file was created or modified in this phase.

## Migration Results

```
python manage.py migrate
```

All 34 migrations across `academics`, `accounts`, `auth`, `contenttypes`,
`resources`, `token_blacklist`, and `whatsapp` applied successfully
(`... OK` for every one). Re-running `migrate --plan` afterward reported
"No planned migration operations." — confirming nothing was left pending.
`makemigrations --check --dry-run` reported "No changes detected" — no model
drifted from its migrations.

## Database Verification

Verified via Django's schema introspection (`connection.introspection.table_names`)
against the live Supabase connection — not by any raw SQL or manual table
creation. **16 tables found**, including every expected one:
`accounts_user`, `academics_department`, `academics_semester`,
`academics_subject`, `resources_resource`, `whatsapp_wacontact`,
`whatsapp_wamessagelog`, `django_migrations`,
`token_blacklist_outstandingtoken`, `token_blacklist_blacklistedtoken`, and
the rest of Django's/DRF's own tables (`auth_*`, `django_content_type`).

`python manage.py check_db` confirmed reachable, reporting only:
```
Engine:   postgresql
Database: postgres
Connection OK — the database is reachable.
```

## Test Results

**Backend** — full `pytest` suite, run against local SQLite (explicitly with
`REC_DATABASE_URL=""` for that invocation only — `backend/.env` and the
running app were unaffected and still point at Supabase): **passed, exit
code 0**, same result as every prior run in this project (280 tests). This
override was necessary and is now documented — see "Issues Found".

**Frontend** — `npm run build`: succeeded, same output as every prior build
in this project (`dist/index.html`, CSS and JS bundles, no errors).

**Django checks against Supabase:**

| Check | Result |
| --- | --- |
| `manage.py check` | Clean, both before and after the password fixes |
| `manage.py migrate` | 34/34 migrations applied |
| `manage.py showmigrations` | All `[X]` (applied) |
| `manage.py makemigrations --check --dry-run` | No changes detected |
| `manage.py migrate --plan` | No planned migration operations |
| `manage.py check_db` | Connection OK |
| Table introspection | 16/16 expected tables found |

## Frontend Build Result

Succeeded (`npm run build`), unaffected by any backend database change — the
frontend never talks to the database directly.

## Data Migration Status

**Schema migration: completed.** **Existing application data migration has
NOT been performed.** The Supabase database now has the full table
structure, empty of rows. The local SQLite database
(`backend/rec_aids.sqlite3`) still holds whatever data it had, untouched by
this phase. Moving real data across is a deliberate separate action — see
`docs/SUPABASE_SETUP.md` §11.

## Storage Status

Unchanged. `REC_S3_*` was not set; local disk (`MEDIA_ROOT`) remains the
storage backend. Not activated, per explicit instruction.

## Authentication Status

Unchanged. SimpleJWT + the custom `accounts.User` model, exactly as before.
No Supabase Auth code was added.

## IPv4/IPv6 Notes

The direct connection (`db.kuzjdhvyvsgiweayrarg.supabase.co:5432`) resolves
IPv6-only, as expected. It was reachable at the TCP level on the very first
test. After a burst of connection attempts using an incorrect placeholder
password (while validating the setup before the real password was entered),
the same endpoint became consistently unreachable at the TCP level across
several retries spaced minutes apart — while this machine's general IPv6
connectivity remained confirmed working throughout (tested independently
against an unrelated host). This does not match an IPv4/IPv6 capability gap
(DNS resolved, IPv6 worked generally) — the most likely explanation is
Supabase-side throttling of that endpoint following the failed-auth burst,
though this was not confirmed against Supabase's own logs/status. **No
Supabase project setting, billing plan, or the IPv4 add-on was changed** to
resolve this — switching `REC_DATABASE_URL` to the **Session Pooler**
connection (a different host already offered by the same Supabase project)
resolved it immediately and has been reliable since.

## Security Verification

- The password was never read, displayed, logged, or written to any file by
  Claude. It was entered directly into `backend/.env` by the user, twice.
- **One real, disclosed incident:** an unencoded `#` in the Session Pooler
  password caused a Python `ValueError` traceback (from `urllib.parse`, a
  standard library module, not this repo's code) that echoed a fragment of
  the connection string into terminal output during diagnosis. This was
  flagged to the user immediately and in full, with a recommendation to
  rotate the password; the user's decision was to proceed rather than
  rotate. All diagnosis after that point used redacted, boolean-only checks
  (character presence, string lengths, exception class names) that never
  printed the password, the full URL, or any substring of it.
- `git status` and `git check-ignore backend/.env` were run and confirmed:
  `backend/.env` is ignored, not staged, and not present in git history at
  any point in this project (checked across all branches/remotes in Phase
  1, re-verified clean in this phase).
- No commit in this phase touches `backend/.env` or any credential.
- `check_db` continues to report only engine and database name, never
  credentials — verified again against the live Supabase connection.

## Remaining Manual Steps

1. Create an admin user against the Supabase database:
   `python manage.py createadmin --email ... --name ...` (or
   `createsuperuser`).
2. Decide whether/when to seed catalogue data (`seed_departments`,
   `seed_academics`) or migrate real existing data from SQLite — not done
   automatically, per instruction.
3. Decide whether to keep using the Session Pooler long-term or retry the
   direct connection later (it may recover on its own if it was a temporary
   throttle) — no action needed unless a problem resurfaces.
4. Storage (Supabase Storage) and Auth (Supabase Auth) migrations remain
   explicitly out of scope, for a future phase if ever wanted.
5. If a CI pipeline is added, make sure it runs `pytest` with
   `REC_DATABASE_URL` cleared, exactly as documented in
   `docs/SUPABASE_SETUP.md` §10 — otherwise it will hit the same
   test-database timeout behaviour found in this phase.

---

# Phase 3 — Data Migration Plan (Analysis Only)

## Objective

Inspect the local SQLite database and the (now-schema-only) Supabase
database, and produce an exact, reviewable plan for migrating real
application data across. **No data was migrated, modified, or deleted in
this phase** — every command run was read-only (`.count()`, introspection,
`SELECT COUNT(*)`).

Full detail in `docs/data-migration-plan.md`; this is the summary.

## What Was Found

- Local SQLite (`backend/rec_aids.sqlite3`, ~508 KB): 19 departments, 152
  semesters, 910 subjects, 11 resources (all file-backed PDFs, ~50 MB on
  disk, all verified present), 2 users (1 admin, 1 student, both
  `pbkdf2_sha256`).
- Supabase (Session Pooler): schema only, as left by Phase 2 — 0 rows in
  every catalogue/resource table, 1 user (the admin created after Phase 2,
  unrelated to the local users).
- Zero orphaned foreign keys, zero missing files, zero many-to-many tables
  in use anywhere in the schema.
- `auth_permission` (48), `django_content_type` (12), and
  `django_migrations` (35) already match exactly between local and
  Supabase — these are Django-generated, not real data, and are correctly
  excluded from any future migration.
- `token_blacklist_*` tables (30 + 74 rows locally) are session bookkeeping
  tied to a `SECRET_KEY` that differs between environments — correctly
  excluded.

## Recommended Strategy

Django's own `dumpdata`/`loaddata`, run per-app, reviewed by hand before
loading — not a custom script, not raw SQL. Full reasoning in
`docs/data-migration-plan.md` §Recommended Migration Strategy.

## Open Decision Before Any Future Migration Runs

User migration is a product decision, not a mechanical one: whether the
local admin/student accounts should become the Supabase accounts,
supersede, or coexist with the admin already created directly against
Supabase. Flagged, not decided, in this phase.

## Files Created

- `docs/data-migration-plan.md`

## Files Modified

- `docs/all-phases-details.md` (this section)

No application code, model, migration, or database was touched.

## Data Migration Status

**Not performed.** This phase is analysis only, per explicit instruction.
The exact commands to run (once the user-migration decision above is made
and approved) are listed in `docs/data-migration-plan.md` §Next Steps.

---

# Phase 4 — Academic Data + User Migration

## Objective

Execute the plan from Phase 3: migrate real academic catalogue data,
resource metadata, and the two local user accounts from local SQLite into
the now-schema-only Supabase database, per the user's explicit "Option C"
decision — keep the existing Supabase admin **and** migrate both local
users as separate accounts (not a merge, not a replacement). File bytes
(PDFs) and Supabase Storage/Auth remained explicitly out of scope.

## Backup

Before any write to either database:

- `backend/rec_aids.sqlite3` copied to
  `backend/.backups/<timestamp>/rec_aids.sqlite3.backup` — verified
  byte-identical to the original (520,192 bytes) both before and after the
  full migration.
- `backend/media/` (23 files, 50 MB) copied to
  `backend/.backups/<timestamp>/media/`.
- Supabase's pre-migration `accounts.User` table (the single existing admin
  row) exported to
  `backend/.backups/<timestamp>/supabase-pre-migration/accounts_user.json`
  — used later to prove, field-by-field, that this row was never modified.
- All backups are local-only, under directories now explicitly added to
  `.gitignore` (`backend/.backups/`, `backend/.migration_fixtures/`) — see
  §Files Modified.

## Academic Export

`dumpdata`, per model, from local SQLite (read-only against that database):
Department (19), Semester (152), Subject (910), Resource (11). Counts
matched Phase 3's inventory exactly. Reviewed before loading: every foreign
key within the fixtures resolved (zero orphans), no credentials or secrets
present in any academic fixture.

## Academic Import

Loaded into Supabase via `loaddata`, in dependency order, with primary keys
preserved (safe — Supabase's academic tables were completely empty, no
collision risk):

| Model | Loaded | Verified count |
| --- | --- | --- |
| Department | 19 | 19 ✅ |
| Semester | 152 | 152 ✅ |
| Subject | 910 | 910 ✅ |
| Resource | 11 | 11 ✅ (loaded *after* user migration — see below) |

PostgreSQL sequences for all four tables confirmed correctly positioned
after the load (`last_value >= max(id)` for each) — no manual `setval()`
needed; Django's `loaddata` handles this automatically on PostgreSQL.

## User Migration

**A primary-key conflict was found and handled exactly as Step 9
anticipated — not a stop condition.** The local admin's id (1) collided
with the pre-existing Supabase admin's id (also 1). No unique-field
(email) conflict existed — the three accounts' emails are all distinct.

Resolution: the two local users were created on Supabase via the Django
ORM with **freshly auto-assigned primary keys** (not the local ones),
copying every non-secret field (email, name, role, is_staff, is_superuser,
is_active, department, created_at) and the **existing password hash
copied verbatim** (never re-hashed, never displayed, never logged) so both
accounts keep their original login credentials.

| | Local id | Supabase id | Email | Role |
| --- | --- | --- | --- | --- |
| Migrated admin | 1 | **2** | `admin@rec.local` | ADMIN |
| Migrated student | 2 | **3** | `student@rec.local` | STUDENT |
| *(pre-existing, untouched)* | — | 1 | *(the Phase-2 admin)* | ADMIN |

Because the migrated admin's ID changed from 1 to 2, the Resource fixture's
`uploaded_by` field (all 11 resources were uploaded by local admin id 1)
was **remapped to id 2 before loading** — not loaded with the raw local
value, which would have silently misattributed every resource to the
*pre-existing* Supabase admin instead of the person who actually uploaded
them. This is why Resource was loaded after users, not before as the
literal step order suggested — flagged and explained at the time, done to
prevent a real (if non-crashing) data-integrity bug rather than to follow
the letter of the instructions over their evident intent.

`accounts_user_id_seq` confirmed correctly positioned after the ORM-based
creation (Postgres advances it automatically on a normal `INSERT`).

**The pre-existing Supabase admin (id 1) was proven unmodified**, not just
assumed: every field — including the password hash — was compared against
the Phase 1 backup and found identical, `updated_at` included (which would
have changed had the row been touched by any `save()` call). The comparison
reported equality only, never the values themselves.

## Final User Count

**3**, as required: the pre-existing Supabase admin (id 1, unmodified),
the migrated local admin (id 2), the migrated local student (id 3).

## Database Row Counts

| Model | Local | Supabase (final) | Match |
| --- | --- | --- | --- |
| Department | 19 | 19 | ✅ |
| Semester | 152 | 152 | ✅ |
| Subject | 910 | 910 | ✅ |
| Resource | 11 | 11 | ✅ |
| User | 2 (source) | 3 (2 migrated + 1 pre-existing) | ✅ (by design) |

## Foreign Key Validation

Checked directly on Supabase after the full migration: zero orphaned
semesters (bad department FK), zero orphaned subjects (bad semester FK),
zero orphaned resources (bad subject FK *or* bad `uploaded_by` FK), zero
users with an invalid department FK. Zero duplicate
`(department, semester_number)` pairs, zero duplicate
`(semester, course_code)` pairs, zero duplicate emails.

## Authentication Verification

- Migrated admin (`admin@rec.local`) — logged in successfully against
  Supabase via `/api/auth/admin/login/`: HTTP 200, response `user.id == 2`,
  `role == ADMIN`, `is_admin == true`.
- Migrated student (`student@rec.local`) — logged in successfully via
  `/api/auth/login/`: HTTP 200, `user.id == 3`, `role == STUDENT`,
  `is_admin == false`.
- Pre-existing Supabase admin — verified structurally rather than by live
  login (its password is not known to Claude and was not guessed or
  reset): confirmed present, `is_active`, role, and every other field
  including the password hash unchanged from before this phase (see
  §User Migration above).
- Both test logins' JWTs were blacklisted immediately after verification —
  see §Problems Encountered.
- No change to the authentication system itself: still SimpleJWT + the
  custom `accounts.User` model.

## Resource Verification

All 11 migrated `Resource` rows checked against local disk: every `file`
path resolves to an existing file under `backend/media/` — same files
Phase 3 verified, untouched, still local-disk-only. No file bytes were
uploaded anywhere; only the 11 database rows describing them were migrated,
as scoped.

## Test Results

Full `pytest` suite, run against local SQLite (`REC_DATABASE_URL=""` for
that invocation only): **280 tests passed, exit code 0** — identical to
every prior run in this project. Confirms the migration work (which only
ever wrote to Supabase) left the local database and the app's own
correctness completely unaffected.

Also, against Supabase: `manage.py check` (clean), `makemigrations --check`
("No changes detected"), `migrate --plan` ("No planned migration
operations"), `check_db` ("Connection OK").

## Frontend Build

`npm run build` succeeded — unaffected, as in every prior phase.

## Data Integrity

Re-verified read-only, after all writes were complete: row counts stable
(19/152/910/11/3), zero orphans, zero duplicates. Live API smoke tests
against Supabase — `/api/departments/` (19 departments), `/api/semesters/`
(8 for AI&DS), `/api/subjects/?search=data` (62 matches), `/api/subjects/facets/`
(total 910 across 19 departments), `/api/resources/?subject=12` (5
resources) — all returned expected, correct results.

## Storage Status

Unchanged. All files remain on local disk (`backend/media/`). Supabase
Storage was not activated, no `REC_S3_*` variable was set, no file was
uploaded anywhere. Explicitly out of scope for this phase and the next.

## Remaining Work

1. **Phase 5 (not started, per explicit instruction to stop):** Supabase
   Storage — actually uploading the 11 PDFs (~50 MB) so the app can serve
   them from somewhere other than this one machine's disk.
2. Decide what to do with the two test JWTs generated during verification
   — already blacklisted, no action required, noted for completeness.
3. Consider whether the pre-existing Supabase admin (id 1) is still the
   intended primary admin account going forward, now that two more admin
   *and* student accounts exist on Supabase — a product decision, not a
   technical one.
4. The local SQLite database and its backup remain as the historical
   source of truth for this data — no further action needed on them.

## Problems Encountered

**One security incident, disclosed immediately and already remediated:**
during live authentication verification, a `curl | ` fallback command (the
`python3` binary it expected wasn't on `PATH`, so the pipeline fell through
to a plain `cat` of the raw HTTP response) printed a real JWT **refresh
token** into tool output for one test login. This was not a password, a
password hash, or the database connection string — but it was a live
credential that shouldn't have been displayed.

Remediation, immediate: the leaked token was blacklisted via
`rest_framework_simplejwt`'s blacklist (by its `jti`, recovered from the
same accidental output, since the raw token string itself was not reused);
it can no longer be used to obtain a new access token. Every verification
step afterward — including a second, correctly-executed login test for the
same account — used a method that parses the JSON response with Python and
prints only field names/booleans/safe values, never a token, and every
test-login token generated during verification (not just the leaked one)
was blacklisted immediately after use as routine hygiene.

No other credential, password, hash, or connection string was ever
displayed, logged, or committed at any point in this phase.

## Rollback Information

Nothing needed rolling back — every step succeeded and was verified before
proceeding to the next. If it had been needed: the local SQLite database
was never written to (every local-side operation was a read), so it was
never at risk; the Supabase-side data added by this phase
(Department/Semester/Subject/Resource rows, plus the 2 new User rows) could
be removed with per-model `.delete()` calls in reverse dependency order
without affecting the pre-existing Supabase admin, exactly as
`docs/data-migration-plan.md` §Rollback Plan describes.

## Files Created

- `backend/.backups/<timestamp>/` — SQLite backup, media backup, Supabase
  pre-migration user snapshot. Local-only, gitignored.
- `backend/.migration_fixtures/` — reviewed dumpdata fixtures (academic
  data, the corrected Resource fixture, the local-user fixture with
  password hashes, the user ID-mapping file). Local-only, gitignored.

## Files Modified

- `.gitignore` — added `backend/.backups/` and `backend/.migration_fixtures/`.
- `docs/data-migration-plan.md` — execution-status note added; the
  original plan preserved as-is.
- `docs/all-phases-details.md` (this section).

No application code, model, migration, or the local SQLite database itself
was modified.
