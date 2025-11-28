"""
Rate Sync Schemas
Pydantic schemas for rate synchronization endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


class ExternalSourceEnum(str, Enum):
    """Available external rate sources"""
    EXCHANGERATE_API = "exchangerate-api"
    FRANKFURTER = "frankfurter"
    AUTO = "auto"


class CurrencyPairRequest(BaseModel):
    """Currency pair specification"""
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")


class InitiateRateSyncRequest(BaseModel):
    """Request to initiate rate synchronization"""
    base_currency: str = Field(default="USD", min_length=3, max_length=3, description="Base currency for fetching")
    target_currencies: Optional[List[str]] = Field(None, description="Specific currencies to sync (None = all active)")
    source: ExternalSourceEnum = Field(default=ExternalSourceEnum.AUTO, description="External API source")
    specific_pair: Optional[CurrencyPairRequest] = Field(None, description="Sync only specific currency pair")

    class Config:
        json_schema_extra = {
            "example": {
                "base_currency": "USD",
                "target_currencies": ["EUR", "GBP", "TRY"],
                "source": "auto",
                "specific_pair": None
            }
        }


class RateComparisonData(BaseModel):
    """Comparison between current and fetched rates"""
    from_currency: str
    to_currency: str
    current_rate: Optional[str]
    fetched_rate: str
    change: Optional[str]
    change_percentage: Optional[str]
    source: str
    has_current: bool


class RateSyncResponse(BaseModel):
    """Response from rate sync initiation"""
    request_id: str
    status: str
    source: str
    base_currency: str
    rates_count: int
    expires_at: str
    rates: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "source": "exchangerate-api",
                "base_currency": "USD",
                "rates_count": 7,
                "expires_at": "2025-11-11T10:30:00",
                "rates": {
                    "USD/EUR": {
                        "from_currency": "USD",
                        "to_currency": "EUR",
                        "current_rate": "0.91",
                        "fetched_rate": "0.92",
                        "change": "0.01",
                        "change_percentage": "1.09",
                        "source": "exchangerate-api",
                        "has_current": True
                    }
                }
            }
        }


class RequestDetailsResponse(BaseModel):
    """Detailed information about a rate update request"""
    request_id: str
    status: str
    source: str
    base_currency: str
    requested_by: str
    requested_at: str
    expires_at: str
    is_expired: bool
    rates_count: int
    rates: Dict[str, Any]
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None
    rates_applied_count: Optional[int] = None


class ApproveRatesRequest(BaseModel):
    """Request to approve and apply rates"""
    notes: Optional[str] = Field(None, description="Approval notes")
    spread_percentage: Decimal = Field(default=Decimal("2.0"), ge=0, le=10, description="Buy/sell spread percentage")

    class Config:
        json_schema_extra = {
            "example": {
                "notes": "Rates look good, approved",
                "spread_percentage": 2.0
            }
        }


class ApproveRatesResponse(BaseModel):
    """Response from rate approval"""
    request_id: str
    status: str
    applied_count: int
    failed_count: int
    errors: Optional[List[str]] = None


class RejectRatesRequest(BaseModel):
    """Request to reject rates"""
    notes: Optional[str] = Field(None, description="Rejection reason")

    class Config:
        json_schema_extra = {
            "example": {
                "notes": "Rates seem inaccurate"
            }
        }


class RejectRatesResponse(BaseModel):
    """Response from rate rejection"""
    request_id: str
    status: str
    message: str


class PendingRequestsResponse(BaseModel):
    """List of pending requests"""
    count: int
    requests: List[Dict[str, Any]]
