#!/bin/sh

# Stop startup if migrations or static file collection fail.
set -e

echo "==> Applying database migrations"
# Set up the database before accepting requests.
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput --clear --verbosity 0

# Only reload changed code when debug mode is enabled.
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
