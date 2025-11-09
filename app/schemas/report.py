"""
CEMS Report Schemas
===================
Phase 8.2: Pydantic schemas for all report types
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


# ==================== FINANCIAL REPORT SCHEMAS ====================

class DailySummaryResponse(BaseModel):
    """Daily Transaction Summary Response"""
    date: date
    branch_id: Optional[str]
    branch_name: Optional[str]
    
    total_transactions: int
    volume_by_currency: Dict[str, float]
    total_revenue: float
    
    transaction_breakdown: Dict[str, int]  # by type
    
    top_transaction: Optional[Dict[str, Any]]
    busiest_hour: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-01-15",
                "branch_id": "BR001",
                "branch_name": "Main Branch",
                "total_transactions": 150,
                "volume_by_currency": {
                    "USD": 50000.00,
                    "YER": 12500000.00
                },
                "total_revenue": 5000.00,
                "transaction_breakdown": {
                    "EXCHANGE": 120,
                    "INCOME": 20,
                    "EXPENSE": 10
                },
                "busiest_hour": "14:00"
            }
        }


class MonthlyRevenueResponse(BaseModel):
    """Monthly Revenue Report Response"""
    year: int
    month: int
    branch_id: Optional[str]
    
    total_revenue: float
    revenue_by_source: Dict[str, float]
    daily_breakdown: List[Dict[str, Any]]
    
    comparison_previous_month: Optional[Dict[str, float]]
    top_revenue_days: List[Dict[str, Any]]
    
    average_daily_revenue: float
    growth_rate: Optional[float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2025,
                "month": 1,
                "total_revenue": 150000.00,
                "revenue_by_source": {
                    "exchange_commission": 120000.00,
                    "transfer_fees": 30000.00
                },
                "average_daily_revenue": 5000.00,
                "growth_rate": 15.5
            }
        }


class BranchPerformanceResponse(BaseModel):
    """Branch Performance Metrics"""
    branch_id: str
    branch_name: str
    
    total_transactions: int
    total_revenue: float
    average_transaction_value: float
    
    efficiency_score: float  # transactions per staff member
    customer_satisfaction: Optional[float]
    
    currency_breakdown: Dict[str, int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "branch_id": "BR001",
                "branch_name": "Main Branch",
                "total_transactions": 1500,
                "total_revenue": 50000.00,
                "average_transaction_value": 33.33,
                "efficiency_score": 75.0
            }
        }


class ExchangeTrendResponse(BaseModel):
    """Currency Exchange Rate Trends"""
    from_currency: str
    to_currency: str
    start_date: date
    end_date: date
    
    rate_history: List[Dict[str, Any]]
    
    average_rate: float
    highest_rate: float
    lowest_rate: float
    
    volatility: float  # Standard deviation
    trend: str  # "increasing", "decreasing", "stable"
    
    volume_by_rate: Dict[str, int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_currency": "USD",
                "to_currency": "YER",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "average_rate": 1250.00,
                "highest_rate": 1255.00,
                "lowest_rate": 1245.00,
                "volatility": 3.5,
                "trend": "stable"
            }
        }


# ==================== BALANCE REPORT SCHEMAS ====================

class BalanceSnapshotResponse(BaseModel):
    """Branch Balance Snapshot"""
    branch_id: str
    branch_name: str
    snapshot_date: date
    
    balances_by_currency: Dict[str, float]
    total_balance_base_currency: float
    
    changes_since_last: Optional[Dict[str, float]]
    alert_status: str  # "ok", "warning", "critical"
    
    class Config:
        json_schema_extra = {
            "example": {
                "branch_id": "BR001",
                "branch_name": "Main Branch",
                "snapshot_date": "2025-01-15",
                "balances_by_currency": {
                    "USD": 100000.00,
                    "YER": 125000000.00,
                    "SAR": 50000.00
                },
                "total_balance_base_currency": 150000.00,
                "alert_status": "ok"
            }
        }


class BalanceMovementResponse(BaseModel):
    """Balance Movement Over Period"""
    branch_id: str
    currency_code: str
    start_date: date
    end_date: date
    
    opening_balance: float
    total_inflows: float
    total_outflows: float
    closing_balance: float
    
    net_change: float
    daily_movements: List[Dict[str, Any]]
    
    largest_inflow: Optional[Dict[str, Any]]
    largest_outflow: Optional[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "branch_id": "BR001",
                "currency_code": "USD",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "opening_balance": 100000.00,
                "total_inflows": 50000.00,
                "total_outflows": 30000.00,
                "closing_balance": 120000.00,
                "net_change": 20000.00
            }
        }


class LowBalanceAlertResponse(BaseModel):
    """Low Balance Alert"""
    branch_id: str
    branch_name: str
    currency_code: str
    
    current_balance: float
    minimum_balance: float
    shortage: float
    
    severity: str  # "warning", "critical"
    recommended_action: str
    
    last_replenishment: Optional[datetime]
    
    class Config:
        json_schema_extra = {
            "example": {
                "branch_id": "BR002",
                "branch_name": "Downtown Branch",
                "currency_code": "USD",
                "current_balance": 5000.00,
                "minimum_balance": 10000.00,
                "shortage": 5000.00,
                "severity": "warning",
                "recommended_action": "Request vault transfer"
            }
        }


# ==================== USER ACTIVITY SCHEMAS ====================

class UserActivityResponse(BaseModel):
    """User Activity Report"""
    user_id: str
    username: str
    start_date: date
    end_date: date
    
    total_transactions: int
    transactions_by_type: Dict[str, int]
    
    total_amount_processed: float
    
    login_count: int
    average_session_duration: Optional[float]  # minutes
    
    activity_timeline: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "USR001",
                "username": "john.doe",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "total_transactions": 250,
                "transactions_by_type": {
                    "EXCHANGE": 200,
                    "TRANSFER": 50
                },
                "total_amount_processed": 500000.00,
                "login_count": 20
            }
        }


class AuditTrailResponse(BaseModel):
    """Audit Trail Entry"""
    audit_id: str
    entity_type: str
    entity_id: str
    
    action: str  # "CREATE", "UPDATE", "DELETE"
    changed_by: str
    changed_at: datetime
    
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": "AUD001",
                "entity_type": "transaction",
                "entity_id": "TXN001",
                "action": "UPDATE",
                "changed_by": "john.doe",
                "changed_at": "2025-01-15T14:30:00",
                "old_values": {"status": "PENDING"},
                "new_values": {"status": "COMPLETED"}
            }
        }


# ==================== EXPORT SCHEMAS ====================

class ReportExportRequest(BaseModel):
    """Request to Export a Report"""
    report_type: str = Field(..., description="Type of report to export")
    format: str = Field(..., description="Export format: json, excel, or pdf")
    
    filters: Dict[str, Any] = Field(default_factory=dict, description="Report filters")
    
    include_charts: bool = Field(default=False, description="Include charts in PDF/Excel")
    page_orientation: str = Field(default="portrait", description="PDF page orientation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "daily_summary",
                "format": "pdf",
                "filters": {
                    "branch_id": "BR001",
                    "date": "2025-01-15"
                },
                "include_charts": True,
                "page_orientation": "landscape"
            }
        }


class ReportExportResponse(BaseModel):
    """Report Export Response"""
    filename: str
    download_url: str
    
    file_size: int  # bytes
    format: str
    
    generated_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "daily_summary_20250115.pdf",
                "download_url": "/api/v1/reports/download/daily_summary_20250115.pdf",
                "file_size": 102400,
                "format": "pdf",
                "generated_at": "2025-01-15T15:00:00"
            }
        }


# ==================== DASHBOARD SCHEMAS ====================

class DashboardOverviewResponse(BaseModel):
    """Dashboard Overview Data"""
    total_transactions_today: int
    total_revenue_today: float
    active_branches: int
    low_balance_alerts: int
    pending_approvals: int
    
    top_currencies: List[Dict[str, Any]]
    quick_stats: Dict[str, Any]
    
    generated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_transactions_today": 150,
                "total_revenue_today": 5000.00,
                "active_branches": 5,
                "low_balance_alerts": 2,
                "pending_approvals": 3,
                "top_currencies": [
                    {"currency_code": "USD", "transaction_count": 80}
                ],
                "generated_at": "2025-01-15T15:00:00"
            }
        }


class ChartDataResponse(BaseModel):
    """Generic Chart Data Response"""
    chart_type: str  # "line", "bar", "pie", "area"
    period: Optional[str]
    
    data: List[Dict[str, Any]]
    
    metadata: Optional[Dict[str, Any]]
    generated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "chart_type": "line",
                "period": "daily",
                "data": [
                    {"date": "2025-01-01", "value": 100},
                    {"date": "2025-01-02", "value": 120}
                ],
                "generated_at": "2025-01-15T15:00:00"
            }
        }
