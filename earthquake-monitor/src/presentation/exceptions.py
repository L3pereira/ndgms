"""Custom exceptions for the presentation layer."""


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id '{resource_id}' not found")


class ValidationError(Exception):
    """Raised when request validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
