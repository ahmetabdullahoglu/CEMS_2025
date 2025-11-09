"""
CEMS Dashboard API
==================
Phase 8.2: Real-time Dashboard Data & Charts
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.security import get_current_user, require_permission
from app.db.base import get_db
from app.services.report_service import ReportService
from app.db.models.user import User
from app.db.models.transaction import Transaction, TransactionStatus, TransactionType
from app.db.models.branch import Branch, BranchBalance
from app.db.models.currency import Currency

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    branch_id: Optional[str] = Query(None, description="Branch ID (optional)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🏠 Dashboard Overview - Main KPIs
    
    **Returns:**
    - Today's transaction count & revenue
    - Active branches count
    - Low balance alerts
    - Pending approvals
    - Top currencies by volume
    - Quick stats
    """
    
    # Branch managers can only see their branch
    if current_user.role.name == "branch_manager" and not branch_id:
        branch_id = current_user.branch_id
    
    today = date.today()
    
    # Build transaction query
    txn_query = db.query(Transaction).filter(
        func.date(Transaction.transaction_date) == today,
        Transaction.status == TransactionStatus.COMPLETED
    )
    
    if branch_id:
        txn_query = txn_query.filter(Transaction.branch_id == branch_id)
    
    transactions_today = txn_query.all()
    
    # Calculate today's metrics
    total_transactions_today = len(transactions_today)
    total_revenue_today = sum(
        txn.commission_amount for txn in transactions_today 
        if txn.commission_amount
    )
    
    # Active branches
    if branch_id:
        active_branches = 1
    else:
        active_branches = db.query(Branch).filter(Branch.is_active == True).count()
    
    # Low balance alerts
    report_service = ReportService(db)
    low_balance_alerts = len(report_service.low_balance_alert_report())
    
    # Pending approvals (transactions requiring approval)
    pending_approvals = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.PENDING
    ).count()
    
    # Top currencies by transaction volume today
    currency_volumes = {}
    for txn in transactions_today:
        currency = txn.source_currency_code
        if currency not in currency_volumes:
            currency_volumes[currency] = {
                'count': 0,
                'total_amount': 0
            }
        currency_volumes[currency]['count'] += 1
        currency_volumes[currency]['total_amount'] += float(txn.source_amount)
    
    top_currencies = sorted(
        currency_volumes.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:5]
    
    # Quick stats
    yesterday = today - timedelta(days=1)
    txn_yesterday = db.query(Transaction).filter(
        func.date(Transaction.transaction_date) == yesterday,
        Transaction.status == TransactionStatus.COMPLETED
    )
    
    if branch_id:
        txn_yesterday = txn_yesterday.filter(Transaction.branch_id == branch_id)
    
    transactions_yesterday = txn_yesterday.count()
    
    # Calculate growth
    if transactions_yesterday > 0:
        transaction_growth = ((total_transactions_today - transactions_yesterday) / transactions_yesterday) * 100
    else:
        transaction_growth = 100.0 if total_transactions_today > 0 else 0.0
    
    return {
        "overview": {
            "total_transactions_today": total_transactions_today,
            "total_revenue_today": float(total_revenue_today),
            "active_branches": active_branches,
            "low_balance_alerts": low_balance_alerts,
            "pending_approvals": pending_approvals,
            "transaction_growth_percent": round(transaction_growth, 2)
        },
        "top_currencies": [
            {
                "currency_code": code,
                "transaction_count": data['count'],
                "total_volume": round(data['total_amount'], 2)
            }
            for code, data in top_currencies
        ],
        "quick_stats": {
            "transactions_yesterday": transactions_yesterday,
            "average_transaction_value": round(total_revenue_today / total_transactions_today, 2) if total_transactions_today > 0 else 0,
            "busiest_hour": _get_busiest_hour(transactions_today) if transactions_today else "N/A"
        },
        "generated_at": datetime.now().isoformat()
    }


