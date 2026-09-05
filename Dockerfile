# Two stages: build the Vite frontend with Node, then run Django with only
# Python in the final image. Render's native Python runtime has no Node, and
# the SPA needs a real build step (tsc + vite) — so this project is Docker on
# Render even though there is nothing else container-specific about it.

FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim AS backend
WORKDIR /app

# psycopg[binary] ships its own libpq, so no system Postgres client library is
# needed here.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

WORKDIR /app/backend
# Collected at build time, not on every boot: STATIC_ROOT does not depend on
# any runtime secret, so there is no reason to redo it on every restart.
RUN REC_SECRET_KEY=build-time-placeholder REC_DEBUG=1 python manage.py collectstatic --no-input

EXPOSE 8000
# Migrations run on boot rather than as a separate release step because
# Render's free tier has no such step; both are idempotent, so a redeploy
# with no schema change is a fast no-op.
CMD python manage.py migrate --no-input && \
    gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4
