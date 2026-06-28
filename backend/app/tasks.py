from app.celery_app import celery_app


@celery_app.task(name="app.tasks.summarize_post")
def summarize_post(title: str, body: str) -> dict:
    word_count = len(body.split())
    reading_time_minutes = max(1, (word_count + 199) // 200)
    excerpt = body[:140].rstrip()
    if len(body) > 140:
        excerpt = f"{excerpt}..."

    return {
        "title": title,
        "excerpt": excerpt,
        "reading_time_minutes": reading_time_minutes,
    }