@router.get("/charts/transaction-volume")
async def get_transaction_volume_chart(
    period: str = Query("daily", description="daily, weekly, or monthly"),
    branch_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📊 Transaction Volume Chart Data
    
    **Periods:**
    - daily: Last 30 days
    - weekly: Last 12 weeks
    - monthly: Last 12 months
    
    **Returns:**
    Chart data ready for frontend visualization
    """
    
    if current_user.role.name == "branch_manager" and not branch_id:
        branch_id = current_user.branch_id
    
    today = date.today()
    
    if period == "daily":
        # Last 30 days
        start_date = today - timedelta(days=30)
        data = _get_daily_volume(db, start_date, today, branch_id)
        
    elif period == "weekly":
        # Last 12 weeks
        start_date = today - timedelta(weeks=12)
        data = _get_weekly_volume(db, start_date, today, branch_id)
        
    elif period == "monthly":
        # Last 12 months
        start_date = today - timedelta(days=365)
        data = _get_monthly_volume(db, start_date, today, branch_id)
        
    else:
        raise HTTPException(status_code=400, detail="Invalid period. Use: daily, weekly, or monthly")
    
    return {
        "period": period,
        "chart_type": "line",
        "data": data,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/charts/revenue-trend")
async def get_revenue_trend_chart(
    period: str = Query("monthly", description="monthly or yearly"),
    branch_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    💰 Revenue Trend Chart
    
    **Returns:**
    Monthly or yearly revenue trends
    """
    
    if current_user.role.name == "branch_manager" and not branch_id:
        branch_id = current_user.branch_id
    
    report_service = ReportService(db)
    today = date.today()
    
    if period == "monthly":
        # Last 12 months
        data = []
        for i in range(11, -1, -1):
            month_date = today - timedelta(days=30*i)
            revenue = report_service.monthly_revenue_report(
                branch_id=branch_id,
                year=month_date.year,
                month=month_date.month
            )
            data.append({
                "period": month_date.strftime("%Y-%m"),
                "revenue": float(revenue.get('total_revenue', 0))
            })
    
    elif period == "yearly":
        # Last 3 years
        data = []
        current_year = today.year
        for year in range(current_year - 2, current_year + 1):
            yearly_revenue = 0
            for month in range(1, 13):
                try:
                    revenue = report_service.monthly_revenue_report(
                        branch_id=branch_id,
                        year=year,
                        month=month
                    )
                    yearly_revenue += float(revenue.get('total_revenue', 0))
                except:
                    pass
            
            data.append({
                "period": str(year),
                "revenue": yearly_revenue
            })
    
    else:
        raise HTTPException(status_code=400, detail="Invalid period. Use: monthly or yearly")
    
    return {
        "period": period,
        "chart_type": "area",
        "data": data,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/charts/currency-distribution")
async def get_currency_distribution_chart(
    branch_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze (1-90)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🥧 Currency Distribution Pie Chart
    
    **Returns:**
    Transaction volume distribution by currency
    """
    
    if current_user.role.name == "branch_manager" and not branch_id:
        branch_id = current_user.branch_id
    
    start_date = date.today() - timedelta(days=days)
    
    # Query transactions
    query = db.query(
        Transaction.source_currency_code,
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.source_amount).label('total_amount')
    ).filter(
        Transaction.transaction_date >= start_date,
        Transaction.status == TransactionStatus.COMPLETED
    )
    
    if branch_id:
        query = query.filter(Transaction.branch_id == branch_id)
    
    results = query.group_by(Transaction.source_currency_code).all()
    
    # Format for pie chart
    data = [
        {
            "currency": row.source_currency_code,
            "count": row.count,
            "percentage": 0  # Will calculate below
        }
        for row in results
    ]
    
    total_count = sum(item['count'] for item in data)
    for item in data:
        item['percentage'] = round((item['count'] / total_count * 100), 2) if total_count > 0 else 0
    
    # Sort by count descending
    data.sort(key=lambda x: x['count'], reverse=True)
    
    return {
        "chart_type": "pie",
        "period_days": days,
        "data": data,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/charts/branch-comparison")
async def get_branch_comparison_chart(
    metric: str = Query("transactions", description="transactions, revenue, or efficiency"),
    period_days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🏢 Branch Comparison Bar Chart
    
    **Metrics:**
    - transactions: Total transaction count
    - revenue: Total revenue generated
    - efficiency: Transactions per staff member
    
    **Permissions:** Admin only
    """
    
    require_permission(current_user, "view_all_reports")
    
    start_date = date.today() - timedelta(days=period_days)
    
    branches = db.query(Branch).filter(Branch.is_active == True).all()
    
    data = []
    
    for branch in branches:
        # Get transactions for this branch
        txns = db.query(Transaction).filter(
            Transaction.branch_id == branch.id,
            Transaction.transaction_date >= start_date,
            Transaction.status == TransactionStatus.COMPLETED
        ).all()
        
        if metric == "transactions":
            value = len(txns)
            
        elif metric == "revenue":
            value = sum(txn.commission_amount for txn in txns if txn.commission_amount)
            value = float(value)
            
        elif metric == "efficiency":
            # Transactions per staff (assuming staff count in branch model)
            staff_count = getattr(branch, 'staff_count', 1)
            value = len(txns) / staff_count if staff_count > 0 else 0
            
        else:
            raise HTTPException(status_code=400, detail="Invalid metric. Use: transactions, revenue, or efficiency")
        
        data.append({
            "branch_name": branch.name,
            "branch_code": branch.code,
            "value": round(value, 2)
        })
    
    # Sort by value descending
    data.sort(key=lambda x: x['value'], reverse=True)
    
    return {
        "chart_type": "bar",
        "metric": metric,
        "period_days": period_days,
        "data": data,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/alerts")
async def get_dashboard_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔔 Dashboard Alerts & Notifications
    
    **Returns:**
    - Critical alerts
    - Warnings
    - Info notifications
    """
    
    report_service = ReportService(db)
    
    alerts = {
        "critical": [],
        "warning": [],
        "info": []
    }
    
    # Low balance alerts
    low_balances = report_service.low_balance_alert_report()
    for alert in low_balances:
        severity = alert.get('severity', 'warning')
        alerts[severity].append({
            "type": "low_balance",
            "message": f"Low balance in {alert['branch_name']} - {alert['currency_code']}: {alert['current_balance']}",
            "timestamp": datetime.now().isoformat()
        })
    
    # Pending approvals
    pending_count = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.PENDING
    ).count()
    
    if pending_count > 0:
        alerts["warning"].append({
            "type": "pending_approvals",
            "message": f"{pending_count} transactions pending approval",
            "count": pending_count,
            "timestamp": datetime.now().isoformat()
        })
    
    # High volume alert (if today's transactions > 2x daily average)
    # This is a simplified version
    today_count = db.query(Transaction).filter(
        func.date(Transaction.transaction_date) == date.today()
    ).count()
    
    if today_count > 100:  # Example threshold
        alerts["info"].append({
            "type": "high_volume",
            "message": f"High transaction volume today: {today_count} transactions",
            "timestamp": datetime.now().isoformat()
        })
    
    return alerts


# ==================== HELPER FUNCTIONS ====================

def _get_busiest_hour(transactions: List[Transaction]) -> str:
    """Find the hour with most transactions"""
    hour_counts = {}
    for txn in transactions:
        hour = txn.transaction_date.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    if not hour_counts:
        return "N/A"
    
    busiest_hour = max(hour_counts, key=hour_counts.get)
    return f"{busiest_hour:02d}:00"


def _get_daily_volume(db: Session, start_date: date, end_date: date, branch_id: Optional[str]) -> List[Dict]:
    """Get daily transaction volume"""
    query = db.query(
        func.date(Transaction.transaction_date).label('date'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == TransactionStatus.COMPLETED
    )
    
    if branch_id:
        query = query.filter(Transaction.branch_id == branch_id)
    
    results = query.group_by(func.date(Transaction.transaction_date)).all()
    
    return [
        {
            "date": row.date.isoformat(),
            "value": row.count
        }
        for row in results
    ]


def _get_weekly_volume(db: Session, start_date: date, end_date: date, branch_id: Optional[str]) -> List[Dict]:
    """Get weekly transaction volume"""
    query = db.query(
        func.extract('week', Transaction.transaction_date).label('week'),
        func.extract('year', Transaction.transaction_date).label('year'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == TransactionStatus.COMPLETED
    )
    
    if branch_id:
        query = query.filter(Transaction.branch_id == branch_id)
    
    results = query.group_by('week', 'year').all()
    
    return [
        {
            "period": f"{int(row.year)}-W{int(row.week):02d}",
            "value": row.count
        }
        for row in results
    ]


def _get_monthly_volume(db: Session, start_date: date, end_date: date, branch_id: Optional[str]) -> List[Dict]:
    """Get monthly transaction volume"""
    query = db.query(
        func.extract('month', Transaction.transaction_date).label('month'),
        func.extract('year', Transaction.transaction_date).label('year'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == TransactionStatus.COMPLETED
    )
    
    if branch_id:
        query = query.filter(Transaction.branch_id == branch_id)
    
    results = query.group_by('month', 'year').all()
    
    return [
        {
            "period": f"{int(row.year)}-{int(row.month):02d}",
            "value": row.count
        }
        for row in results
    ]
