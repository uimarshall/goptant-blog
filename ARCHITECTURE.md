# ARCHITECTURE OF THE APPLICATION

> We will have 3 layers in the application.

1. Database models: These are the SQL alchemy classes that defines what we store in the database.
2. Pydantic Schemas: These define what we accept and return from our API.
3. API Routes: These are FASTAPI endpoints that can handle the actual request.

> The separation makes sense because each layer has a different job.

`Database models` have ORM specific features like relationships and database column types.

Pydantic schemas define our API contract, i.e. what we accept and what we return.

Keeping those separate means we can change one without affecting the other. So the data flow is going to to work like this:

Request comes In -> Pydantic Validates it -> SQL alchemy stores or retrieves the data -> And pydantic format the response and the response goes out.

So there is clear boundary between each layer.

## Overview

This application follows a **3-layer architecture**. Think of these layers like the floors of a building — each floor has a specific purpose, and you move through them in a defined order. Keeping concerns separated this way makes the code easier to understand, test, and maintain.

---

## The 3 Layers

### 1. Database Models (SQLAlchemy)

These are Python classes that describe the **shape of your data in the database** — what tables exist, what columns they have, and how tables relate to each other (e.g. a user can have many posts).

SQLAlchemy is an **ORM (Object-Relational Mapper)**, which means instead of writing raw SQL like:

```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
```

...you write a Python class instead:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

SQLAlchemy then handles translating that into actual database operations for you.

---

### 2. Pydantic Schemas

These are Python classes that define what data is **allowed in** (from a request) and **sent out** (in a response) through your API.

Pydantic is a **data validation library**. When a user sends a request to your API, Pydantic checks that the data matches the expected shape — correct types, required fields present, etc. — _before_ it ever touches your database.

For example, if your API expects a blog post with a `title` (string) and `content` (string), Pydantic will automatically reject a request that sends a number for `title`, or one that is missing `content` entirely.

> **Why keep schemas separate from database models?**
> Your database model might store sensitive fields (like hashed passwords) that you never want to expose in an API response. Pydantic schemas let you control exactly what goes in and what comes out, independently of what the database stores.

---

### 3. API Routes (FastAPI)

These are the **entry points** of your application — the URLs that clients (browsers, mobile apps, other services) call to interact with your backend.

FastAPI is a modern Python web framework. Each route is a Python function decorated with the HTTP method and path it handles:

```python
@app.get("/posts/{id}")
def get_post(id: int):
    ...
```

The route function coordinates the other two layers: it receives a request, uses Pydantic to validate it, calls SQLAlchemy to read or write data, and then returns a Pydantic-shaped response.

---

## How the Layers Work Together (Data Flow)

```
Incoming HTTP Request
        |
        v
[ Pydantic Schema ]  <-- Validates & parses the request body/params
        |
        v
[  API Route fn  ]   <-- Business logic lives here
        |
        v
[ SQLAlchemy Model ] <-- Reads from / writes to the database
        |
        v
[ Pydantic Schema ]  <-- Formats the data for the outgoing response
        |
        v
Outgoing HTTP Response
```

In plain English:

1. A request comes in (e.g. `POST /posts` with a JSON body).
2. **Pydantic** validates the incoming data — wrong types or missing fields are rejected immediately with a clear error.
3. The **API route** runs the actual logic (create, read, update, delete).
4. **SQLAlchemy** stores or retrieves the data from the database.
5. **Pydantic** formats the result into the response shape before sending it back.

---

## Why This Separation Matters

| Layer          | Responsibility                     | Library    |
| -------------- | ---------------------------------- | ---------- |
| Database Model | How data is stored                 | SQLAlchemy |
| Schema         | What data is accepted / returned   | Pydantic   |
| Route          | Handling the HTTP request/response | FastAPI    |

Because each layer has **one job**, you can change one without breaking the others. For example:

- You can add a column to a database model without changing what the API returns.
- You can change the API response shape without touching the database.
- You can swap out validation rules in schemas without rewriting route logic.

This is the core idea behind **Separation of Concerns** — a fundamental principle in software design.
