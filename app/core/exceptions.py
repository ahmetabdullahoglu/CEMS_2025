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


class AccountLockedError(AuthenticationError):
    """Exception raised when account is locked due to failed login attempts"""
    def __init__(self, message: str = "Account is locked"):
        super().__init__(message)


class PermissionDeniedError(AuthorizationError):
    """Exception raised when user lacks required permissions"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)


class RoleNotFoundError(AuthorizationError):
    """Exception raised when required role is not found"""
    def __init__(self, role_name: str):
        super().__init__(f"Role '{role_name}' not found")


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


class InvalidAmountError(ValidationError):
    """Exception raised for invalid amount values"""
    def __init__(self, message: str = "Invalid amount"):
        super().__init__(message)


class InvalidCurrencyError(ValidationError):
    """Exception raised for invalid currency"""
    def __init__(self, currency_code: str):
        super().__init__(f"Invalid currency code: {currency_code}")


class InvalidExchangeRateError(ValidationError):
    """Exception raised for invalid exchange rate"""
    def __init__(self, message: str = "Invalid exchange rate"):
        super().__init__(message)


# ==================== Business Logic ====================

class BusinessRuleViolationError(CEMSException):
    """Exception raised when business rule is violated"""
    def __init__(self, message: str = "Business rule violation"):
        super().__init__(message, status_code=422)


class InsufficientBalanceError(BusinessRuleViolationError):
    """Exception raised when balance is insufficient"""
    def __init__(self, message: str = "Insufficient balance"):
        super().__init__(message)


class InsufficientFundsError(BusinessRuleViolationError):
    """Exception raised when funds are insufficient for transaction"""
    def __init__(self, required_amount: str, available_amount: str):
        message = f"Insufficient funds. Required: {required_amount}, Available: {available_amount}"
        super().__init__(message)


class TransactionError(CEMSException):
    """Exception raised for transaction failures"""
    def __init__(self, message: str = "Transaction failed"):
        super().__init__(message, status_code=500)


class DailyLimitExceededError(BusinessRuleViolationError):
    """Exception raised when daily transaction limit is exceeded"""
    def __init__(self, limit: str):
        super().__init__(f"Daily transaction limit of {limit} exceeded")


class TransactionLimitExceededError(BusinessRuleViolationError):
    """Exception raised when transaction limit is exceeded"""
    def __init__(self, limit: str):
        super().__init__(f"Transaction limit of {limit} exceeded")


class MinimumBalanceError(BusinessRuleViolationError):
    """Exception raised when balance falls below minimum"""
    def __init__(self, minimum_balance: str):
        super().__init__(f"Balance cannot fall below minimum of {minimum_balance}")


class ThresholdExceededError(BusinessRuleViolationError):
    """Exception raised when threshold is exceeded"""
    def __init__(self, threshold_type: str, threshold_value: str):
        super().__init__(f"{threshold_type} threshold of {threshold_value} exceeded")


# ==================== Document Management ====================

class DocumentError(CEMSException):
    """Exception raised for document-related errors"""
    def __init__(self, message: str = "Document error"):
        super().__init__(message, status_code=400)


class DocumentNotFoundError(ResourceNotFoundError):
    """Exception raised when document is not found"""
    def __init__(self, document_id: Any):
        super().__init__("Document", document_id)


class InvalidDocumentTypeError(ValidationError):
    """Exception raised for invalid document type"""
    def __init__(self, document_type: str):
        super().__init__(f"Invalid document type: {document_type}")


class DocumentExpiredError(ValidationError):
    """Exception raised when document has expired"""
    def __init__(self, document_id: Any):
        super().__init__(f"Document {document_id} has expired")


# ==================== Customer Management ====================

class CustomerError(CEMSException):
    """Exception raised for customer-related errors"""
    def __init__(self, message: str = "Customer error"):
        super().__init__(message, status_code=400)


class CustomerNotFoundError(ResourceNotFoundError):
    """Exception raised when customer is not found"""
    def __init__(self, customer_id: Any):
        super().__init__("Customer", customer_id)


class DuplicateCustomerError(ResourceAlreadyExistsError):
    """Exception raised when customer already exists"""
    def __init__(self, identifier: str):
        super().__init__("Customer", identifier)


class CustomerVerificationError(ValidationError):
    """Exception raised for customer verification failures"""
    def __init__(self, message: str = "Customer verification failed"):
        super().__init__(message)


class CustomerNotVerifiedError(AuthorizationError):
    """Exception raised when customer is not verified"""
    def __init__(self, customer_id: Any):
        super().__init__(f"Customer {customer_id} is not verified")


class CustomerBlacklistedError(AuthorizationError):
    """Exception raised when customer is blacklisted"""
    def __init__(self, customer_id: Any):
        super().__init__(f"Customer {customer_id} is blacklisted")


# ==================== Branch Management ====================

class BranchError(CEMSException):
    """Exception raised for branch-related errors"""
    def __init__(self, message: str = "Branch error"):
        super().__init__(message, status_code=400)


class BranchNotFoundError(ResourceNotFoundError):
    """Exception raised when branch is not found"""
    def __init__(self, branch_id: Any):
        super().__init__("Branch", branch_id)


class BranchInactiveError(BusinessRuleViolationError):
    """Exception raised when trying to use inactive branch"""
    def __init__(self, branch_id: Any):
        super().__init__(f"Branch {branch_id} is inactive")


class BranchBalanceError(BusinessRuleViolationError):
    """Exception raised for branch balance issues"""
    def __init__(self, message: str = "Branch balance error"):
        super().__init__(message)


# ==================== Vault Management ====================

class VaultError(CEMSException):
    """Exception raised for vault-related errors"""
    def __init__(self, message: str = "Vault error"):
        super().__init__(message, status_code=400)


class VaultNotFoundError(ResourceNotFoundError):
    """Exception raised when vault is not found"""
    def __init__(self, vault_id: Any):
        super().__init__("Vault", vault_id)


class VaultBalanceError(BusinessRuleViolationError):
    """Exception raised for vault balance issues"""
    def __init__(self, message: str = "Vault balance error"):
        super().__init__(message)


class VaultTransferError(TransactionError):
    """Exception raised for vault transfer failures"""
    def __init__(self, message: str = "Vault transfer failed"):
        super().__init__(message)


# ==================== Currency Management ====================

class CurrencyError(CEMSException):
    """Exception raised for currency-related errors"""
    def __init__(self, message: str = "Currency error"):
        super().__init__(message, status_code=400)


class CurrencyNotFoundError(ResourceNotFoundError):
    """Exception raised when currency is not found"""
    def __init__(self, currency_code: str):
        super().__init__("Currency", currency_code)


class CurrencyInactiveError(BusinessRuleViolationError):
    """Exception raised when currency is inactive"""
    def __init__(self, currency_code: str):
        super().__init__(f"Currency {currency_code} is inactive")


class ExchangeRateNotFoundError(ResourceNotFoundError):
    """Exception raised when exchange rate is not found"""
    def __init__(self, from_currency: str, to_currency: str):
        super().__init__(
            "Exchange Rate", 
            f"{from_currency} to {to_currency}"
        )


class ExchangeRateExpiredError(ValidationError):
    """Exception raised when exchange rate has expired"""
    def __init__(self, from_currency: str, to_currency: str):
        super().__init__(
            f"Exchange rate for {from_currency} to {to_currency} has expired"
        )


# ==================== Report & Audit ====================

class ReportError(CEMSException):
    """Exception raised for report generation errors"""
    def __init__(self, message: str = "Report generation failed"):
        super().__init__(message, status_code=500)


class AuditError(CEMSException):
    """Exception raised for audit log errors"""
    def __init__(self, message: str = "Audit logging failed"):
        super().__init__(message, status_code=500)


class ReportNotFoundError(ResourceNotFoundError):
    """Exception raised when report is not found"""
    def __init__(self, report_id: Any):
        super().__init__("Report", report_id)


# ==================== Database ====================

class DatabaseOperationError(CEMSException):
    """Exception raised when database operation fails"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)


