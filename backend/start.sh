#!/usr/bin/env bash
set -e

echo "Running database setup (migrations + seed)..."
python manage.py setup_db

echo "Starting gunicorn..."
exec gunicorn config.wsgi:application
