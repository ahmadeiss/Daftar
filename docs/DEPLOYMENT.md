# Deployment

## Environment Variables

### Backend

| Variable | Required | Description |
| --- | --- | --- |
| `SECRET_KEY` | yes | Long random Django secret |
| `DEBUG` | yes | `False` in production |
| `ALLOWED_HOSTS` | yes | Comma-separated hosts, including Render hostname |
| `CORS_ALLOWED_ORIGINS` | yes | Comma-separated frontend origins |
| `CSRF_TRUSTED_ORIGINS` | recommended | Comma-separated trusted HTTPS origins |
| `DATABASE_URL` | yes | Neon PostgreSQL connection string |
| `CLOUDINARY_CLOUD_NAME` | optional | Required for receipt uploads in production |
| `CLOUDINARY_API_KEY` | optional | Required for receipt uploads in production |
| `CLOUDINARY_API_SECRET` | optional | Required for receipt uploads in production |

### Frontend

| Variable | Required | Description |
| --- | --- | --- |
| `VITE_API_URL` | yes | Render API URL ending in `/api` |

Example:

```text
VITE_API_URL=https://daftar-api.onrender.com/api
```

## Neon PostgreSQL

1. Create a Neon project.
2. Copy the pooled PostgreSQL connection string.
3. Put it in Render as `DATABASE_URL`.
4. Keep `sslmode=require` in the URL.

Example:

```text
postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
```

## Cloudinary

1. Create a Cloudinary account.
2. Copy cloud name, API key, and API secret.
3. Add them to Render.

If these variables are missing locally, Django stores uploaded files in `backend/media/` so development still works.

## Render Backend

Option A: Blueprint

1. Push the repo to GitHub.
2. In Render, create a new Blueprint.
3. Select the repo.
4. Render will read `backend/render.yaml`.
5. Add the unsynced env vars in the Render dashboard.

Option B: Manual web service

```text
Root directory: backend
Runtime: Python
Build command: pip install -r requirements.txt && python manage.py collectstatic --noinput
Pre-deploy command: python manage.py migrate
Start command: gunicorn config.wsgi:application
```

After first deploy, optional demo data:

```bash
python manage.py seed_demo
```

## Vercel Frontend

1. Import the GitHub repo in Vercel.
2. Set root directory to `frontend`.
3. Set build command to `npm run build`.
4. Set output directory to `dist`.
5. Add `VITE_API_URL=https://your-render-service.onrender.com/api`.
6. Deploy.

## Production Checklist

- `DEBUG=False`
- Render hostname included in `ALLOWED_HOSTS`
- Vercel URL included in `CORS_ALLOWED_ORIGINS`
- Neon `DATABASE_URL` configured
- Cloudinary variables configured for receipt uploads
- `python manage.py migrate` completed
- Frontend points to the Render `/api` URL
