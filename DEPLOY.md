## Deploying FastAPI + Next.js to Cloudflare with Docker CI/CD

### Critical Architecture Reality First

**Cloudflare does NOT run Docker containers.** This is the most important thing to understand before planning deployment. Cloudflare's platform is serverless/edge-based. Here's what each part of your stack means for deployment:

| Your Stack        | Cloudflare Support                             | Reality                          |
| ----------------- | ---------------------------------------------- | -------------------------------- |
| Next.js frontend  | ✅ Cloudflare Pages                            | Works natively                   |
| FastAPI (Python)  | ⚠️ Workers (experimental Python, very limited) | Docker won't run here            |
| PostgreSQL        | ❌ None                                        | Use Neon + Cloudflare Hyperdrive |
| Celery + Redis    | ❌ None                                        | Use Upstash Redis                |
| Docker containers | ❌ Not supported                               | Need a separate Docker host      |

---

## Recommended Architecture: Hybrid (Best for Your Stack)

```
┌──────────────────────────────────────────────────────────────┐
│                      CLOUDFLARE                              │
│  ┌─────────────────┐        ┌─────────────────────────────┐ │
│  │  Cloudflare     │        │   Cloudflare DNS/Proxy      │ │
│  │  Pages          │        │   yourapp.com →             │ │
│  │  (Next.js)      │        │   api.yourapp.com           │ │
│  └────────┬────────┘        └──────────────┬──────────────┘ │
└───────────┼──────────────────────────────── │ ───────────────┘
            │                                 │
            │ (API calls)                     │ (proxied)
            ▼                                 ▼
   ┌────────────────┐              ┌─────────────────────┐
   │   Next.js      │              │   Fly.io / Railway  │
   │   (Cloudflare  │   ─────────▶ │   (Docker)          │
   │   Pages CDN)   │              │   FastAPI + Celery  │
   └────────────────┘              │   Worker containers │
                                   └──────────┬──────────┘
                                              │
                        ┌─────────────────────┼──────────────┐
                        │                     │              │
                        ▼                     ▼              ▼
               ┌──────────────┐    ┌──────────────┐  ┌──────────┐
               │ Neon.tech    │    │ Upstash      │  │ Cloudflare│
               │ (Serverless  │    │ (Serverless  │  │ R2        │
               │  PostgreSQL) │    │  Redis)      │  │ (media)   │
               └──────────────┘    └──────────────┘  └──────────┘
```

This is the architecture I'll build the CI/CD pipeline for. It:

