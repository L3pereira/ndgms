"""Unit tests for centralized exception handlers."""

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import DomainException, InvalidDateTimeError
from src.presentation.main import domain_exception_handler


class TestDomainExceptionHandler:
    """Test the centralized domain exception handler."""

    @pytest.mark.asyncio
    async def test_domain_exception_handler_returns_400(self):
        """Test that domain exception handler returns 400 Bad Request."""
        # Create a mock request with required ASGI scope
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        }
        request = Request(scope=scope)

        # Create a domain exception
        exception = InvalidDateTimeError(
            "Earthquake occurrence time cannot be in the future"
        )

        # Call the handler
        response = await domain_exception_handler(request, exception)

        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        assert (
            response.body
            == b'{"detail":"Earthquake occurrence time cannot be in the future"}'
        )

    @pytest.mark.asyncio
    async def test_domain_exception_handler_with_generic_domain_exception(self):
        """Test handler with generic DomainException."""
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        }
        request = Request(scope=scope)
        exception = DomainException("Generic domain validation error")

        response = await domain_exception_handler(request, exception)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        assert response.body == b'{"detail":"Generic domain validation error"}'

    def test_domain_exception_hierarchy(self):
        """Test that all domain exceptions inherit from DomainException."""
        # Verify InvalidDateTimeError is a DomainException
        exception = InvalidDateTimeError("Test message")
        assert isinstance(exception, DomainException)
        assert str(exception) == "Test message"
        assert exception.message == "Test message"
