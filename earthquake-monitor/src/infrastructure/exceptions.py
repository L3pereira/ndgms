"""Infrastructure layer exceptions for the earthquake monitoring system."""


class InfrastructureException(Exception):
    """Base exception for infrastructure layer errors."""

    def __init__(self, message: str, error_code: str = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class DatabaseConnectionError(InfrastructureException):
    """Raised when database connection fails."""

    def __init__(self, original_exception: Exception = None) -> None:
        super().__init__("Failed to connect to database", "DATABASE_CONNECTION_ERROR")
        self.original_exception = original_exception


class DatabaseOperationError(InfrastructureException):
    """Raised when database operation fails."""

    def __init__(self, operation: str, original_exception: Exception = None) -> None:
        message = f"Database operation '{operation}' failed"
        super().__init__(message, "DATABASE_OPERATION_ERROR")
        self.operation = operation
        self.original_exception = original_exception


class ExternalServiceError(InfrastructureException):
    """Raised when external service call fails."""

    def __init__(self, service_name: str, original_exception: Exception = None) -> None:
        message = f"External service '{service_name}' error"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service_name = service_name
        self.original_exception = original_exception


class ConfigurationError(InfrastructureException):
    """Raised when configuration is invalid."""

    def __init__(self, setting_name: str, message: str = None) -> None:
        base_message = f"Invalid configuration for '{setting_name}'"
        full_message = f"{base_message}: {message}" if message else base_message
        super().__init__(full_message, "CONFIGURATION_ERROR")
        self.setting_name = setting_name


class SerializationError(InfrastructureException):
    """Raised when serialization/deserialization fails."""

    def __init__(
        self, data_type: str, operation: str, original_exception: Exception = None
    ) -> None:
        message = f"Failed to {operation} {data_type}"
        super().__init__(message, "SERIALIZATION_ERROR")
        self.data_type = data_type
        self.operation = operation
        self.original_exception = original_exception