class DatabaseConnectionError(DatabaseOperationError):
    """Exception raised for database connection issues"""
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message)


class DatabaseIntegrityError(DatabaseOperationError):
    """Exception raised for database integrity violations"""
    def __init__(self, message: str = "Database integrity error"):
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


class APIConnectionError(ExternalServiceError):
    """Exception raised when external API connection fails"""
    def __init__(self, service_name: str):
        super().__init__(service_name, "Connection failed")


class APIResponseError(ExternalServiceError):
    """Exception raised when external API returns error"""
    def __init__(self, service_name: str, status_code: int, message: str):
        super().__init__(service_name, f"HTTP {status_code}: {message}")


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


class FileSizeExceededError(FileOperationError):
    """Exception raised when file size exceeds limit"""
    def __init__(self, max_size: str):
        super().__init__(f"File size exceeds maximum allowed size of {max_size}")


class FileUploadError(FileOperationError):
    """Exception raised when file upload fails"""
    def __init__(self, message: str = "File upload failed"):
        super().__init__(message)


# ==================== Configuration ====================

class ConfigurationError(CEMSException):
    """Exception raised for configuration issues"""
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status_code=500)


class MissingConfigurationError(ConfigurationError):
    """Exception raised when required configuration is missing"""
    def __init__(self, config_key: str):
        super().__init__(f"Missing required configuration: {config_key}")


