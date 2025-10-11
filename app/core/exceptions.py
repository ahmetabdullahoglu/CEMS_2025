# app/core/exceptions.py
"""
Custom Exception Classes
All custom exceptions for CEMS application
"""

from typing import Any, Dict, Optional


class CEMSException(Exception):
    """Base exception class for CEMS application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# ==================== Authentication & Authorization ====================

class AuthenticationError(CEMSException):
    """Exception raised for authentication failures"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(CEMSException):
    """Exception raised for authorization failures"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)


class InvalidCredentialsError(AuthenticationError):
    """Exception raised for invalid credentials"""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Exception raised when token is expired"""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """Exception raised for invalid token"""
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


# ==================== Resource Management ====================

class ResourceNotFoundError(CEMSException):
    """Exception raised when a resource is not found"""
    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(message, status_code=404)


class ResourceAlreadyExistsError(CEMSException):
    """Exception raised when trying to create a duplicate resource"""
    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(message, status_code=409)


class ResourceConflictError(CEMSException):
    """Exception raised when there's a conflict with resource state"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


# ==================== Validation ====================

class ValidationError(CEMSException):
    """Exception raised for validation failures"""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict] = None):
        super().__init__(message, status_code=400, details=details)


class InvalidInputError(ValidationError):
    """Exception raised for invalid input"""
    def __init__(self, field: str, message: str = "Invalid input"):
        super().__init__(f"{field}: {message}")


# ==================== Business Logic ====================

class BusinessRuleViolationError(CEMSException):
    """Exception raised when business rule is violated"""
    def __init__(self, message: str = "Business rule violation"):
        super().__init__(message, status_code=422)


class InsufficientBalanceError(CEMSException):
    """Exception raised when balance is insufficient"""
    def __init__(self, message: str = "Insufficient balance"):
        super().__init__(message, status_code=400)


class TransactionError(CEMSException):
    """Exception raised for transaction failures"""
    def __init__(self, message: str = "Transaction failed"):
        super().__init__(message, status_code=500)


# ==================== Database ====================

class DatabaseOperationError(CEMSException):
    """Exception raised when database operation fails"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)


class DatabaseConnectionError(DatabaseOperationError):
    """Exception raised for database connection issues"""
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message)


# ==================== Rate Limiting ====================

class RateLimitExceededError(CEMSException):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


# ==================== External Services ====================

class ExternalServiceError(CEMSException):
    """Exception raised for external service failures"""
    def __init__(self, service_name: str, message: str = "External service error"):
        super().__init__(f"{service_name}: {message}", status_code=502)


# ==================== File Operations ====================

class FileOperationError(CEMSException):
    """Exception raised for file operation failures"""
    def __init__(self, message: str = "File operation failed"):
        super().__init__(message, status_code=500)


class FileNotFoundError(FileOperationError):
    """Exception raised when file is not found"""
    def __init__(self, filename: str):
        super().__init__(f"File '{filename}' not found")


class InvalidFileFormatError(FileOperationError):
    """Exception raised for invalid file format"""
    def __init__(self, expected_format: str):
        super().__init__(f"Invalid file format. Expected: {expected_format}")


# ==================== Configuration ====================

class ConfigurationError(CEMSException):
    """Exception raised for configuration issues"""
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status_code=500)


# ==================== Utility ====================

def handle_exception(exc: Exception) -> Dict[str, Any]:
    """
    Convert exception to API response format
    
    Args:
        exc: Exception to handle
        
    Returns:
        Dictionary with error details
    """
    if isinstance(exc, CEMSException):
        return {
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details
        }
    
    # Handle unknown exceptions
    return {
        "error": "InternalServerError",
        "message": "An unexpected error occurred",
        "status_code": 500,
        "details": {}
    }