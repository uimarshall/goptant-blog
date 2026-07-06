# Global Error Handler🧮

## Raw error message🧮

```python
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": [
        "path",
        "post_id"
      ],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "abe"
    }
  ]
}
```

## Global User friendly error message

Good, I have the full picture. Now fixing the type error — `exc.errors()` returns `Sequence[Any]` (defined by Pydantic), not `list[dict]`, so the type hint on the helper needs to match that exactly.

```

```

Error fixed. Now here is the full detailed explanation for a beginner.

---

## What changed and how it all fits together

### The problem we started with

Your original `get_post` function returned an ugly raw error dictionary when a post was not found, and sent no useful feedback when someone typed a non-number in the URL. The goal was to fix both without cluttering main.py.

---

### File 1 — errors.py (new file)

This is the **global error file**. It lives inside the `app/` package, which already existed as a Python package (because of **init**.py).

Think of it like a reception desk for all errors in your API. Instead of handling errors individually in every route, you define the rules once here.

```python
from typing import Any, Sequence
```

- `Sequence` is a built-in Python type hint meaning "any ordered collection" — a list, a tuple, etc.
- `Any` means "any data type, I don't know exactly what it is."
- These are needed because Pydantic (the library FastAPI uses for validation) returns errors as `Sequence[Any]`, not a plain `list[dict]`. This was exactly the type error you saw — your old hint said `list[dict]` but the real type was `Sequence[Any]`, and Python's type checker noticed the mismatch.

```python
def _friendly_validation_message(errors: Sequence[Any]) -> str:
```

- The underscore `_` at the start is a Python convention meaning "this function is private — only used inside this file, not imported elsewhere."
- It receives the list of errors from FastAPI and returns a single plain-English string.
- Inside, it loops through each error and checks its `type` and `loc` (location). For example, when `/api/posts/abe` is called, FastAPI produces an error with `loc = ["path", "post_id"]` and `type = "int_parsing"`. This function catches that and returns `"Post ID must be a number. Example: /api/posts/1"` instead of the technical JSON blob.

```python
def register_error_handlers(app: FastAPI) -> None:
```

- This is the **public** function that main.py calls.
- It takes your FastAPI app as an argument and attaches (registers) two error handlers to it.
- Think of it like plugging in two power adapters into your app.

**Handler 1 — `validation_error_handler`:**

- Fires whenever FastAPI gets input it cannot parse — like a letter where a number is expected.
- FastAPI calls `exc.errors()` internally, which gives the raw Pydantic error list.
- We pass that to `_friendly_validation_message` to get a readable sentence.
- We return it as a `JSONResponse` with status code 422 (the standard code for "unprocessable entity").

**Handler 2 — `http_error_handler`:**

- Fires for standard HTTP errors — 404 (not found), 405 (wrong method), 500 (server crash), etc.
- It maps status codes to plain sentences using a dictionary.
- If the code is not in the dictionary, it falls back to whatever detail FastAPI has.
- Returns a consistent `{"error": "..."}` shape so your frontend always gets the same structure.

---

### File 2 — main.py (two small additions)

```python
from app.errors import register_error_handlers
```

- This imports the function from the new file. Python finds `app/errors.py` because `app/` is a package.

```python
app = FastAPI()
register_error_handlers(app)
```

- After creating the app, we immediately pass it to `register_error_handlers`.
- That function decorates the app with the two handlers.
- Everything else in main.py stays completely unchanged.

---

### How the pieces connect — flow diagram

```
Browser sends:  GET /api/posts/abe
                        ↓
FastAPI tries to parse "abe" as int
                        ↓
Pydantic raises RequestValidationError
                        ↓
errors.py → validation_error_handler() catches it
                        ↓
calls _friendly_validation_message()
                        ↓
returns: {"error": "Post ID must be a number. Example: /api/posts/1"}
                        ↓
Browser receives a clear, readable message
```

---

### Why this structure follows best practices

| Practice                      | What we did                                                                       |
| ----------------------------- | --------------------------------------------------------------------------------- |
| **Separation of concerns**    | Error logic lives in errors.py, route logic stays in main.py                      |
| **Single registration point** | One `register_error_handlers(app)` call wires everything up                       |
| **Consistent response shape** | Every error always returns `{"error": "..."}` — frontend can rely on this         |
| **Correct type hints**        | `Sequence[Any]` matches what Pydantic actually returns, no type errors            |
| **Private helper**            | `_friendly_validation_message` is prefixed with `_` to signal it is internal only |

Created 2 todos

Made changes.