class InvalidConfigurationError(ConfigurationError):
    """Exception raised when configuration is invalid"""
    def __init__(self, config_key: str, message: str):
        super().__init__(f"Invalid configuration for {config_key}: {message}")


# ==================== Notification ====================

class NotificationError(CEMSException):
    """Exception raised for notification failures"""
    def __init__(self, message: str = "Notification failed"):
        super().__init__(message, status_code=500)


class EmailSendError(NotificationError):
    """Exception raised when email sending fails"""
    def __init__(self, recipient: str, message: str = "Email send failed"):
        super().__init__(f"Failed to send email to {recipient}: {message}")


class SMSSendError(NotificationError):
    """Exception raised when SMS sending fails"""
    def __init__(self, phone: str, message: str = "SMS send failed"):
        super().__init__(f"Failed to send SMS to {phone}: {message}")


# ==================== Utility Functions ====================

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


def get_exception_by_name(exception_name: str) -> type:
    """
    Get exception class by name
    
    Args:
        exception_name: Name of the exception class
        
    Returns:
        Exception class or None if not found
    """
    return globals().get(exception_name)

class NotFoundError(CEMSException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class ValidationError(CEMSException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)

class DuplicateError(CEMSException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)

class PermissionDeniedError(CEMSException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)

class DatabaseOperationError(CEMSException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)
        
# ==================== Exception Registry ====================

# All custom exceptions for reference
ALL_EXCEPTIONS = [
    # Base
    "CEMSException",
    
    # Authentication & Authorization
    "AuthenticationError",
    "AuthorizationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "AccountLockedError",
    "PermissionDeniedError",
    "RoleNotFoundError",
    
    # Resource Management
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "ResourceConflictError",
    
    # Validation
    "ValidationError",
    "InvalidInputError",
    "InvalidAmountError",
    "InvalidCurrencyError",
    "InvalidExchangeRateError",
    
    # Business Logic
    "BusinessRuleViolationError",
    "InsufficientBalanceError",
    "InsufficientFundsError",
    "TransactionError",
    "DailyLimitExceededError",
    "TransactionLimitExceededError",
    "MinimumBalanceError",
    "ThresholdExceededError",
    
    # Document Management
    "DocumentError",
    "DocumentNotFoundError",
    "InvalidDocumentTypeError",
    "DocumentExpiredError",
    
    # Customer Management
    "CustomerError",
    "CustomerNotFoundError",
    "DuplicateCustomerError",
    "CustomerVerificationError",
    "CustomerNotVerifiedError",
    "CustomerBlacklistedError",
    
    # Branch Management
    "BranchError",
    "BranchNotFoundError",
    "BranchInactiveError",
    "BranchBalanceError",
    
    # Vault Management
    "VaultError",
    "VaultNotFoundError",
    "VaultBalanceError",
    "VaultTransferError",
    
    # Currency Management
    "CurrencyError",
    "CurrencyNotFoundError",
    "CurrencyInactiveError",
    "ExchangeRateNotFoundError",
    "ExchangeRateExpiredError",
    
    # Report & Audit
    "ReportError",
    "AuditError",
    "ReportNotFoundError",
    
    # Database
    "DatabaseOperationError",
    "DatabaseConnectionError",
    "DatabaseIntegrityError",
    
    # Rate Limiting
    "RateLimitExceededError",
    
    # External Services
    "ExternalServiceError",
    "APIConnectionError",
    "APIResponseError",
    
    # File Operations
    "FileOperationError",
    "FileNotFoundError",
    "InvalidFileFormatError",
    "FileSizeExceededError",
    "FileUploadError",
    
    # Configuration
    "ConfigurationError",
    "MissingConfigurationError",
    "InvalidConfigurationError",
    
    # Notification
    "NotificationError",
    "EmailSendError",
    "SMSSendError",
    
    "NotFoundError",
    "ValidationError", 
    "DuplicateError",
    "PermissionDeniedError",
    "DatabaseOperationError",
]


__all__ = ALL_EXCEPTIONS + ["handle_exception", "get_exception_by_name"]