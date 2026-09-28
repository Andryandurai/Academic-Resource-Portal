# REC Academic Resource Portal

Academic resource portal for **Rajalakshmi Engineering College**. Students need
no account: the site opens on the dashboard for their department, where they
browse the curriculum semester by semester and open the unit notes and
examination material published for each subject. Faculty sign in at `/faculty`
to manage the subject catalogue and upload, replace and delete those resources.

All nineteen departments are selectable. Fourteen have had their syllabus
supplied — AI&DS, AI&ML, EEE, BME, Civil, CSE, ECE, CSD, ME, IT, Mechatronics,
Robotics and Automation, CSE (Cyber Security) and Food Technology — and the rest
show an empty state until theirs is added. Nothing assumes a department has
eight populated semesters or any particular subject count: curricula are data
(`academics/curricula.py`), not code.

> **Provenance.** Not an official Rajalakshmi Engineering College service. No
> official REC logo asset is bundled — the header uses a text mark, and the
> footer states this explicitly. Apply official branding only when authorised.

---

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19 + TypeScript, built with **Vite 6** |
| Routing | **React Router 7** |
| State | **Zustand 5** (session + UI only) |
| Styling | EchoSense design system (`styles/app.css`) with a retuned REC token palette |
| Icons | Inline SVG — no icon library |
| Backend | **Django 5.2** |
| API | **Django REST Framework 3.15** |
| Auth | **SimpleJWT** access/refresh with refresh-token blacklisting |
| Passwords | Django PBKDF2 (bcrypt kept only to read migrated hashes) |
| Validation | DRF serializers + `core/validators.py` |
| Files | Django `FileField` under `MEDIA_ROOT`, served by a public read-only endpoint |
| DB (dev) | SQLite |
| DB (prod) | PostgreSQL via `REC_DATABASE_URL` |
| Messaging | **WhatsApp Cloud API** (free service-conversation replies) + optional **Groq** free-tier LLM |
| Tests | **pytest + pytest-django** |
| Server | **Gunicorn** |
| Static | **WhiteNoise** (also serves the built SPA) |

---

## Run it

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows;  source venv/bin/activate on Unix
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_departments        # the 19 department records
python manage.py seed_academics          # semesters and subjects for those with a syllabus
python manage.py createadmin --email admin@college.edu --name "Dept Admin"
python manage.py runserver               # http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

The Vite dev server proxies `/api` to Django, so the browser sees one origin and
CORS is never load-bearing.

### Tests

```bash
cd backend && pytest
```

### Other commands

```bash
python manage.py verify_curriculum       # assert the DB matches the syllabus
python manage.py import_legacy --db ../prisma/dev.db   # one-off migration
python manage.py seed_academics --prune  # drop non-syllabus subjects (never deletes ones with files)
```

---

## Production

```bash
npm --prefix frontend ci && npm --prefix frontend run build
cd backend
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py seed_academics
gunicorn config.wsgi:application --chdir backend --bind 0.0.0.0:$PORT --workers 2 --threads 4
```

One service serves the API and the SPA: WhiteNoise answers `frontend/dist`, and
`config/spa.py` returns `index.html` for client-side routes so a deep link or a
refresh works instead of 404ing. Set `REC_SECRET_KEY`, `REC_DEBUG=0`,
`REC_ALLOWED_HOSTS` and `REC_DATABASE_URL`. See [.env.example](.env.example).

---

## API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/auth/login/` | Sign-in → access + refresh + user |
| `POST /api/auth/admin/login/` | Faculty sign-in; refuses to issue a token to a non-faculty account |
| `POST /api/auth/token/refresh/` | New access token |
| `GET /api/auth/me/` | Current user — re-reads the role from the database |
| `POST /api/auth/logout/` | Blacklists the refresh token |
| `GET /api/auth/users/` | Admin-only user overview |
| `GET /api/stats/` | Dashboard counters, computed live (open) |
| `GET /api/semesters/` | Semesters I–VIII with subject counts |
| `GET /api/subjects/` | `?search=&semester=&semester_number=&course_type=&category=` |
| `POST|PATCH|DELETE /api/subjects/…` | Faculty only |
| `GET /api/subjects/:id/resource-counts/` | All eight categories, zeros included |
| `GET /api/resources/` | `?subject=&semester=&resource_type=&search=&uploaded_from=&uploaded_to=` |
| `POST|PATCH|DELETE /api/resources/…` | Faculty only |
| `GET /api/resources/:id/download/` | Public file stream; `?inline=1` previews a PDF |
| `POST /api/whatsapp/webhook/` | Meta Cloud API delivery — see [backend/whatsapp/README.md](backend/whatsapp/README.md) |

