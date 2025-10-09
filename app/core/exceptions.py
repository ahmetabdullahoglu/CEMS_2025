"""
CEMS Custom Exceptions
Defines all custom exceptions used throughout the application
"""

from typing import Any, Optional


class CEMSException(Exception):
    """Base exception for all CEMS errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# ==================== Authentication & Authorization ====================

class AuthenticationError(CEMSException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    
    def __init__(self, message: str = "Invalid username or password", **kwargs):
        super().__init__(message, **kwargs)


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired"""
    
    def __init__(self, message: str = "Token has expired", **kwargs):
        super().__init__(message, **kwargs)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""
    
    def __init__(self, message: str = "Invalid token", **kwargs):
        super().__init__(message, **kwargs)


class AccountLockedError(AuthenticationError):
    """Raised when user account is locked"""
    
    def __init__(
        self,
        message: str = "Account is locked due to multiple failed login attempts",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class PermissionDeniedError(CEMSException):
    """Raised when user lacks required permissions"""
    
    def __init__(
        self,
        message: str = "You don't have permission to perform this action",
        required_permission: Optional[str] = None,
        **kwargs
    ):
        details = {"required_permission": required_permission} if required_permission else {}
        super().__init__(message, status_code=403, details=details, **kwargs)


# ==================== Resource Errors ====================

class ResourceNotFoundError(CEMSException):
    """Raised when requested resource doesn't exist"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        **kwargs
    ):
        message = f"{resource_type} with ID '{resource_id}' not found"
        details = {"resource_type": resource_type, "resource_id": str(resource_id)}
        super().__init__(message, status_code=404, details=details, **kwargs)


class ResourceAlreadyExistsError(CEMSException):
    """Raised when trying to create a resource that already exists"""
    
    def __init__(
        self,
        resource_type: str,
        identifier: str,
        **kwargs
    ):
        message = f"{resource_type} with identifier '{identifier}' already exists"
        details = {"resource_type": resource_type, "identifier": identifier}
        super().__init__(message, status_code=409, details=details, **kwargs)


class ResourceInUseError(CEMSException):
    """Raised when trying to delete a resource that's in use"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        reason: str,
        **kwargs
    ):
        message = f"Cannot delete {resource_type} '{resource_id}': {reason}"
        details = {
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "reason": reason
        }
        super().__init__(message, status_code=409, details=details, **kwargs)


# ==================== Validation Errors ====================

