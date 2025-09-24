"""Application layer exceptions for the earthquake monitoring system."""


class ApplicationException(Exception):
    """Base exception for application layer errors."""

    def __init__(self, message: str, error_code: str = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class UseCaseExecutionError(ApplicationException):
    """Raised when a use case execution fails."""

    def __init__(self, message: str, original_exception: Exception = None) -> None:
        super().__init__(message, "USE_CASE_EXECUTION_ERROR")
        self.original_exception = original_exception


class EventPublishingError(ApplicationException):
    """Raised when event publishing fails."""

    def __init__(self, event_type: str, original_exception: Exception = None) -> None:
        message = f"Failed to publish event of type: {event_type}"
        super().__init__(message, "EVENT_PUBLISHING_ERROR")
        self.event_type = event_type
        self.original_exception = original_exception


class ValidationError(ApplicationException):
    """Raised when application-level validation fails."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(
            f"Validation error for '{field}': {message}", "VALIDATION_ERROR"
        )
        self.field = field


class ResourceConflictError(ApplicationException):
    """Raised when a resource conflict occurs."""

    def __init__(self, resource_type: str, identifier: str) -> None:
        message = f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(message, "RESOURCE_CONFLICT")
        self.resource_type = resource_type
        self.identifier = identifier


class ResourceNotFoundError(ApplicationException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, identifier: str) -> None:
        message = f"{resource_type} with identifier '{identifier}' not found"
        super().__init__(message, "RESOURCE_NOT_FOUND")
        self.resource_type = resource_type
        self.identifier = identifier
