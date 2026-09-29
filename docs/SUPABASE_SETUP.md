# Connecting REC-Academic to Supabase

This is the exact procedure to connect this project to a real Supabase
project. It assumes the codebase is already at the state described in
`docs/supabase-readiness-analysis.md` — the database layer already supports
this with no code change; this document is configuration only.

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
2. Choose an organisation, a project name (e.g. `rec-academic`), a database
   password (generate a strong one — **save it now**, it's shown only once),
   and a region close to where the app will run.
3. Wait for provisioning to finish (a couple of minutes).

## 2. Find the Supabase database connection information

1. In the project dashboard: **Project Settings** (gear icon) → **Database**.
2. Under **Connection string**, pick the **URI** tab. You'll see two options:
   - **Session / direct connection** (port `5432`) — a normal Postgres
     connection. Use this for `manage.py migrate`, `createadmin`, and
     anything that needs a long-lived or full-featured connection.
   - **Transaction pooler** (port `6543`, PgBouncer) — better for a
     production web server with several workers, since it multiplexes many
     short connections. Use this for the *running app*, not for migrations
     or `pytest`.
3. Copy the URI. It looks like:
   ```
   postgresql://postgres.xxxxxxxxxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```

## 3. Obtain the PostgreSQL connection string

Take the URI from step 2, substitute your real database password for
`[YOUR-PASSWORD]`, and append `?sslmode=require` (Supabase requires TLS):

```
postgresql://postgres.xxxxxxxxxxxxxxxxxxxx:your-real-password@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require
```

If the password contains `@`, `/`, `:`, or other URL-special characters,
percent-encode it (the app decodes it back — see
`backend/config/settings.py`).

## 4. Configure `DATABASE_URL`

Create `backend/.env` (copy from the repo's `.env.example` — never commit
this file) and set:

```bash
REC_SECRET_KEY="<generate one — see step below>"
REC_DEBUG="0"
REC_ALLOWED_HOSTS="your-domain.example.com"

REC_DATABASE_URL="postgresql://postgres.xxxxxxxxxxxxxxxxxxxx:your-real-password@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require"
```

Generate `REC_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`REC_DATABASE_URL` takes priority over a bare `DATABASE_URL`, so set whichever
name your hosting platform expects — both are read.

**LOCAL DEVELOPMENT alternative:** leave `REC_DATABASE_URL` unset (or the
whole `.env` file absent) to keep using the local SQLite file — nothing else
needs to change to develop locally while a separate Supabase project exists
for staging/production.

## 5. Install required dependencies

The PostgreSQL driver is already in `backend/requirements.txt`
(`psycopg[binary]`). From the `backend/` directory:

```bash
python -m venv venv
venv\Scripts\activate            # Windows; source venv/bin/activate on Unix
pip install -r requirements.txt
```

If you already have a venv from before this phase, just re-run
`pip install -r requirements.txt` — it will pick up nothing new for the
database layer (only `python-dotenv`, `boto3`, `django-storages` if those
weren't already installed, which are needed for the optional storage step,
not for the database connection itself).

## 6. Run migrations

With `REC_DATABASE_URL` set to your Supabase connection string:

```bash
cd backend
python manage.py migrate
```

This creates every table (`accounts`, `academics`, `resources`, `whatsapp`,
`auth`, `contenttypes`, `token_blacklist`) in the Supabase database. Safe to
re-run — Django migrations are idempotent.

**Do not** run `flush`, `migrate <app> zero`, or drop the database — none of
that is part of this procedure and none of it was run against your existing
data by this phase.

## 7. Create an admin/superuser

```bash
python manage.py createadmin --email admin@yourcollege.edu --name "Your Name"
```

(Or `python manage.py createsuperuser` for Django's own prompt-based flow —
both work; `createadmin` is this project's own convenience command.)

Optionally seed the catalogue data:

```bash
python manage.py seed_departments
python manage.py seed_academics
```

## 8. Test the backend

```bash
python manage.py check
python manage.py check_db
python manage.py runserver
```

`check_db` (added by this phase) confirms the configured database is
reachable without printing your credentials — it reports only the engine
(`postgresql`) and database name (`postgres`). Expect:

```
Engine:   postgresql
Database: postgres
Connection OK — the database is reachable.
```

Then hit `http://127.0.0.1:8000/api/health/` — should return
`{"status": "ok", ...}`.

**Do not run `pytest` against the Supabase connection.** The test suite
creates and drops a throwaway test database on every run, which needs
`CREATEDB` privileges the pooled connection may not grant. Run tests locally
against SQLite (unset `REC_DATABASE_URL`) — this is a testing convenience,
not a limitation of the app.

## 9. Configure frontend environment variables

The frontend does not talk to Supabase or to the database directly — it only
calls the Django API. Usually nothing needs to change here. Only set
`VITE_API_BASE_URL` (in `frontend/.env`) if the frontend will be deployed
*separately* from the backend:

```bash
VITE_API_BASE_URL="https://api.yourcollege.edu"
```

Leave it unset for the normal same-origin deployment (Django serves the
built SPA itself — see the `Dockerfile`) or for local development (Vite
proxies `/api` to `127.0.0.1:8000`).

`VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` placeholders exist in
`.env.example` for a *future* phase (if the frontend is ever given direct
Supabase access, e.g. Supabase Auth). They are not read by any code today —
leave them unset.

## 10. Start the frontend

```bash
cd frontend
npm install
npm run dev          # development, http://localhost:5173
# or
npm run build         # production build into frontend/dist,
                       # served by Django itself (see Dockerfile)
```

## 11. Start the backend

Development:

```bash
cd backend
python manage.py runserver
```

Production (as the `Dockerfile` runs it):

```bash
python manage.py migrate --no-input
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4
```

## 12. Verify the database connection

```bash
python manage.py check_db
```

or, from the Supabase dashboard: **Table Editor** — the tables created by
step 6 (`accounts_user`, `academics_department`, `resources_resource`, etc.)
should be visible there once `migrate` has run.

## 13. Future Supabase Storage setup (not done in this phase)

Uploaded resource files still live on local disk today. To move them to
Supabase Storage later:

1. Supabase dashboard → **Storage** → **New bucket**. Keep it **private** —
   this app never generates public file URLs; every download goes through
   its own authenticated Django endpoint regardless of where the bytes
   physically live, and that must stay true.
2. **Project Settings** → **Storage** → **S3 Connection** for the access
   key, secret key, endpoint URL and region.
3. Add to `backend/.env`:
   ```bash
   REC_S3_ACCESS_KEY_ID="..."
   REC_S3_SECRET_ACCESS_KEY="..."
   REC_S3_BUCKET_NAME="resources"
   REC_S3_ENDPOINT_URL="https://xxxxxxxxxxxx.supabase.co/storage/v1/s3"
   REC_S3_REGION_NAME="us-east-1"
   ```
4. Restart the backend. New uploads go to the bucket automatically — no code
   change, since `settings.py` already switches `STORAGES["default"]` to the
   S3 backend whenever `REC_S3_ACCESS_KEY_ID` is set.
5. Existing local files are **not** moved automatically — that's a one-time
   data migration (copy each `Resource.file` into the new storage), to be
   done deliberately, separately, and only when you're ready.

## 14. Security precautions

- Never commit `backend/.env` or any `.env.*` file. `.gitignore` already
  blocks these except `.env.example` (`.env`, `.env.*`, `!.env.example`).
- Never put `REC_DATABASE_URL`, `REC_SECRET_KEY`, `REC_S3_SECRET_ACCESS_KEY`,
  or any Supabase **service-role** key in a `VITE_` variable or anywhere in
  frontend code — anything with the `VITE_` prefix is bundled into the
  JavaScript shipped to every browser.
- Only a Supabase **anon/publishable** key is ever safe in the frontend, and
  only once a future phase actually adds a Supabase client there.
- Rotate the Supabase database password immediately if it is ever pasted
  into a chat log, ticket, commit message, or shared document.
- `REC_SECRET_KEY` must be unique per environment and never reused between
  local development and Supabase/production — the app refuses to boot with
  `REC_DEBUG=0` and the default development key (see `settings.py`).
- Set `REC_ALLOWED_HOSTS` to your real domain in production — the wildcard
  default only applies when `REC_DEBUG=1`.

## 15. Deployment environment variables (summary)

Required for a Supabase/production deployment:

```bash
REC_SECRET_KEY="<generated secret>"
REC_DEBUG="0"
REC_ALLOWED_HOSTS="your-domain.example.com"
REC_DATABASE_URL="postgresql://...supabase.co:6543/postgres?sslmode=require"
```

Optional, as needed:

```bash
REC_MEDIA_ROOT=""                 # only if not using S3/Supabase Storage
REC_S3_ACCESS_KEY_ID=""           # Supabase Storage — see §13
REC_S3_SECRET_ACCESS_KEY=""
REC_S3_BUCKET_NAME="resources"
REC_S3_ENDPOINT_URL=""
REC_S3_REGION_NAME=""
REC_CORS_ORIGINS=""               # only if the frontend is hosted separately
VITE_API_BASE_URL=""              # only if the frontend is hosted separately
```

Every one of these is already read by the existing codebase — none of this
required a code change, only configuration.
