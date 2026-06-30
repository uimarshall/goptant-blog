## FastAPI Best Practices: Development to Production

---

### 1. Code Modularisation

**Current state:** All Pydantic models (`PostResponse`, `TaskQueuedResponse`, etc.) and all route handlers live in main.py. This works now, but will become unmanageable as the app grows.

**Target structure:**

```
app/
├── main.py              # App factory only — no routes, no models
├── config.py            # ✅ Already correct
├── db.py                # ✅ Fine for now, consider repositories pattern later
├── celery_app.py        # ✅ Already isolated
├── tasks.py             # ✅ Already isolated
├── schemas/             # Pydantic models (request/response shapes)
│   ├── __init__.py
│   ├── post.py          # PostResponse
│   └── task.py          # TaskQueuedResponse, TaskStatusResponse
├── routers/             # One file per domain
│   ├── __init__.py
│   ├── posts.py         # GET /api/posts
│   └── tasks.py         # POST /api/tasks/..., GET /api/tasks/{id}
└── services/            # Business logic, separated from HTTP layer
    ├── __init__.py
    └── post_service.py  # list_posts logic, summarization dispatch
```

**How routers plug in to main.py:**

```python
# main.py (app factory only)
from app.routers import posts, tasks

app.include_router(posts.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
```

---

### 2. Configuration & Secrets

**Current state:** config.py uses `pydantic-settings` — this is already best practice.

**Extend it for production:**

```python
class Settings(BaseSettings):
    app_name: str = "Goptant Blog API"
    environment: Literal["development", "staging", "production"] = "development"
    database_url: str
    redis_url: str
    frontend_url: str
    debug: bool = False                  # Never True in production
    secret_key: str                      # For JWT signing
    allowed_hosts: list[str] = ["*"]    # Lock this down in production
```

Rules:

- **Never** hardcode secrets — always pull from environment variables or a secrets manager (AWS Secrets Manager, Azure Key Vault)
- `database_url` and `redis_url` should have **no defaults** in production — fail fast if misconfigured
- Use separate `.env.development`, `.env.staging`, `.env.production` files

---

### 3. Database: Connection Pooling

**Current state:** db.py calls `connect()` per request — this opens and closes a new TCP connection on every API call. Under load, this exhausts PostgreSQL's connection limit.

**Fix — use a connection pool:**

```python
from psycopg_pool import ConnectionPool

pool: ConnectionPool | None = None

def init_pool():
    global pool
    pool = ConnectionPool(
        settings.database_url,
        min_size=2,
        max_size=10,
        kwargs={"row_factory": dict_row},
    )

def get_connection():
    return pool.connection()  # borrows from pool, returns on exit
```

Initialise the pool in the `lifespan` context and close it on shutdown:

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    init_pool()
    init_database()
    yield
    pool.close()
```

---

### 4. Async vs. Sync Routes

FastAPI supports both. The choice has a real performance impact:

| Route type   | When to use                                                             | Effect                                         |
| ------------ | ----------------------------------------------------------------------- | ---------------------------------------------- |
| `def` (sync) | CPU-bound work, or blocking libraries (like `psycopg` sync)             | FastAPI runs it in a thread pool automatically |
| `async def`  | True async I/O — `httpx`, async DB drivers (`asyncpg`, `psycopg` async) | Runs on the event loop — most efficient        |

**Current state:** All routes in main.py use `def` (sync). That's correct given `psycopg` (sync) is used. If you switch to `psycopg` async or `asyncpg`, flip the routes to `async def`.

**Never do this** — it blocks the event loop:

```python
async def get_posts():
    time.sleep(1)   # blocks everything — use asyncio.sleep or a thread
```

---

### 5. Dependency Injection

FastAPI's `Depends()` system is the idiomatic way to share resources (DB connections, auth, pagination params) across routes without globals.

```python
from fastapi import Depends

def get_db():
    with pool.connection() as conn:
        yield conn   # automatically returned to pool after request

@router.get("/posts")
def get_posts(db = Depends(get_db)):
    ...
```

Benefits:

- Testable — swap `get_db` for a test DB in tests
- No global state leaking between requests
- Works with auth: `Depends(get_current_user)` applies to any route

---

### 6. Error Handling

**Never let raw exceptions reach the client.** Define custom exception handlers:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class PostNotFoundError(Exception):
    def __init__(self, post_id: int):
        self.post_id = post_id

@app.exception_handler(PostNotFoundError)
async def post_not_found_handler(request: Request, exc: PostNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": f"Post {exc.post_id} not found"},
    )
```

This keeps error shapes consistent and prevents stack traces leaking in production.

---

### 7. Structured Logging

`print()` is not production logging. Use structured JSON logs so tools like Datadog, CloudWatch, or Loki can parse them:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        })
```

Or use **`structlog`** — the de-facto standard for structured Python logging.

---

### 8. Performance: Caching

db.py hits PostgreSQL on every `GET /api/posts` request. For a blog, posts don't change every second — cache aggressively.

**Two approaches:**

```python
# Option 1: FastAPI response-level cache headers
@router.get("/posts", response_model=list[PostResponse])
def get_posts(response: Response):
    response.headers["Cache-Control"] = "public, max-age=60"
    return ...

# Option 2: Redis cache (project already has Redis via Celery)
import redis
cache = redis.from_url(settings.redis_url)

def get_posts_cached():
    cached = cache.get("posts")
    if cached:
        return json.loads(cached)
    posts = list_posts()
    cache.setex("posts", 60, json.dumps(posts, default=str))
    return posts
```

---

### 9. Security Hardening

| Concern                            | Fix                                                                    |
| ---------------------------------- | ---------------------------------------------------------------------- |
| CORS `allow_origins=["*"]` in prod | Lock to specific domains — already done via `settings.frontend_url` ✅ |
| No rate limiting                   | Add `slowapi` middleware                                               |
| No request size limit              | Set `uvicorn --limit-concurrency` and body size limits                 |
| Sensitive data in logs             | Scrub passwords, tokens from log output                                |
| SQL injection                      | Use parameterised queries (psycopg does this by default with `%s`) ✅  |

---

### 10. Production Deployment

```
                    ┌─────────────┐
   Browser  ───────▶│   Nginx     │  (TLS termination, rate limiting)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Uvicorn    │  (multiple workers via Gunicorn)
                    │  workers    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          FastAPI      PostgreSQL     Redis
           app            (pool)    (Celery broker
                                     + cache)
```

**Run command for production (never use `uvicorn` alone):**

```bash
gunicorn app.main:app \
  --workers 4 \              # (2 × CPU cores) + 1
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 30 \
  --access-logfile -
```

---

### Summary: What to Fix in This Project Now vs. Later

| Priority        | Action                                              |
| --------------- | --------------------------------------------------- |
| **Now**         | Move models to `schemas/`, routes to `routers/`     |
| **Now**         | Add connection pooling to db.py                     |
| **Now**         | Add structured logging                              |
| **Soon**        | Add `Depends()` for DB and auth                     |
| **Soon**        | Add Redis caching for `list_posts`                  |
| **Before prod** | Add exception handlers                              |
| **Before prod** | Switch from `uvicorn` to `gunicorn + UvicornWorker` |
| **Before prod** | Add rate limiting via `slowapi`                     |
