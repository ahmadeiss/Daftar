#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser if not exists..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="admin@daftar.local").exists():
    User.objects.create_superuser("admin@daftar.local", "admin@daftar.local", "admin123456")
    print("Superuser admin@daftar.local created.")
else:
    print("Superuser already exists.")
EOF

echo "Seeding demo data..."
python manage.py seed_demo

echo "Starting gunicorn..."
exec gunicorn config.wsgi:application
