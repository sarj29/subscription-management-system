"""
Custom exception classes and FastAPI exception handlers.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------
class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None, status_code: int | None = None) -> None:
        self.detail = detail or self.__class__.detail
        self.status_code = status_code or self.__class__.status_code
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found."


class ConflictError(AppException):
    status_code = 409
    detail = "Resource already exists."


class ForbiddenError(AppException):
    status_code = 403
    detail = "You do not have permission to perform this action."


class ValidationError(AppException):
    status_code = 422
    detail = "Validation error."


class InvalidStatusTransitionError(AppException):
    """Raised when a status change is not permitted by the state machine."""

    status_code = 422

    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            detail=f"Cannot transition from '{current}' to '{target}'.",
        )


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------
def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on *app*."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
