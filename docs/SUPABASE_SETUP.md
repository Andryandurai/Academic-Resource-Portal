# Connecting REC-Academic to Supabase

This is the exact procedure to connect this project to a real Supabase
project. It assumes the codebase is already at the state described in
`docs/supabase-readiness-analysis.md` — the database layer already supports
this with no code change; this document is configuration only.

**Current status: this project is connected to Supabase PostgreSQL and the
full schema has been migrated.** See `docs/all-phases-details.md` → Phase 2
for the complete results. The rest of this document is the reusable
procedure, written against this project's real (non-secret) connection
details — the password is never in this document, in `.env.example`, or in
any file Claude writes.

Two setups are described throughout. Use whichever matches what you're doing
right now:

- **LOCAL DEVELOPMENT** — the default. SQLite, zero configuration, exactly as
  the project has always run.
- **SUPABASE / PRODUCTION** — point the same codebase at a Supabase
  PostgreSQL database (and, later, Supabase Storage) instead.

Nothing in the application code differs between the two; only environment
variables change.

---

## 1. Create a Supabase project

1. Go to <https://supabase.com>, sign in, and click **New project**.
2. Choose an organisation, a project name, a database password (generate a
   strong one — **save it now**, it's shown only once), and a region close
   to where the app will run.
3. Wait for provisioning to finish (a couple of minutes).

(This project already has a Supabase project — see §2.)

## 2. This project's Supabase database connection information

From the Supabase dashboard: **Project Settings** (gear icon) → **Database**
→ **Connection string**.

| | Direct connection | Session Pooler *(currently in use)* |
| --- | --- | --- |
| Host | `db.kuzjdhvyvsgiweayrarg.supabase.co` | *(get from dashboard — region-specific)* |
| Port | `5432` | `5432` |
| Database | `postgres` | `postgres` |
| User | `postgres` | `postgres.kuzjdhvyvsgiweayrarg` (project ref appended) |
| Password | *(yours)* | *(yours)* |

**This deployment uses the Session Pooler, not the direct connection.** The
direct connection (`db.<ref>.supabase.co:5432`) was tried first and its TCP
port was reachable once, but became consistently unreachable shortly after
— see §6 for the full finding. The Session Pooler resolved it and is what
`backend/.env` is configured with now.

## 3. Obtain the PostgreSQL connection string

The full form, with your real password substituted in and `sslmode=require`
appended (Supabase requires TLS):

```
postgresql://postgres.kuzjdhvyvsgiweayrarg:your-real-password@<pooler-host-from-dashboard>:5432/postgres?sslmode=require
```

**If the password contains any of `: / ? # [ ] @ ! $ & ' ( ) * + , ; = %`,
percent-encode it before putting it in the URL.** This was a real issue
during this project's setup — an unencoded `#` in the password silently
truncated the entire rest of the connection string (a URL fragment
delimiter), which surfaced as a confusing "port could not be parsed" error
with no indication the password was the cause. Encode it yourself:

```bash
python -c "from urllib.parse import quote; print(quote('your-password', safe=''))"
```

## 4. Configure `REC_DATABASE_URL`

`backend/.env` (gitignored, never committed) holds:

```bash
REC_DEBUG="1"
REC_DATABASE_URL="postgresql://postgres.kuzjdhvyvsgiweayrarg:<percent-encoded-password>@<pooler-host>:5432/postgres?sslmode=require"
```

Enter your own percent-encoded password directly into that file — Claude
does not have it and will not ask for it.

`REC_DATABASE_URL` takes priority over a bare `DATABASE_URL`, so either name
works if your hosting platform injects the plain one instead — both are
read.

**LOCAL DEVELOPMENT alternative:** delete `backend/.env` (or clear
`REC_DATABASE_URL` in it) to fall back to the local SQLite file.

## 5. Install required dependencies

The PostgreSQL driver is already in `backend/requirements.txt`
(`psycopg[binary]`). From the `backend/` directory:

```bash
python -m venv venv
venv\Scripts\activate            # Windows; source venv/bin/activate on Unix
pip install -r requirements.txt
```

## 6. IPv4 / IPv6 consideration, and why this project uses the pooler

Supabase's **direct connection** resolves to an **IPv6 address only** — no
IPv4 (`A`) record — unless the paid IPv4 add-on is enabled, which this
project does **not** use.

What was actually observed while setting this project up:

1. The direct connection's IPv6 address **was** reachable at the TCP level
   on the first test (general IPv6 connectivity from the dev machine was
   confirmed working throughout, including against an unrelated host).
2. After a burst of connection attempts with an incorrect password (testing
   the setup before the real password was entered), the direct connection
   became **consistently unreachable** at the TCP level — not an
   authentication failure, a network-level failure, across multiple retries
   spaced minutes apart.
3. Switching to the **Session Pooler** (a different host, a PgBouncer layer
   in front of Postgres) connected immediately and has worked reliably
   since.

The most likely explanation is Supabase-side throttling of the direct
connection endpoint after repeated failed authentication attempts from the
same source — not a real IPv4/IPv6 gap, since general IPv6 worked
throughout and DNS resolution never failed. This wasn't confirmed against
Supabase's own status/logs, so it's reported as the most likely explanation
rather than a certainty.

**No Supabase project setting, billing plan, or the IPv4 add-on was changed**
to work around this — the pooler was already available as a normal
connection option, and switching to it required only an environment
variable change on this side.

If you hit the same direct-connection issue on a fresh setup: try the
Session Pooler first, or wait a few minutes and retry the direct connection
before concluding it's IPv4/IPv6-related.

## 7. Run migrations

With `REC_DATABASE_URL` set to your real connection string (§4):

```bash
cd backend
python manage.py check
python manage.py migrate
python manage.py showmigrations
```

This creates every table (`accounts`, `academics`, `resources`, `whatsapp`,
`auth`, `contenttypes`, `token_blacklist`) in the Supabase database. Safe to
re-run — Django migrations are idempotent. **Already done for this
project** — see Phase 2 in `docs/all-phases-details.md` for the full
migration list and table verification.

**Do not** run `flush`, `migrate <app> zero`, or drop the database.

## 8. Create an admin/superuser

```bash
python manage.py createadmin --email admin@yourcollege.edu --name "Your Name"
```

(Or `python manage.py createsuperuser`.) Optionally seed catalogue data:

```bash
python manage.py seed_departments
python manage.py seed_academics
```

**Not yet done for this project** — the Supabase database currently has the
schema only (empty tables). See §11.

## 9. Test the backend

```bash
python manage.py check
python manage.py check_db
python manage.py runserver
```

`check_db` reports only the engine and database name, never credentials.
Confirmed working against this project's Supabase database:

```
Engine:   postgresql
Database: postgres
Connection OK — the database is reachable.
```

## 10. Running the test suite (keep it on local SQLite)

**Do not run `pytest` while `backend/.env` points `REC_DATABASE_URL` at
Supabase.** Confirmed during this project's setup: pointing the test runner
at Supabase makes pytest-django try to create/drop a throwaway test database
there, which either needs privileges the connecting role may not have, or —
observed directly — hangs for a long time before failing with a timeout,
rather than failing fast.

Override for the one test invocation, which falls back to local SQLite
(confirmed: full 280-test suite passes this way):

```bash
# bash / Git Bash
REC_DATABASE_URL="" python -m pytest -q
```

```powershell
# PowerShell
$env:REC_DATABASE_URL = ""
python -m pytest -q
Remove-Item Env:\REC_DATABASE_URL
```

This only affects that one command's environment — `backend/.env` (and
therefore `manage.py runserver`) is unaffected and keeps using Supabase.

