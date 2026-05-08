#!/usr/bin/env bash
set -e

echo "=== Daftar Startup ==="
echo "Running migrations..."
python manage.py migrate --verbosity 2 --noinput 2>&1 | tee /tmp/migrate.log

echo "Creating superuser if not exists..."
python manage.py shell << 'EOF' 2>&1 | tee /tmp/superuser.log
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="admin@daftar.local").exists():
    User.objects.create_superuser("admin@daftar.local", "admin@daftar.local", "admin123456")
    print("Superuser admin@daftar.local created.")
else:
    print("Superuser already exists.")
EOF

echo "Seeding demo data..."
python manage.py seed_demo 2>&1 | tee /tmp/seed.log || echo "Seed failed, continuing..."

echo "=== Startup complete, starting gunicorn ==="
exec gunicorn config.wsgi:application --access-logfile - --error-logfile -