class ValidationError(CEMSException):
    """Raised when data validation fails"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        **kwargs
    ):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=422, details=details, **kwargs)


class InvalidDataError(ValidationError):
    """Raised when provided data is invalid"""
    pass


class InvalidAmountError(ValidationError):
    """Raised when transaction amount is invalid"""
    
    def __init__(
        self,
        message: str = "Invalid transaction amount",
        amount: Optional[float] = None,
        **kwargs
    ):
        details = {"amount": amount} if amount else {}
        super().__init__(message, field="amount", details=details, **kwargs)


# ==================== Business Logic Errors ====================

class InsufficientBalanceError(CEMSException):
    """Raised when branch/vault has insufficient balance"""
    
    def __init__(
        self,
        branch_name: str,
        currency: str,
        required: float,
        available: float,
        **kwargs
    ):
        message = (
            f"Insufficient balance in {branch_name} for {currency}. "
            f"Required: {required}, Available: {available}"
        )
        details = {
            "branch": branch_name,
            "currency": currency,
            "required": required,
            "available": available
        }
        super().__init__(message, status_code=400, details=details, **kwargs)


class InvalidExchangeRateError(CEMSException):
    """Raised when exchange rate is invalid or not available"""
    
    def __init__(
        self,
        from_currency: str,
        to_currency: str,
        **kwargs
    ):
        message = f"Invalid or unavailable exchange rate from {from_currency} to {to_currency}"
        details = {"from_currency": from_currency, "to_currency": to_currency}
        super().__init__(message, status_code=400, details=details, **kwargs)


class TransactionError(CEMSException):
    """Base exception for transaction-related errors"""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, **kwargs):
        details = {"transaction_id": transaction_id} if transaction_id else {}
        super().__init__(message, status_code=400, details=details, **kwargs)


class TransactionAlreadyProcessedError(TransactionError):
    """Raised when trying to modify a completed transaction"""
    
    def __init__(self, transaction_id: str, **kwargs):
        message = f"Transaction {transaction_id} has already been processed"
        super().__init__(message, transaction_id=transaction_id, **kwargs)


class TransactionCancellationError(TransactionError):
    """Raised when transaction cannot be cancelled"""
    
    def __init__(
        self,
        transaction_id: str,
        reason: str,
        **kwargs
    ):
        message = f"Cannot cancel transaction {transaction_id}: {reason}"
        details = {"transaction_id": transaction_id, "reason": reason}
        super().__init__(message, transaction_id=transaction_id, details=details, **kwargs)


class TransferApprovalError(CEMSException):
    """Raised when transfer approval fails"""
    
    def __init__(self, message: str, transfer_id: Optional[str] = None, **kwargs):
        details = {"transfer_id": transfer_id} if transfer_id else {}
        super().__init__(message, status_code=400, details=details, **kwargs)


# ==================== Currency Errors ====================

class CurrencyError(CEMSException):
    """Base exception for currency-related errors"""
    
    def __init__(self, message: str, currency_code: Optional[str] = None, **kwargs):
        details = {"currency_code": currency_code} if currency_code else {}
        super().__init__(message, status_code=400, details=details, **kwargs)


class InvalidCurrencyError(CurrencyError):
    """Raised when currency code is invalid"""
    
    def __init__(self, currency_code: str, **kwargs):
        message = f"Invalid currency code: {currency_code}"
        super().__init__(message, currency_code=currency_code, **kwargs)


class MultipleBasceCurrencyError(CurrencyError):
    """Raised when trying to set multiple base currencies"""
    
    def __init__(self, **kwargs):
        message = "Only one base currency can be active at a time"
        super().__init__(message, **kwargs)


# ==================== Branch Errors ====================

class BranchError(CEMSException):
    """Base exception for branch-related errors"""
    
    def __init__(self, message: str, branch_id: Optional[str] = None, **kwargs):
        details = {"branch_id": branch_id} if branch_id else {}
        super().__init__(message, status_code=400, details=details, **kwargs)


class BranchAccessDeniedError(BranchError):
    """Raised when user doesn't have access to a branch"""
    
    def __init__(self, branch_id: str, **kwargs):
        message = f"You don't have access to branch {branch_id}"
        super().__init__(message, branch_id=branch_id, **kwargs)


class MultipleMainBranchError(BranchError):
    """Raised when trying to set multiple main branches"""
    
    def __init__(self, **kwargs):
        message = "Only one main branch can exist"
        super().__init__(message, **kwargs)


# ==================== Customer Errors ====================

class CustomerError(CEMSException):
    """Base exception for customer-related errors"""
    
    def __init__(self, message: str, customer_id: Optional[str] = None, **kwargs):
        details = {"customer_id": customer_id} if customer_id else {}
        super().__init__(message, status_code=400, details=details, **kwargs)


class DuplicateCustomerError(CustomerError):
    """Raised when customer with same identifier already exists"""
    
    def __init__(self, identifier_type: str, identifier_value: str, **kwargs):
        message = f"Customer with {identifier_type} '{identifier_value}' already exists"
        details = {"identifier_type": identifier_type, "identifier_value": identifier_value}
        super().__init__(message, details=details, **kwargs)


# ==================== System Errors ====================

class DatabaseError(CEMSException):
    """Raised when database operation fails"""
    
    def __init__(self, message: str = "Database operation failed", **kwargs):
        super().__init__(message, status_code=500, **kwargs)


class ConcurrencyError(DatabaseError):
    """Raised when concurrent modification is detected"""
    
    def __init__(
        self,
        message: str = "Resource was modified by another process",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class ConfigurationError(CEMSException):
    """Raised when system configuration is invalid"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=500, **kwargs)


class ExternalServiceError(CEMSException):
    """Raised when external service call fails"""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        **kwargs
    ):
        details = {"service_name": service_name}
        super().__init__(message, status_code=503, details=details, **kwargs)


# ==================== Rate Limiting ====================

class RateLimitExceededError(CEMSException):
    """Raised when rate limit is exceeded"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, status_code=429, details=details, **kwargs)