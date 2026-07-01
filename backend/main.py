from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()  # Initialize FastAPI application


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
@app.get("/")
def home():
    return {"message": "Hello from backend server!"}


@app.get("/api/posts")
def get_posts():
    return {"posts": posts}


# The @app.get("/api/html") decorator indicates that this function will handle GET requests to the "/api/html" URL. The response_class=HTMLResponse argument tells FastAPI this endpoint returns HTML (not JSON).

# The include_in_schema=False argument means this endpoint won't appear in the automatically generated API docs.


@app.get("/api/html", response_class=HTMLResponse, include_in_schema=False)
def get_post_html():
    html_content = """
    <html>
        <head>
            <title>Blog Posts</title>
        </head>
        <body>
            <h1>Blog Posts</h1>
            <ul>
                {}
            </ul>
        </body>
    </html>
    """.format(
        "".join(
            f"<li><strong>{post['title']}</strong> by {post['author']} on {post['date_posted']}</li>"
            for post in posts
        )
    )
    return HTMLResponse(content=html_content, status_code=200)


'''

1. `@app.get("/api/html", response_class=HTMLResponse)`  
This is a FastAPI route decorator.  
It means: when a browser sends a GET request to `/api/html`, run the function below.  
`response_class=HTMLResponse` tells FastAPI this endpoint returns HTML (not JSON).

2. `def get_post_html():`  
Defines the function that handles that request.

3. `html_content = """`  
Starts a multi-line Python string. This string will contain your full HTML page.

4. `<html>`  
Root HTML tag.

5. `<head>`  
Start of metadata section of the page.

6. `<title>Blog Posts</title>`  
Sets browser tab title to “Blog Posts”.

7. `</head>`  
Ends head section.

8. `<body>`  
Starts visible page content.

9. `<h1>Blog Posts</h1>`  
Main heading displayed on page.

10. `<ul>`  
Starts an unordered list.

11. `{}`  
A placeholder inside the string.  
This will be replaced by `.format(...)` with generated `<li>` items.

12. `</ul>`  
Ends unordered list.

13. `</body>`  
Ends visible content area.

14. `</html>`  
Ends HTML document.

15. `""".format(`  
Closes the multi-line string and immediately calls `.format(...)` to fill placeholders.  
Since there is one `{}`, you pass one value to `.format(...)`.

16. `"".join(`  
Creates one big string by joining many small strings together (each small string is one `<li>`).

17. `f"<li><strong>{post['title']}</strong> by {post['author']} on {post['date_posted']}</li>"`  
This is an f-string template for one list item.  
For each post, it builds HTML like:  
`<li><strong>Title</strong> by Author on Date</li>`  
`<strong>` makes the title bold.

18. `for post in posts`  
This is a generator expression iterating through every dictionary in `posts`.

19. `)`  
Ends `join(...)`.

20. `)`  
Ends `format(...)`.  
At this point, `html_content` is a complete HTML page string with all posts inserted.

21. `return HTMLResponse(content=html_content, status_code=200)`  
Returns the HTML to the client.  
`status_code=200` means “OK/success”.

Quick mental model:
1. Build an HTML template with one placeholder.
2. Generate `<li>` rows from `posts`.
3. Insert rows into placeholder.
4. Return final HTML page.
'''
