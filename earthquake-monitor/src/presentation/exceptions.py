"""Presentation layer exception handling."""

import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.application.exceptions import (
    ApplicationException,
    ResourceConflictError,
    ResourceNotFoundError,
    UseCaseExecutionError,
    ValidationError,
)
from src.domain.exceptions import DomainException

logger = logging.getLogger(__name__)


class PresentationException(HTTPException):
    """Base exception for presentation layer."""

    def __init__(self, status_code: int, detail: str, error_code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """Handle domain exceptions and convert to HTTP responses."""
    logger.warning(f"Domain exception: {exc.message}")

    return JSONResponse(
        status_code=400,
        content={
            "error": "Domain validation failed",
            "message": exc.message,
            "error_code": "DOMAIN_VALIDATION_ERROR",
            "type": exc.__class__.__name__,
        },
    )


async def application_exception_handler(
    request: Request, exc: ApplicationException
) -> JSONResponse:
    """Handle application exceptions and convert to HTTP responses."""
    if isinstance(exc, ResourceNotFoundError):
        status_code = 404
        logger.info(f"Resource not found: {exc.message}")
    elif isinstance(exc, ResourceConflictError):
        status_code = 409
        logger.info(f"Resource conflict: {exc.message}")
    elif isinstance(exc, ValidationError):
        status_code = 400
        logger.warning(f"Validation error: {exc.message}")
    elif isinstance(exc, UseCaseExecutionError):
        status_code = 500
        logger.error(f"Use case execution error: {exc.message}")
    else:
        status_code = 500
        logger.error(f"Application error: {exc.message}")

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "Application error",
            "message": exc.message,
            "error_code": exc.error_code or "APPLICATION_ERROR",
            "type": exc.__class__.__name__,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "type": "InternalServerError",
        },
    )
