# goptant-blog

A minimal Medium-style blog starter built with:

- FastAPI for the backend API
- Next.js for the frontend
- PostgreSQL for blog data
- Redis and Celery for background jobs
- Docker Compose for local deployment
- GitHub Actions for CI verification

## Project structure

- `/backend` - FastAPI API and Celery worker
- `/frontend` - Next.js application
- `docker-compose.yml` - local stack for frontend, API, worker, Redis, and Postgres
- `.github/workflows/ci.yml` - CI workflow

## Quick start

1. Copy `.env.example` values into your shell if you want to run services outside Docker.
2. Start the full stack:

   ```bash
   docker compose up --build
   ```

3. Open:
   - Frontend: `http://localhost:3000`
   - API docs: `http://localhost:8000/docs`

## Local development

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
