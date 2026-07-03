from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()  # Initialize FastAPI application

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")


posts: list[dict] = [
    {
        "id": 1,
        "author": "Ava Johnson",
        "title": "Getting Started with Python",
        "content": "Python is a beginner-friendly language used for web development, automation, and data analysis.",
        "date_posted": "2026-06-20",
    },
    {
        "id": 2,
        "author": "Liam Carter",
        "title": "Understanding FastAPI Basics",
        "content": "FastAPI helps you build modern APIs quickly using Python type hints and automatic docs.",
        "date_posted": "2026-06-22",
    },
    {
        "id": 3,
        "author": "Noah Smith",
        "title": "Why Use Celery for Background Tasks",
        "content": "Celery lets your app handle long-running jobs in the background so API responses stay fast.",
        "date_posted": "2026-06-24",
    },
    {
        "id": 4,
        "author": "Emma Davis",
        "title": "Redis in Simple Terms",
        "content": "Redis is an in-memory data store often used for caching, queues, and fast key-value lookups.",
        "date_posted": "2026-06-26",
    },
    {
        "id": 5,
        "author": "Mason Brown",
        "title": "Intro to Docker Compose",
        "content": "Docker Compose allows you to run multiple services like API, database, and worker with one command.",
        "date_posted": "2026-06-28",
    },
]


# Decorators are used to define routes in FastAPI. The @app.get("/") decorator indicates that this function will handle GET requests to the root URL ("/").
# include_in_schema=False hides this route from the automatically generated API docs.
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "title": "Home",
            "heading": "Welcome to the Goptant Home Page",
            "paragraph": "This is a simple blog built with FastAPI and Jinja2.",
            "posts": posts,
        },  # context dictionary containing variables to be passed to the template, the keys in the dictionary correspond to variable names in the template, and the values are the data that will be rendered.
    )


@app.get("/api/posts")
def get_posts():
    return {"posts": posts}
