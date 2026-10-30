#!/bin/sh
# HeritageConnect web container start-up script.
#
# 1. Apply database migrations (creates/updates PostGIS tables).
# 2. Collect static files into /app/staticfiles (shared with Nginx).
# 3. Start Gunicorn, the production WSGI server.
#
# "set -e" stops the container if any step fails, so problems are
# visible in "docker compose logs web" instead of being ignored.
set -e

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput --clear --verbosity 0

# Auto-reload on code changes only in development (DJANGO_DEBUG=True).
RELOAD_FLAG=""
case "$(echo "${DEBUG:-False}" | tr '[:upper:]' '[:lower:]')" in
    true|1|yes) RELOAD_FLAG="--reload"; echo "==> Development mode (auto-reload on)";;
    *) echo "==> Production mode";;
esac

echo "==> Starting Gunicorn"
exec gunicorn hello_map.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    $RELOAD_FLAG