Every read endpoint is open to anonymous visitors. Every write verb returns
**401** without a faculty token (and **403** for any non-faculty account),
regardless of what the client sends. Faculty accounts are created on the server
with `python manage.py createadmin`; there is no self-registration. Deleting a subject that still holds resources returns **409**.

---

## WhatsApp bot

Students never need the website or an app: they message one WhatsApp number
and the bot sends back notes, reference links or YouTube videos straight from
this same database — asking "which unit?" / "which kind?" when a message like
"data structures" is ambiguous, and answering directly when it isn't (e.g.
"unit 1 data structures notes"). Entirely free to run — see
[backend/whatsapp/README.md](backend/whatsapp/README.md) for the architecture,
free Meta Cloud API setup, and a dry-run mode that exercises the whole
conversation with `curl` before any WhatsApp account exists.

---

## Data model

```
Department ─┬─< Semester ──< Subject ──< Resource
            └─< User                        └── uploaded_by ──> User
```

- `Subject.course_code` is **nullable** — the syllabus publishes no code for the
  8 electives and one is never invented.
- `credits` is stored on every subject so GPA/CGPA can be added later.
- `course_type` is only `THEORY` or `LAB_ORIENTED_THEORY`; laboratory-only,
  non-credit, employability, internship and project courses are out of scope, so
  there is no third value for one to be filed under.
- Nothing limits a category to one file.
- `Resource.kind` is `NOTES` (a file), `REFERENCE` or `YOUTUBE` (a URL each) —
  mutually exclusive, enforced by a database check constraint as well as the
  serializer.

---

## Security

- Three enforcement points: DRF permission classes (`core/permissions.py`),
  serializer validation, and React Router guards. Only the first two protect
  data — the guards decide what is *rendered*.
- Uploads are validated on extension, declared media type, **file signature**
  and size before anything reaches disk. Stored names are server-generated
  UUIDs, so the uploader's filename never becomes a path.
- `MEDIA_ROOT` is outside `frontend/` and `STATIC_ROOT` and is not served
  statically; the download endpoint is public (students have no accounts) and
  sends `nosniff` + a restrictive CSP. Do not upload anything confidential.
- Login is throttled; unknown accounts and wrong passwords return identical
  responses so registered addresses cannot be enumerated.
- Logout blacklists the refresh token.

---

## Migration notes

Migrated from Next.js 16 + Prisma. `python manage.py import_legacy` carried the
two things the seed cannot regenerate: **user accounts**, with their bcryptjs
hashes rewritten into Django's `bcrypt$…` encoding so nobody had to reset a
password (Django re-hashes to PBKDF2 on next login — verified by test and by a
live login), and **uploaded resources** with their files.

The legacy SQLite file is copied to `.legacy-backup/` before the old stack is
removed.

### Removing the old stack

Verified first, then removed. Run from the repository root once you are happy
with the migrated data:

```powershell
Remove-Item -Recurse -Force src, prisma, storage, node_modules, .next,
  next.config.ts, next-env.d.ts, postcss.config.mjs, prisma.config.ts,
  package.json, package-lock.json, tsconfig.json, eslint.config.mjs, .env
```

Nothing in `backend/` or `frontend/` depends on any of it.

---

## Not implemented

- **GPA/CGPA calculation** — out of scope; credits are stored so it can be added.
- **Password reset by email** — needs an outbound mail service.
- **Django Channels / realtime** — not required; the ASGI entry point exists.
- **AI/ML and Three.js** — explicitly excluded.
