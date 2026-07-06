"""Global exception handlers for the Goptant blog API.

Register all handlers by calling register_error_handlers(app) once in main.py.

API routes (/api/*) receive a consistent JSON error response.
Browser routes receive the rendered error.html template.
"""

from pathlib import Path
from typing import Any, Sequence

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


def _friendly_validation_message(errors: Sequence[Any]) -> str:
    """Map Pydantic / FastAPI validation error types to human-readable text."""
    for err in errors:
        loc = list(err.get("loc", []))
        err_type = err.get("type", "")

        if loc == ["path", "post_id"] and err_type == "int_parsing":
            return "Post ID must be a number. Example: /api/posts/1"

        # Generic path-parameter parsing fallback
        if len(loc) == 2 and loc[0] == "path" and err_type == "int_parsing":
            field = loc[1]
            return f"'{field}' must be a whole number."

        # Missing required field
        if err_type == "missing":
            field = loc[-1] if loc else "field"
            return f"Required field '{field}' is missing."

    return "Invalid request. Please check your input and try again."


def register_error_handlers(app: FastAPI) -> None:
    """Attach all global error handlers to the FastAPI app instance."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> Response:
        message = _friendly_validation_message(exc.errors())

        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"error": message},
            )

        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": message,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> Response:
        status_messages: dict[int, str] = {
            404: "The resource you requested could not be found.",
            405: "That HTTP method is not allowed for this endpoint.",
            500: "An unexpected server error occurred. Please try again later.",
        }
        message = status_messages.get(exc.status_code, str(exc.detail))

        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": message},
            )

        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": exc.status_code,
                "message": message,
            },
            status_code=exc.status_code,
        )
