from ast import List

from app.errors import register_error_handlers
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from schemas import PostCreate, PostResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()  # Initialize FastAPI application
# register_error_handlers(app)  # Attach global error handlers

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


@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": "April 23, 2025",
    }
    posts.append(new_post)
    return new_post


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


@app.get(
    "/api/posts",
    response_model=list[PostResponse],
)
def get_posts():
    return posts


# Path parameter is used to capture the post_id from the URL. The function retrieves the post with the matching ID from the posts list and returns it as a JSON response. If no post is found, it returns a 404 error with a message.


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_single_post(post_id: int):
    post = next((post for post in posts if post["id"] == post_id), None)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )
    return post


@app.get("/posts/{post_id}", include_in_schema=False, name="get_single_post")
def get_single_post_page(request: Request, post_id: int):
    post = next((post for post in posts if post["id"] == post_id), None)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    title = post["title"][:50] + "..." if len(post["title"]) > 50 else post["title"]
    return templates.TemplateResponse(
        request, "post.html", {"post": post, "title": title}
    )


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
