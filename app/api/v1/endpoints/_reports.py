"""
CEMS Reports API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from decimal import Decimal

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services.report_service import ReportService
from app.services.report_export_service import ReportExportService, get_export_filename
from app.core.permissions import check_permission

router = APIRouter(prefix="/reports", tags=["reports"])


# ==================== FINANCIAL REPORTS ====================

@router.get("/daily-summary")
async def get_daily_summary(
    branch_id: Optional[str] = None,
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily transaction summary"""
    # Permission check
    if not check_permission(current_user, "reports:view_branch"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    service = ReportService(db)
    report = service.daily_transaction_summary(
        branch_id=branch_id,
        target_date=target_date
    )
    
    return report


@router.get("/monthly-revenue")
async def get_monthly_revenue(
    branch_id: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get monthly revenue report"""
    service = ReportService(db)
    report = service.monthly_revenue_report(
        branch_id=branch_id,
        year=year,
        month=month
    )
    
    return report


@router.get("/branch-performance")
async def get_branch_performance(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare branch performance"""
    # Requires admin permission
    if not check_permission(current_user, "reports:view_all"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = ReportService(db)
    report = service.branch_performance_comparison(
        start_date=start_date,
        end_date=end_date
    )
    
    return report


@router.get("/exchange-trends")
async def get_exchange_trends(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze currency exchange trends"""
    service = ReportService(db)
    report = service.currency_exchange_trends(
        currency_pair=(from_currency, to_currency),
        start_date=start_date,
        end_date=end_date
    )
    
    return report


@router.get("/customer-analysis/{customer_id}")
async def get_customer_analysis(
    customer_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze customer transactions"""
    service = ReportService(db)
    report = service.customer_transaction_analysis(
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return report


# ==================== BALANCE REPORTS ====================

@router.get("/balance-snapshot/{branch_id}")
async def get_balance_snapshot(
    branch_id: str,
    snapshot_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get branch balance snapshot"""
    service = ReportService(db)
    report = service.branch_balance_snapshot(
        branch_id=branch_id,
        snapshot_date=snapshot_date
    )
    
    return report


@router.get("/vault-summary")
async def get_vault_summary(
    snapshot_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vault balance summary"""
    # Requires vault access
    if not check_permission(current_user, "vault:read"):
        raise HTTPException(status_code=403, detail="Vault access required")
    
    service = ReportService(db)
    report = service.vault_balance_summary(snapshot_date)
    
    return report


@router.get("/low-balance-alerts")
async def get_low_balance_alerts(
    threshold_percentage: float = Query(20.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get low balance alerts"""
    service = ReportService(db)
    report = service.low_balance_alert_report(threshold_percentage)
    
    return report


@router.get("/balance-movement")
async def get_balance_movement(
    branch_id: str = Query(...),
    currency_code: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track balance movements"""
    service = ReportService(db)
    report = service.balance_movement_report(
        branch_id=branch_id,
        currency_code=currency_code,
        start_date=start_date,
        end_date=end_date
    )
    
    return report


# ==================== USER ACTIVITY REPORTS ====================

@router.get("/user-activity/{user_id}")
async def get_user_activity(
    user_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user activity log"""
    # Users can see their own activity, admins can see all
    if user_id != str(current_user.id) and not check_permission(current_user, "reports:view_all"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    service = ReportService(db)
    report = service.user_activity_log(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return report


@router.get("/user-transactions/{user_id}")
async def get_user_transactions(
    user_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transactions by user"""
    service = ReportService(db)
    report = service.transaction_by_user(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return report


@router.get("/audit-trail/{entity_type}/{entity_id}")
async def get_audit_trail(
    entity_type: str,
    entity_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get entity audit trail"""
    # Requires admin access
    if not check_permission(current_user, "reports:view_all"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = ReportService(db)
    report = service.audit_trail_report(
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return report


# ==================== ANALYTICS ====================

@router.get("/commission-earned")
async def get_commission_earned(
    branch_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate commission earned"""
    service = ReportService(db)
    report = service.calculate_commission_earned(
        branch_id=branch_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return report


@router.get("/high-value-customers")
async def get_high_value_customers(
    branch_id: Optional[str] = None,
    min_transaction_value: Decimal = Query(Decimal("10000")),
    period_days: int = Query(90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Identify high-value customers"""
    service = ReportService(db)
    report = service.identify_high_value_customers(
        branch_id=branch_id,
        min_transaction_value=min_transaction_value,
        period_days=period_days
    )
    
    return report


@router.get("/volume-trends")
async def get_volume_trends(
    branch_id: Optional[str] = None,
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze transaction volume trends"""
    service = ReportService(db)
    report = service.transaction_volume_trends(
        branch_id=branch_id,
        period=period
    )
    
    return report


@router.get("/rate-volatility")
async def get_rate_volatility(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    period_days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze exchange rate volatility"""
    service = ReportService(db)
    report = service.exchange_rate_volatility_analysis(
        currency_pair=(from_currency, to_currency),
        period_days=period_days
    )
    
    return report


# ==================== EXPORT ENDPOINT ====================

from pydantic import BaseModel

class ExportRequest(BaseModel):
    report_type: str
    format: str  # json, xlsx, pdf
    filters: dict


@router.post("/export")
async def export_report(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export report in specified format"""
    service = ReportService(db)
    export_service = ReportExportService()
    
    # Generate report based on type
    report_data = None
    
    if request.report_type == "daily_summary":
        report_data = service.daily_transaction_summary(**request.filters)
    elif request.report_type == "monthly_revenue":
        report_data = service.monthly_revenue_report(**request.filters)
    elif request.report_type == "branch_performance":
        report_data = service.branch_performance_comparison(**request.filters)
    # ... handle other types
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    # Export in requested format
    if request.format == "json":
        output = export_service.export_to_json(report_data)
        return {"content": output, "mime_type": "application/json"}
    
    elif request.format == "xlsx":
        output = export_service.export_to_excel(report_data, template='standard')
        filename = get_export_filename(request.report_type, 'xlsx')
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif request.format == "pdf":
        output = export_service.export_to_pdf(report_data)
        filename = get_export_filename(request.report_type, 'pdf')
        
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")