# Daftar

Daftar is a production-ready MVP for small merchants in Palestine to manage customer debts and installments without paper notebooks or scattered WhatsApp messages.

The app is intentionally small: JWT login, customers, debts, auto-generated installments, partial/full payments, balance increases, customer credit profiles, paid/late tracking, a simple dashboard, reminder-ready overdue logic, and optional receipt image upload.

## Project Structure

```text
Daftar/
  backend/      Django REST Framework API
  frontend/     React + Vite + TailwindCSS app
  docs/         API, schema, and deployment documentation
```

## Stack

- Frontend: React, Vite, TailwindCSS, i18next
- Backend: Django REST Framework, Simple JWT
- Database: Neon PostgreSQL through `DATABASE_URL`
- Storage: Cloudinary for receipt uploads
- Hosting: Vercel frontend, Render backend

## Local Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Demo login:

```text
demo@daftar.local
demo123456
```

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Documentation

- [API endpoints](docs/API.md)
- [Database schema](docs/SCHEMA.md)
- [Admin panel](docs/ADMIN.md)
- [Deployment instructions](docs/DEPLOYMENT.md)
