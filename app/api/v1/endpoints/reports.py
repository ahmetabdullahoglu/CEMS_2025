"""
CEMS Report API Endpoints
=========================
Phase 8.2: Complete Report API with Export & Dashboard
"""

from datetime import date, datetime, timedelta
from typing import Optional, List
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import io
import os

from app.api.deps import (
    get_async_db,
    get_current_user,
    get_current_active_user,
    check_permission,
    require_roles
)
from app.db.base import get_db
from app.services.report_service import ReportService
from app.services.report_export_service import ReportExportService
from app.schemas.report import (
    DailySummaryResponse,
    MonthlyRevenueResponse,
    BranchPerformanceResponse,
    ExchangeTrendResponse,
    BalanceSnapshotResponse,
    BalanceMovementResponse,
    LowBalanceAlertResponse,
    UserActivityResponse,
    AuditTrailResponse,
    ReportExportRequest,
    ReportExportResponse
)
from app.db.models.user import User

router = APIRouter()


# ==================== FINANCIAL REPORTS ====================

@router.get("/daily-summary")
def get_daily_summary(
    branch_id: Optional[str] = Query(None, description="Branch ID (optional)"),
    target_date: Optional[date] = Query(None, description="Target date (default: today)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📊 Daily Transaction Summary Report"""
    check_permission(current_user, "view_reports")
    
    if current_user.role and current_user.role.name == "branch_manager" and not branch_id:
        branch_id = current_user.branch_id
    
    report_service = ReportService(db)
    
    try:
        summary = report_service.daily_transaction_summary(
            branch_id=branch_id,
            target_date=target_date or date.today()
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/monthly-revenue")
def get_monthly_revenue(
    branch_id: Optional[str] = Query(None),
    year: int = Query(..., description="Year (e.g., 2025)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """💰 Monthly Revenue Report"""
    check_permission(current_user, "view_reports")
    
    if current_user.role and current_user.role.name == "branch_manager" and not branch_id:
        branch_id = current_user.branch_id
    
    report_service = ReportService(db)
    
    try:
        revenue = report_service.monthly_revenue_report(
            branch_id=branch_id,
            year=year,
            month=month
        )
        return revenue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/branch-performance")
def get_branch_performance(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🏢 Branch Performance Comparison"""
    check_permission(current_user, "view_all_reports")
    
    report_service = ReportService(db)

    try:
        performance = report_service.branch_performance_comparison(
            start_date=start_date,
            end_date=end_date
        )
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/exchange-trends")
def get_exchange_trends(
    from_currency: str = Query(..., description="From currency code (e.g., USD)"),
    to_currency: str = Query(..., description="To currency code (e.g., YER)"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📈 Currency Exchange Rate Trends"""
    check_permission(current_user, "view_reports")
    
    report_service = ReportService(db)

    try:
        trends = report_service.currency_exchange_trends(
            currency_pair=(from_currency, to_currency),
            start_date=start_date,
            end_date=end_date
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# ==================== BALANCE REPORTS ====================

@router.get("/balance-snapshot")
def get_balance_snapshot(
    branch_id: Optional[str] = Query(None),
    snapshot_date: Optional[date] = Query(None, description="Snapshot date (default: today)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """💵 Branch Balance Snapshot"""
    check_permission(current_user, "view_balances")
    
    if current_user.role and current_user.role.name == "branch_manager" and not branch_id:
        branch_id = current_user.branch_id
    
    if not branch_id:
        raise HTTPException(status_code=400, detail="branch_id is required")
    
    report_service = ReportService(db)
    
    try:
        snapshot = report_service.branch_balance_snapshot(
            branch_id=branch_id,
            snapshot_date=snapshot_date or date.today()
        )
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/balance-movement")
def get_balance_movement(
    branch_id: str = Query(...),
    currency_code: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📊 Balance Movement Report"""
    check_permission(current_user, "view_balances")
    
    if current_user.role and current_user.role.name == "branch_manager" and branch_id != current_user.branch_id:
        raise HTTPException(status_code=403, detail="Access denied to this branch")
    
    report_service = ReportService(db)

    try:
        movement = report_service.balance_movement_report(
            branch_id=branch_id,
            currency_code=currency_code,
            start_date=start_date,
            end_date=end_date
        )
        return movement
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/low-balance-alerts")
def get_low_balance_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """⚠️ Low Balance Alerts"""
    check_permission(current_user, "view_balances")
    
    report_service = ReportService(db)
    
    try:
        alerts = report_service.low_balance_alert_report()
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# ==================== USER ACTIVITY REPORTS ====================

@router.get("/user-activity")
def get_user_activity(
    user_id: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """👤 User Activity Report"""
    if current_user.id != user_id:
        check_permission(current_user, "view_all_reports")
    
    report_service = ReportService(db)

    try:
        activity = report_service.user_activity_log(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        return activity
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/audit-trail")
def get_audit_trail(
    entity_type: str = Query(..., description="Entity type (e.g., transaction, branch, user)"),
    entity_id: str = Query(..., description="Entity ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📋 Audit Trail Report"""
    check_permission(current_user, "view_audit_logs")
    
    report_service = ReportService(db)

    try:
        audit_trail = report_service.audit_trail_report(
            entity_type=entity_type,
            entity_id=entity_id,
            start_date=None,
            end_date=None
        )
        return audit_trail
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# ==================== REPORT EXPORT ====================

@router.post("/export")
def export_report(
    report_type: str,
    format: str,
    filters: dict = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📥 Export Report to File (JSON/Excel/PDF)"""
    check_permission(current_user, "export_reports")
    
    report_service = ReportService(db)
    export_service = ReportExportService()
    
    try:
        # Generate report data
        if report_type == "daily_summary":
            report_data = report_service.daily_transaction_summary(
                branch_id=filters.get("branch_id"),
                target_date=filters.get("date")
            )
        elif report_type == "monthly_revenue":
            report_data = report_service.monthly_revenue_report(
                branch_id=filters.get("branch_id"),
                year=filters.get("year"),
                month=filters.get("month")
            )
        elif report_type == "branch_performance":
            report_data = report_service.branch_performance_comparison(
                start_date=filters.get("start_date"),
                end_date=filters.get("end_date")
            )
        elif report_type == "balance_snapshot":
            report_data = report_service.branch_balance_snapshot(
                branch_id=filters.get("branch_id"),
                snapshot_date=filters.get("date"),
                target_date=filters.get("target_date")
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
        
        # Export to format
        filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == "json":
            content = export_service.export_to_json(report_data, pretty=True)
            filename += ".json"
            media_type = "application/json"
            
        elif format == "excel":
            content = export_service.export_to_excel(report_data)
            filename += ".xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
        elif format == "pdf":
            content = export_service.export_to_pdf(report_data)
            filename += ".pdf"
            media_type = "application/pdf"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        if isinstance(content, BytesIO):
            content_bytes = content.getvalue()
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            content_bytes = str(content).encode()

        # Return file
        return StreamingResponse(
            io.BytesIO(content_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
