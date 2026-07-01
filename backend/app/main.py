from __future__ import annotations

from contextlib import asynccontextmanager

from app.celery_app import celery_app
from app.config import settings
from app.db import init_database, list_posts
from celery.result import AsyncResult
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class PostResponse(BaseModel):
    id: int
    title: str
    summary: str
    body: str
    author: str
    published_at: str


class TaskQueuedResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/posts", response_model=list[PostResponse])
def get_posts() -> list[PostResponse]:
    return [
        PostResponse(**{**post, "published_at": post["published_at"].isoformat()})
        for post in list_posts()
    ]


@app.post("/api/tasks/summarize-latest", response_model=TaskQueuedResponse)
def queue_latest_post_summary() -> TaskQueuedResponse:
    posts = list_posts()
    if posts:
        latest_post = posts[0]
        title = latest_post["title"]
        body = latest_post["body"]
    else:
        title = "Untitled draft"
        body = "Draft content"

    task = celery_app.send_task("app.tasks.summarize_post", args=[title, body])
    return TaskQueuedResponse(task_id=task.id, status="queued")


@app.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    result = AsyncResult(task_id, app=celery_app)
    payload = (
        result.result
        if result.successful() and isinstance(result.result, dict)
        else None
    )
    return TaskStatusResponse(
        task_id=task_id, status=result.status.lower(), result=payload
    )
