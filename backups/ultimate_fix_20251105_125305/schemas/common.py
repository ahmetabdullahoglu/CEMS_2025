"""
Common/Shared Pydantic Schemas
Reusable schemas used across multiple endpoints
"""

from typing import Any, Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field, field_validator


# ==================== Generic Type Variable ====================
T = TypeVar('T')


# ==================== Pagination Schemas ====================

class PaginationParams(BaseModel):
    """
    Common pagination parameters
    Used in query parameters for list endpoints
    """
    page: int = Field(default=1, ge=1, description="Page number (starting from 1)")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by"
    )
    sort_order: Optional[str] = Field(
        default="asc",
        description="Sort order: asc or desc"
    )
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: Optional[str]) -> Optional[str]:
        """Validate sort order is either asc or desc"""
        if v is not None and v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order must be either "asc" or "desc"')
        return v.lower() if v else None
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database query"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper
    Used for list endpoints with pagination
    """
    success: bool = True
    data: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """
        Create a paginated response
        
        Args:
            data: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated response object
        """
        total_pages = (total + page_size - 1) // page_size
        
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


# ==================== Response Schemas ====================

class SuccessResponse(BaseModel):
    """
    Generic success response
    Used for operations that don't return specific data
    """
    success: bool = True
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Optional additional data")


class ErrorResponse(BaseModel):
    """
    Generic error response
    Used for error responses
    """
    success: bool = False
    error: dict = Field(..., description="Error details")
    
    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        details: Optional[dict] = None
    ) -> "ErrorResponse":
        """
        Create an error response
        
        Args:
            code: Error code
            message: Error message
            details: Optional error details
            
        Returns:
            ErrorResponse: Error response object
        """
        return cls(
            error={
                "code": code,
                "message": message,
                "details": details or {}
            }
        )


class MessageResponse(BaseModel):
    """
    Simple message response
    Used for operations that just need to return a message
    """
    success: bool = True
    message: str


# ==================== Filter Schemas ====================

class DateRangeFilter(BaseModel):
    """
    Common date range filter
    Used for filtering by date ranges
    """
    start_date: Optional[str] = Field(
        None,
        description="Start date (ISO format: YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None,
        description="End date (ISO format: YYYY-MM-DD)"
    )
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format"""
        if v is not None:
            from datetime import datetime
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        return v


class SearchFilter(BaseModel):
    """
    Common search filter
    Used for text search across multiple fields
    """
    query: str = Field(..., min_length=1, description="Search query")
    fields: Optional[List[str]] = Field(
        None,
        description="Fields to search in (leave empty to search all)"
    )


# ==================== Status Schemas ====================

class StatusResponse(BaseModel):
    """
    Status check response
    Used for health checks and status endpoints
    """
    success: bool = True
    status: str = Field(..., description="Current status")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="Current timestamp")
    details: Optional[dict] = Field(None, description="Additional status details")


# ==================== File Upload Schemas ====================

class FileUploadResponse(BaseModel):
    """
    File upload response
    Used after successful file upload
    """
    success: bool = True
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File MIME type")
    url: Optional[str] = Field(None, description="File URL if accessible")


# ==================== Bulk Operation Schemas ====================

class BulkOperationRequest(BaseModel, Generic[T]):
    """
    Generic bulk operation request
    Used for batch operations
    """
    items: List[T] = Field(..., description="List of items to process")
    
    @field_validator('items')
    @classmethod
    def validate_items_not_empty(cls, v: List[T]) -> List[T]:
        """Ensure items list is not empty"""
        if not v:
            raise ValueError('Items list cannot be empty')
        return v


class BulkOperationResponse(BaseModel):
    """
    Bulk operation response
    Reports success/failure for each item
    """
    success: bool = True
    total: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[dict] = Field(
        default_factory=list,
        description="List of errors for failed items"
    )


# ==================== Audit Schemas ====================

class AuditInfo(BaseModel):
    """
    Audit information
    Common fields for audit trail
    """
    created_by: Optional[str] = Field(None, description="User who created")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


# ==================== Validation Schemas ====================

class ValidationError(BaseModel):
    """
    Validation error detail
    Used in validation error responses
    """
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    type: str = Field(..., description="Validation error type")


class ValidationErrorResponse(BaseModel):
    """
    Validation error response
    Used when request validation fails
    """
    success: bool = False
    error: dict = Field(..., description="Error details")
    
    @classmethod
    def create(
        cls,
        errors: List[ValidationError]
    ) -> "ValidationErrorResponse":
        """
        Create a validation error response
        
        Args:
            errors: List of validation errors
            
        Returns:
            ValidationErrorResponse: Validation error response object
        """
        return cls(
            error={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": [error.dict() for error in errors]
                }
            }
        )


# ==================== Statistics Schemas ====================

class StatisticsResponse(BaseModel):
    """
    Generic statistics response
    Used for statistical data endpoints
    """
    success: bool = True
    period: str = Field(..., description="Time period for statistics")
    data: dict = Field(..., description="Statistical data")
    generated_at: str = Field(..., description="When statistics were generated")


# ==================== Export Schemas ====================

class ExportRequest(BaseModel):
    """
    Export request
    Used for data export endpoints
    """
    format: str = Field(
        ...,
        description="Export format (pdf, excel, csv, json)"
    )
    filters: Optional[dict] = Field(
        None,
        description="Filters to apply before export"
    )
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate export format"""
        valid_formats = ['pdf', 'excel', 'csv', 'json']
        if v.lower() not in valid_formats:
            raise ValueError(f'Format must be one of: {", ".join(valid_formats)}')
        return v.lower()


class ExportResponse(BaseModel):
    """
    Export response
    Returned after successful export
    """
    success: bool = True
    export_id: str = Field(..., description="Unique export identifier")
    format: str = Field(..., description="Export format")
    download_url: str = Field(..., description="URL to download the export")
    expires_at: str = Field(..., description="When the download link expires")
    file_size: Optional[int] = Field(None, description="File size in bytes")


# ==================== Utility Functions ====================

def create_success_response(message: str, data: Any = None) -> SuccessResponse:
    """
    Helper function to create success response
    
    Args:
        message: Success message
        data: Optional additional data
        
    Returns:
        SuccessResponse: Success response object
    """
    return SuccessResponse(message=message, data=data)


def create_error_response(
    code: str,
    message: str,
    details: Optional[dict] = None
) -> ErrorResponse:
    """
    Helper function to create error response
    
    Args:
        code: Error code
        message: Error message
        details: Optional error details
        
    Returns:
        ErrorResponse: Error response object
    """
    return ErrorResponse.create(code=code, message=message, details=details)