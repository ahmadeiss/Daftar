import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(BASE_DIR))

print("=== Daftar Startup ===", flush=True)

print("Running migrations...", flush=True)
result = subprocess.run(
    [sys.executable, "manage.py", "migrate", "--verbosity", "2", "--noinput"],
    cwd=BASE_DIR,
)
print(f"Migrations exited with code {result.returncode}", flush=True)

print("Creating superuser if not exists...", flush=True)
subprocess.run(
    [sys.executable, "manage.py", "shell", "-c", (
        "from django.contrib.auth import get_user_model; "
        "User = get_user_model(); "
        "u, created = User.objects.get_or_create(username='admin@daftar.local', defaults={'email': 'admin@daftar.local', 'is_staff': True, 'is_superuser': True, 'first_name': 'Daftar Admin'}); "
        "created and (u.set_password('admin123456'), u.save(update_fields=['password'])); "
        "print(f'Superuser {'created' if created else 'already exists'}')"
    )],
    cwd=BASE_DIR,
)

print("=== Starting gunicorn ===", flush=True)
os.execvp("gunicorn", ["gunicorn", "config.wsgi:application", "--access-logfile", "-", "--error-logfile", "-"])