- Keeps your Docker containers on [Fly.io](https://fly.io) (Docker-native, excellent free tier)
- Uses Cloudflare Pages for Next.js (free, global CDN)
- Uses managed serverless databases (no server to manage)
- Uses Cloudflare as DNS/proxy in front of everything

---

## Step-by-Step: Secrets and Project Setup

### Step 1 — Services to Create (Before Any Code)

1. **[Neon.tech](https://neon.tech)** — Free PostgreSQL. Copy the `postgresql+asyncpg://...` connection string.
2. **[Upstash.com](https://upstash.com)** — Free Redis. Copy the `rediss://...` connection string.
3. **[Fly.io](https://fly.io)** — Free Docker hosting. Install `flyctl` and run `fly auth login`.
4. **[Cloudflare](https://cloudflare.com)** — Free account. Get your Account ID and create an API token.

### Step 2 — Add GitHub Actions Secrets

In your GitHub repo → Settings → Secrets and Variables → Actions:

```
# Fly.io
FLY_API_TOKEN          = <from: fly auth token>

# Cloudflare
CLOUDFLARE_API_TOKEN   = <Cloudflare API token with Pages:Edit permission>
CLOUDFLARE_ACCOUNT_ID  = <your account ID from Cloudflare dashboard>

# Database
DATABASE_URL           = postgresql+asyncpg://user:pass@neon.host/db?sslmode=require

# Redis
REDIS_URL              = rediss://:token@upstash-host:port

# App
FRONTEND_URL           = https://yourapp.pages.dev
```

---

## Step 3 — Fix Your Backend database.py for Production

Your current database.py hardcodes SQLite. The docker-compose.yml uses PostgreSQL. You need environment-aware configuration:

```python
# backend/database.py — production-ready version
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    settings.database_url,          # reads from DATABASE_URL env var
    echo=False,
    pool_pre_ping=True,             # detects stale connections
    pool_size=5,                    # max connections in pool
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
```

The `settings.database_url` comes from your `app/config.py` which already reads from env vars — this will pick up `DATABASE_URL` from the environment in production automatically.

---

## Step 4 — Fly.io Configuration Files

### `backend/fly.toml` — FastAPI App

```toml
# fly.toml — Defines how Fly.io runs your FastAPI Docker container
app = "goptant-blog-api"        # must match your Fly app name
primary_region = "lhr"          # London — pick closest to your users

[build]
  dockerfile = "Dockerfile"     # uses your existing Dockerfile

[env]
  PORT = "8000"
  PYTHONUNBUFFERED = "1"

# Secrets like DATABASE_URL and REDIS_URL are set via `fly secrets set`
# NOT here — never put secrets in fly.toml (it's committed to git)

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true           # redirects HTTP → HTTPS automatically

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [services.concurrency]
    type = "connections"
    hard_limit = 100             # max concurrent connections before spinning up new instance
    soft_limit = 80

  [[services.tcp_checks]]
    interval = "15s"
    timeout = "2s"

[[vm]]
  memory = "256mb"               # free tier: 256MB RAM
  cpu_kind = "shared"
  cpus = 1
```

### `backend/fly.worker.toml` — Celery Worker (Separate Fly App)

```toml
# fly.worker.toml — Separate Fly app just for Celery workers
app = "goptant-blog-worker"
primary_region = "lhr"

[build]
  dockerfile = "Dockerfile"

# Override the CMD from the Dockerfile to run Celery instead of uvicorn
[processes]
  worker = "celery -A app.celery_app.celery_app worker --loglevel=info --concurrency=2"

[env]
  PYTHONUNBUFFERED = "1"

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1
```

---

## Step 5 — Production Dockerfile (Backend)

Your current Dockerfile only copies `./app`. Your main.py is in the backend root, as are `models.py`, `schemas.py`, database.py, and `static/`/`templates/`. Fix it:

```dockerfile
# backend/Dockerfile — production-ready
FROM python:3.12-slim

WORKDIR /app

# Security: don't run as root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL backend files (not just ./app)
COPY app ./app
COPY main.py models.py schemas.py database.py ./
COPY static ./static
COPY templates ./templates
COPY media ./media

# Own files by non-root user
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Use main:app (the root-level main.py), not app.main:app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

> **Note:** Your docker-compose.yml currently points to `app.main:app` but your production main.py is at the root level. You need to reconcile this — the root `main.py` is the one with all the routes.

---

## Step 6 — Frontend Environment for Production

```dockerfile
# frontend/Dockerfile — production-ready (multi-stage)
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci                      # ci is faster and stricter than install

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Non-root user for security
RUN addgroup --system nextjs && adduser --system --ingroup nextjs nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

For Cloudflare Pages, the Next.js frontend is deployed directly from source — **not via Docker**. Cloudflare Pages builds it for you.

---

## Step 7 — The GitHub Actions CI/CD Pipeline

This is the core. Create this file:

```yaml
# .github/workflows/deploy.yml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main # deploys to production
      - development # deploys to staging
  pull_request:
    branches:
      - main
      - development # runs tests only on PRs, no deploy

jobs:
  # ─────────────────────────────────────────────────────────────
  # JOB 1: Test the Backend
  # Runs on every push and PR — fast feedback before deploying
  # ─────────────────────────────────────────────────────────────
  test-backend:
    name: Backend Tests
    runs-on: ubuntu-latest

    services:
      # Spin up a real PostgreSQL container for tests
      # GitHub Actions supports Docker services natively
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        # Downloads your repo into the runner

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip' # caches pip packages between runs — faster CI

      - name: Install dependencies
        working-directory: ./backend
        run: pip install -r requirements.txt

      - name: Run tests
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          # Replace with your test command when you add tests
          python -m pytest tests/ -v --tb=short || echo "No tests yet"

  # ─────────────────────────────────────────────────────────────
  # JOB 2: Lint & Type Check Frontend
  # ─────────────────────────────────────────────────────────────
  test-frontend:
    name: Frontend Lint
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Lint
        working-directory: ./frontend
        run: npm run lint

  # ─────────────────────────────────────────────────────────────
  # JOB 3: Deploy FastAPI to Fly.io
  # Only runs on push to main/development — NOT on PRs
  # Waits for both test jobs to pass first (needs:)
  # ─────────────────────────────────────────────────────────────
  deploy-backend:
    name: Deploy FastAPI (Fly.io)
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend] # gates: both tests must pass
    if: github.event_name == 'push' # skip on PRs

    # Environment-specific config (main → production, dev → staging)
    environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}

    steps:
      - uses: actions/checkout@v4

      - name: Install Fly CLI
        uses: superfly/flyctl-actions/setup-flyctl@master
        # Official Fly.io GitHub Action — installs flyctl on the runner

      - name: Deploy API to Fly.io
        working-directory: ./backend
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
        run: |
          # flyctl deploy:
          #   --config = which fly.toml to use
          #   --dockerfile = which Dockerfile to build
          #   --remote-only = builds the Docker image on Fly's servers (no local Docker needed)
          #   --wait-timeout = how long to wait for the deploy to succeed
          flyctl deploy \
            --config fly.toml \
            --dockerfile Dockerfile \
            --remote-only \
            --wait-timeout 120

      - name: Deploy Celery Worker to Fly.io
        working-directory: ./backend
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
        run: |
          flyctl deploy \
            --config fly.worker.toml \
            --dockerfile Dockerfile \
            --remote-only \
            --wait-timeout 120

  # ─────────────────────────────────────────────────────────────
  # JOB 4: Deploy Next.js to Cloudflare Pages
  # Cloudflare Pages builds Next.js natively — no Docker involved
  # ─────────────────────────────────────────────────────────────
  deploy-frontend:
    name: Deploy Next.js (Cloudflare Pages)
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    if: github.event_name == 'push'

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Build Next.js
        working-directory: ./frontend
        env:
          # Points the frontend at your deployed Fly.io API URL
          NEXT_PUBLIC_API_URL: ${{ github.ref == 'refs/heads/main' && 'https://goptant-blog-api.fly.dev' || 'https://goptant-blog-api-staging.fly.dev' }}
        run: npm run build

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        # Official Cloudflare GitHub Action
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy .next --project-name=goptant-blog --branch=${{ github.ref_name }}
          # --project-name = your Cloudflare Pages project name
          # --branch = the git branch (main → production URL, others → preview URLs)
          workingDirectory: frontend
```

---

## How Everything Fits Together — Flow Diagram

```
Developer pushes code to GitHub
            │
            ▼
┌─────────────────────────────────────┐
│        GitHub Actions Triggered     │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ test-backend  │  │test-frontend│ │
│  │ (pytest +     │  │ (eslint)    │ │
│  │  postgres svc)│  │             │ │
│  └──────┬───────┘  └──────┬──────┘ │
│         │   Both must pass │        │
│         └────────┬─────────┘        │
│                  ▼                  │
│  ┌───────────────────────────────┐  │
│  │  if push to main/development  │  │
│  │  ┌─────────────┐ ┌─────────┐ │  │
│  │  │deploy-backend│ │deploy-  │ │  │
│  │  │(flyctl)      │ │frontend │ │  │
│  │  │              │ │(wrangler│ │  │
│  │  │ API + Worker │ │ Pages)  │ │  │
│  │  └─────────────┘ └─────────┘ │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
            │                │
            ▼                ▼
   Fly.io (FastAPI)    Cloudflare Pages
   Docker container    (Next.js global CDN)
            │
            ├── Neon PostgreSQL
            └── Upstash Redis
```

**What each piece does:**

- `actions/checkout@v4` — Copies your repo into the GitHub Actions VM
- `cache: "pip"` / `cache: "npm"` — Saves installed packages between runs, cuts CI time by ~60%
- `services: postgres:` — GitHub Actions spins up a Docker sidecar — your tests get a real DB
- `needs:` — Dependency graph: deploy jobs won't start until tests pass
- `if: github.event_name == 'push'` — PRs only test, never deploy (safe)
- `environment:` — GitHub Environments let you require manual approval for production deploys
- `--remote-only` — Fly.io builds your Docker image on their infrastructure, no local Docker daemon needed in CI

---

## First-Time Setup Commands

Run these once on your local machine to create the Fly.io apps:

```bash
# Install flyctl
# https://fly.io/docs/hands-on/install-flyctl/

cd backend

# Create the API app (first time only)
flyctl apps create goptant-blog-api

# Set production secrets on Fly.io (these are injected as env vars into the container)
flyctl secrets set \
  DATABASE_URL="postgresql+asyncpg://..." \
  REDIS_URL="rediss://..." \
  FRONTEND_URL="https://goptant-blog.pages.dev" \
  --app goptant-blog-api

# Create the worker app (first time only)
flyctl apps create goptant-blog-worker
flyctl secrets set \
  DATABASE_URL="postgresql+asyncpg://..." \
  REDIS_URL="rediss://..." \
  --app goptant-blog-worker

# Create Cloudflare Pages project (first time only — or do it in the dashboard)
npx wrangler pages project create goptant-blog
```

---

## Cost Implications

### Free Tier (Sufficient to start)

| Service               | Free Tier                                              | Paid After                     |
| --------------------- | ------------------------------------------------------ | ------------------------------ |
| **Cloudflare Pages**  | Unlimited sites, 500 builds/month, unlimited bandwidth | $5/month for more builds       |
| **Fly.io**            | 3 shared-CPU VMs with 256MB RAM free                   | ~$1.94/month per additional VM |
| **Neon (PostgreSQL)** | 0.5 GB storage, 1 compute unit                         | $19/month for more             |
| **Upstash (Redis)**   | 10,000 commands/day, 256MB                             | Pay per 100K commands          |
| **GitHub Actions**    | 2,000 minutes/month (public repos: unlimited)          | $0.008/minute                  |
| **Cloudflare DNS**    | Free forever                                           | -                              |

**Total for this blog at low traffic: $0/month** (comfortably within free tiers)

### Production Scale Cost (estimated)

| Scale                          | Monthly Cost |
| ------------------------------ | ------------ |
| Small blog (< 10K users/month) | **$0–5**     |
| Medium (10K–100K users/month)  | **$20–50**   |
| Large (100K+ users/month)      | **$50–200**  |

### Cost vs. Alternatives

| Platform                   | Monthly Cost | Docker Support | Notes                       |
| -------------------------- | ------------ | -------------- | --------------------------- |
| **This architecture**      | $0–5         | ✅ Fly.io      | Best value                  |
| VPS (DigitalOcean/Hetzner) | $6–12        | ✅ Full        | You manage everything       |
| Railway                    | $5+          | ✅             | Simple but pricier          |
| AWS ECS/Fargate            | $30–100+     | ✅             | Enterprise, complex         |
| Render                     | $7+          | ✅             | Easy but expensive at scale |

### Render Cost Breakdown (Full Stack)

Render is a simpler alternative to the Fly.io + Cloudflare hybrid above — everything lives in one platform. The trade-off is higher cost once you move off the free tier.

**Per-service pricing (as of 2025):**

| Service               | Instance Type | Price/month | RAM    | CPU | Notes                                                |
| --------------------- | ------------- | ----------- | ------ | --- | ---------------------------------------------------- |
| **FastAPI (Web)**     | Free          | $0          | 512 MB | 0.1 | Spins down after 15 min inactivity (~30s cold start) |
| **FastAPI (Web)**     | Starter       | $7          | 512 MB | 0.5 | Always on, no spin-down                              |
| **FastAPI (Web)**     | Standard      | $25         | 2 GB   | 1   | Recommended for production                           |
| **Celery Worker**     | Starter       | $7          | 512 MB | 0.5 | Background workers have no free tier                 |
| **Celery Worker**     | Standard      | $25         | 2 GB   | 1   |                                                      |
| **Next.js (Static)**  | Static Site   | $0          | —      | —   | Free forever via Render's CDN                        |
| **PostgreSQL**        | Free          | $0          | 256 MB | 0.1 | **30-day expiry** — deleted after 30 days            |
| **PostgreSQL**        | Basic-256mb   | $6          | 256 MB | 0.1 | Persistent, no PITR                                  |
| **PostgreSQL**        | Basic-1gb     | $19         | 1 GB   | 0.5 | Recommended for production                           |
| **Redis (Key Value)** | Free          | $0          | 25 MB  | —   | No persistence (data lost on restart)                |
| **Redis (Key Value)** | Starter       | $10         | 256 MB | —   | Persistent, 250 connections                          |

**Realistic cost scenarios for this blog:**

| Scenario                         | Services                                                                   | Monthly Cost |
| -------------------------------- | -------------------------------------------------------------------------- | ------------ |
| **Experimenting (free tier)**    | Free web + free PostgreSQL\* + free Redis + free static                    | **$0**       |
| **Minimum always-on**            | Starter web + Basic-256mb DB + Starter Redis + free static                 | **~$23**     |
| **Recommended small production** | Standard web + Starter worker + Basic-1gb DB + Starter Redis + free static | **~$81**     |

> ⚠️ **Free PostgreSQL expires after 30 days.** Render deletes the database automatically. It is only suitable for experiments.

> ⚠️ **Free web services spin down after 15 minutes of inactivity.** The first request after idle takes ~30 seconds to respond — bad for a blog with real users.

**Render vs. this guide's architecture (Fly.io + Cloudflare):**

| Factor                | Render                           | Fly.io + Cloudflare (this guide) |
| --------------------- | -------------------------------- | -------------------------------- |
| Minimum paid cost     | ~$23/month                       | ~$0–5/month                      |
| Setup complexity      | Low (single platform)            | Medium (multiple services)       |
| Docker support        | ✅ Native                        | ✅ Native                        |
| Static site CDN       | ✅ Included                      | ✅ Cloudflare Pages (faster)     |
| Managed PostgreSQL    | ✅ Included                      | Via Neon.tech (separate)         |
| Managed Redis         | ✅ Included                      | Via Upstash (separate)           |
| Free tier longevity   | PostgreSQL expires after 30 days | Neon free tier is permanent      |
| Celery worker pricing | $7+/month (no free tier)         | Included in Fly.io free VMs      |

Render is a good choice if you value having **everything in one dashboard** and are willing to pay ~$23/month from the start. For a blog project on a budget, the Fly.io + Cloudflare hybrid in this guide is significantly cheaper.

---

## Best Practices Summary

**Security:**

- Never commit `.env` files — use GitHub Secrets + Fly.io `secrets set`
- Non-root user in both Dockerfiles (already shown above)
- Use `--remote-only` so your local machine never needs Docker Hub credentials
- Set `force_https = true` in `fly.toml` (already shown)

**Reliability:**

- `pool_pre_ping=True` in SQLAlchemy engine — detects dropped DB connections
- `--wait-timeout 120` in flyctl — CI fails loudly if deploy hangs
- `services.tcp_checks` in `fly.toml` — Fly health-checks your container before routing traffic to it
- Use `npm ci` (not `npm install`) in CI — deterministic installs from `package-lock.json`

**Performance:**

- Multi-stage Docker build for frontend (shown above) — removes dev dependencies, shrinks image ~3x
- `cache: "pip"` / `cache: "npm"` — cuts CI time significantly
- `--workers 2` in uvicorn — uses both CPUs on the free VM

**Your immediate action items:**

1. Note that database.py currently hardcodes SQLite — update it for PostgreSQL in production (shown in Step 3)
2. The `CMD` in your current Dockerfile points to `app.main:app` but production routes are in the root main.py — decide which is the entrypoint
3. Add `output: 'standalone'` to next.config.mjs for the optimized Docker build

Created 4 todos