## 11. Data migration is a separate step — NOT performed yet

Connecting Django to Supabase and running `migrate` created the **schema**
(empty tables) — confirmed via table introspection. It did **not** copy
across whatever data already exists in the local SQLite database
(`backend/rec_aids.sqlite3`) — departments, subjects, uploaded resources,
user accounts. That is a deliberate, separate action, not performed by this
phase. When ready:

- Re-run the seed commands (§8) against Supabase for catalogue data that's
  reproducible from `academics/curricula.py`, or
- Export/import real data with `python manage.py dumpdata` /
  `python manage.py loaddata` (not attempted or validated in this phase).

## 12. Configure frontend environment variables

The frontend does not talk to Supabase or to the database directly — it only
calls the Django API. Only set `VITE_API_BASE_URL` (in `frontend/.env`) if
the frontend will be deployed *separately* from the backend. Leave it unset
otherwise (same-origin deployment, or local dev with the Vite proxy).

`VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` placeholders exist in
`.env.example` for a *future* phase and are not read by any code today.

## 13. Start the frontend / 14. Start the backend

```bash
cd frontend && npm install && npm run dev      # or npm run build
cd backend && python manage.py runserver       # or the Dockerfile's gunicorn command
```

## 15. Verify the database connection / tables

```bash
python manage.py check_db
```

or Supabase dashboard → **Table Editor** — all 16 tables (including
`accounts_user`, `academics_department`, `resources_resource`,
`whatsapp_wacontact`) are visible there now.

## 16. Future Supabase Storage setup (not done in this phase)

Uploaded resource files still live on local disk. See
`docs/supabase-readiness-analysis.md` §13 for the unchanged migration path
(`REC_S3_*` variables, already read by `settings.py`, not activated).

## 17. Security precautions

- Never commit `backend/.env` or any `.env.*` file — `.gitignore` blocks
  these except `.env.example`. Verified throughout this phase.
- The real database password was never displayed, logged, or written to any
  file by Claude at any point in this project's setup.
- **A password containing an unencoded reserved character (`#`, `@`, etc.)
  can produce a Python traceback that echoes a fragment of it** — this
  happened once during this project's setup via an uncaught `ValueError`
  from `urllib.parse`, not from any code in this repository. If your own
  password ever appears in a terminal traceback, chat log, or shared
  document for any reason, treat it as exposed and rotate it from the
  Supabase dashboard, the same as any other leaked credential.
- Never put `REC_DATABASE_URL`, `REC_SECRET_KEY`, or any Supabase
  **service-role** key in a `VITE_` variable — anything with that prefix is
  bundled into the JavaScript shipped to every browser. Only an
  anon/publishable key is ever safe there, and only once a future phase adds
  a Supabase client to the frontend.
- `REC_SECRET_KEY` must be unique per environment.
- Set `REC_ALLOWED_HOSTS` to your real domain in production.

## 18. Deployment environment variables (summary)

```bash
REC_SECRET_KEY="<generated secret>"
REC_DEBUG="0"
REC_ALLOWED_HOSTS="your-domain.example.com"
REC_DATABASE_URL="postgresql://postgres.kuzjdhvyvsgiweayrarg:...@<pooler-host>:5432/postgres?sslmode=require"
```

Optional: `REC_MEDIA_ROOT`, `REC_S3_*` (Supabase Storage — §16),
`REC_CORS_ORIGINS` / `VITE_API_BASE_URL` (only if the frontend is hosted
separately).
