"""Error handling service for use cases."""

import logging
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from src.application.exceptions import (
    ApplicationException,
    ResourceConflictError,
    ResourceNotFoundError,
    UseCaseExecutionError,
)
from src.domain.exceptions import (
    DomainException,
    EarthquakeAlreadyExistsError,
    EarthquakeNotFoundError,
)
from src.infrastructure.exceptions import (
    DatabaseOperationError,
    ExternalServiceError,
    InfrastructureException,
)

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


class ErrorHandlerService:
    """Service for handling and transforming exceptions across layers."""

    def __init__(self):
        self._error_mappings = {
            EarthquakeNotFoundError: self._handle_not_found_error,
            EarthquakeAlreadyExistsError: self._handle_conflict_error,
        }

    async def execute_use_case(
        self, use_case_func: Callable[P, T], *args: P.args, **kwargs: P.kwargs
    ) -> T:
        """Execute a use case with comprehensive error handling."""
        try:
            return await use_case_func(*args, **kwargs)
        except DomainException as e:
            logger.warning(f"Domain exception in use case: {e.message}")
            mapped_exception = self._map_domain_exception(e)
            raise mapped_exception from e
        except InfrastructureException as e:
            logger.error(f"Infrastructure exception in use case: {e.message}")
            raise UseCaseExecutionError(
                f"Use case execution failed due to infrastructure error: {e.message}",
                original_exception=e,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected exception in use case: {str(e)}")
            raise UseCaseExecutionError(
                "An unexpected error occurred during use case execution",
                original_exception=e,
            ) from e

    def _map_domain_exception(
        self, domain_exception: DomainException
    ) -> ApplicationException:
        """Map domain exceptions to appropriate application exceptions."""
        exception_type = type(domain_exception)

        if exception_type in self._error_mappings:
            return self._error_mappings[exception_type](domain_exception)

        # Default mapping for unmapped domain exceptions
        return UseCaseExecutionError(
            f"Domain validation failed: {domain_exception.message}",
            original_exception=domain_exception,
        )

    def _handle_not_found_error(
        self, domain_exception: EarthquakeNotFoundError
    ) -> ResourceNotFoundError:
        """Handle earthquake not found errors."""
        return ResourceNotFoundError("Earthquake", "unknown")

    def _handle_conflict_error(
        self, domain_exception: EarthquakeAlreadyExistsError
    ) -> ResourceConflictError:
        """Handle earthquake already exists errors."""
        return ResourceConflictError("Earthquake", "unknown")

    def handle_infrastructure_error(
        self, operation: str, exception: Exception
    ) -> InfrastructureException:
        """Handle and wrap infrastructure errors."""
        if isinstance(exception, InfrastructureException):
            return exception

        if "database" in operation.lower() or "sql" in str(exception).lower():
            return DatabaseOperationError(operation, exception)

        if "http" in str(exception).lower() or "network" in str(exception).lower():
            return ExternalServiceError(operation, exception)

        # Default infrastructure error
        return InfrastructureException(
            f"Infrastructure operation '{operation}' failed: {str(exception)}",
            "INFRASTRUCTURE_ERROR",
        )
