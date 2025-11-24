"""
CEMS Report Service - خدمة التقارير الشاملة
===========================================
Phase 8.1: Report Service with all calculations
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import func, and_, or_, case
from sqlalchemy.orm import Session

from app.db.models.transaction import Transaction, TransactionType, TransactionStatus
from app.db.models.branch import Branch, BranchBalance
from app.db.models.vault import Vault, VaultBalance, VaultTransfer, VaultTransferStatus
from app.db.models.currency import Currency, ExchangeRate
from app.db.models.customer import Customer
from app.db.models.user import User
from app.db.models.audit import AuditLog
from app.core.exceptions import ReportGenerationError


class ReportService:
    """خدمة التقارير - Financial, Balance, User Activity, Analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== FINANCIAL REPORTS ====================
    
    def daily_transaction_summary(
        self,
        branch_id: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        ملخص المعاملات اليومية
        Daily transaction summary for a branch or all branches
        
        Returns:
            - Total transactions count
            - Total volume by currency
            - Revenue/commission earned
            - Transaction breakdown by type
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            # Base query
            query = self.db.query(Transaction).filter(
                func.date(Transaction.transaction_date) == target_date,
                Transaction.status == TransactionStatus.COMPLETED
            )
            
            if branch_id:
                query = query.filter(Transaction.branch_id == branch_id)
            
            transactions = query.all()
            
            # Calculate metrics
            total_count = len(transactions)
            
            # Group by currency
            volume_by_currency = {}
            revenue_by_type = {
                'exchange': Decimal('0'),
                'income': Decimal('0'),
                'expense': Decimal('0'),
                'transfer': Decimal('0')
            }
            
            type_breakdown = {
                TransactionType.EXCHANGE: 0,
                TransactionType.INCOME: 0,
                TransactionType.EXPENSE: 0,
                TransactionType.TRANSFER: 0
            }
            
            for txn in transactions:
                # Volume tracking
                currency_code = txn.source_currency.code if txn.source_currency else 'UNK'
                if currency_code not in volume_by_currency:
                    volume_by_currency[currency_code] = Decimal('0')
                volume_by_currency[currency_code] += txn.source_amount or Decimal('0')

                # Revenue tracking
                if txn.commission_amount:
                    revenue_by_type[txn.transaction_type.value] += txn.commission_amount
                
                # Type breakdown
                type_breakdown[txn.transaction_type] += 1
            
            total_revenue = sum(revenue_by_type.values())
            
            return {
                'date': target_date.isoformat(),
                'branch_id': branch_id,
                'total_transactions': total_count,
                'total_revenue': float(total_revenue),
                'volume_by_currency': {k: float(v) for k, v in volume_by_currency.items()},
                'revenue_by_type': {k: float(v) for k, v in revenue_by_type.items()},
                'transaction_breakdown': {k.value: v for k, v in type_breakdown.items()},
                'average_commission': float(total_revenue / total_count) if total_count > 0 else 0
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate daily summary: {str(e)}")
    
    def monthly_revenue_report(
        self,
        branch_id: Optional[str] = None,
        year: int = None,
        month: int = None
    ) -> Dict[str, Any]:
        """
        تقرير الإيرادات الشهري
        Monthly revenue report with daily breakdown
        """
        try:
            if year is None:
                year = date.today().year
            if month is None:
                month = date.today().month
            
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            # Query transactions for the month
            query = self.db.query(Transaction).filter(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date < end_date,
                Transaction.status == TransactionStatus.COMPLETED
            )
            
            if branch_id:
                query = query.filter(Transaction.branch_id == branch_id)
            
            transactions = query.all()
            
            # Daily breakdown
            daily_revenue = {}
            total_revenue = Decimal('0')
            total_transactions = len(transactions)
            
            for txn in transactions:
                day = txn.transaction_date.day
                if day not in daily_revenue:
                    daily_revenue[day] = {
                        'revenue': Decimal('0'),
                        'count': 0
                    }

                if txn.commission_amount:
                    daily_revenue[day]['revenue'] += txn.commission_amount
                    total_revenue += txn.commission_amount
                daily_revenue[day]['count'] += 1
            
            # Calculate statistics
            revenue_list = [v['revenue'] for v in daily_revenue.values()]
            avg_daily_revenue = total_revenue / len(daily_revenue) if daily_revenue else Decimal('0')
            max_revenue = max(revenue_list) if revenue_list else Decimal('0')
            min_revenue = min(revenue_list) if revenue_list else Decimal('0')
            
            return {
                'year': year,
                'month': month,
                'branch_id': branch_id,
                'total_revenue': float(total_revenue),
                'total_transactions': total_transactions,
                'average_daily_revenue': float(avg_daily_revenue),
                'max_daily_revenue': float(max_revenue),
                'min_daily_revenue': float(min_revenue),
                'daily_breakdown': {
                    day: {
                        'revenue': float(data['revenue']),
                        'count': data['count']
                    }
                    for day, data in daily_revenue.items()
                }
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate monthly revenue: {str(e)}")
    
    def branch_performance_comparison(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        مقارنة أداء الفروع
        Compare performance across all branches
        """
        try:
            branches = self.db.query(Branch).filter(Branch.is_active == True).all()
            
            comparison_data = []
            
            for branch in branches:
                # Get transactions for this branch
                transactions = self.db.query(Transaction).filter(
                    Transaction.branch_id == branch.id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.status == TransactionStatus.COMPLETED
                ).all()
                
                total_revenue = sum(txn.commission_amount or Decimal('0') for txn in transactions)
                total_count = len(transactions)
                
                comparison_data.append({
                    'branch_id': str(branch.id),
                    'branch_code': branch.code,
                    'branch_name': branch.name,
                    'total_transactions': total_count,
                    'total_revenue': float(total_revenue),
                    'avg_transaction_value': float(total_revenue / total_count) if total_count > 0 else 0
                })
            
            # Sort by revenue
            comparison_data.sort(key=lambda x: x['total_revenue'], reverse=True)
            
            # Add rankings
            for idx, branch_data in enumerate(comparison_data, 1):
                branch_data['rank'] = idx
            
            total_system_revenue = sum(b['total_revenue'] for b in comparison_data)
            
            return {
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_system_revenue': total_system_revenue,
                'branch_count': len(comparison_data),
                'branches': comparison_data
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate branch comparison: {str(e)}")
    
    def currency_exchange_trends(
        self,
        currency_pair: Tuple[str, str],  # (from_currency, to_currency)
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        اتجاهات صرف العملات
        Currency exchange trends analysis
        """
        try:
            from_currency_code, to_currency_code = currency_pair
            
            # Get exchange transactions
            from app.db.models.transaction import ExchangeTransaction

            transactions = self.db.query(ExchangeTransaction).join(
                Currency, ExchangeTransaction.from_currency_id == Currency.id
            ).filter(
                ExchangeTransaction.transaction_date >= start_date,
                ExchangeTransaction.transaction_date <= end_date,
                ExchangeTransaction.status == TransactionStatus.COMPLETED,
                Currency.code == from_currency_code
            ).all()
            
            # Filter for target currency
            relevant_txns = [
                txn for txn in transactions 
                if txn.target_currency and txn.target_currency.code == to_currency_code
            ]
            
            if not relevant_txns:
                return {
                    'currency_pair': f"{from_currency_code}/{to_currency_code}",
                    'message': 'No data available for this period'
                }
            
            # Daily analysis
            daily_data = {}
            for txn in relevant_txns:
                day = txn.transaction_date
                if day not in daily_data:
                    daily_data[day] = {
                        'count': 0,
                        'total_source': Decimal('0'),
                        'total_target': Decimal('0'),
                        'rates': []
                    }
                
                daily_data[day]['count'] += 1
                daily_data[day]['total_source'] += txn.source_amount or Decimal('0')
                daily_data[day]['total_target'] += txn.target_amount or Decimal('0')
                if txn.exchange_rate:
                    daily_data[day]['rates'].append(txn.exchange_rate)
            
            # Calculate daily averages
            trend_data = []
            for day, data in sorted(daily_data.items()):
                avg_rate = sum(data['rates']) / len(data['rates']) if data['rates'] else Decimal('0')
                trend_data.append({
                    'date': day.isoformat(),
                    'transaction_count': data['count'],
                    'total_volume': float(data['total_source']),
                    'average_rate': float(avg_rate)
                })
            
            # Overall statistics
            all_rates = [r for data in daily_data.values() for r in data['rates']]
            total_volume = sum(data['total_source'] for data in daily_data.values())
            
            return {
                'currency_pair': f"{from_currency_code}/{to_currency_code}",
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_transactions': len(relevant_txns),
                'total_volume': float(total_volume),
                'average_rate': float(sum(all_rates) / len(all_rates)) if all_rates else 0,
                'min_rate': float(min(all_rates)) if all_rates else 0,
                'max_rate': float(max(all_rates)) if all_rates else 0,
                'daily_trends': trend_data
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate exchange trends: {str(e)}")
    
    def customer_transaction_analysis(
        self,
        customer_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        تحليل معاملات العميل
        Customer transaction history analysis
        """
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ReportGenerationError("Customer not found")
            
            transactions = self.db.query(Transaction).filter(
                Transaction.customer_id == customer_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.status == TransactionStatus.COMPLETED
            ).all()
            
            # Analysis
            total_count = len(transactions)
            transaction_types = {}
            currencies_used = set()
            total_volume = Decimal('0')
            
            monthly_breakdown = {}
            
            for txn in transactions:
                # Type breakdown
                txn_type = txn.transaction_type.value
                transaction_types[txn_type] = transaction_types.get(txn_type, 0) + 1
                
                # Currencies
                if txn.source_currency:
                    currencies_used.add(txn.source_currency.code)
                
                # Volume
                total_volume += txn.source_amount or Decimal('0')
                
                # Monthly breakdown
                month_key = txn.transaction_date.strftime('%Y-%m')
                if month_key not in monthly_breakdown:
                    monthly_breakdown[month_key] = {
                        'count': 0,
                        'volume': Decimal('0')
                    }
                monthly_breakdown[month_key]['count'] += 1
                monthly_breakdown[month_key]['volume'] += txn.source_amount or Decimal('0')
            
            return {
                'customer': {
                    'id': str(customer.id),
                    'full_name': customer.full_name,
                    'customer_number': customer.customer_number
                },
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_transactions': total_count,
                    'total_volume': float(total_volume),
                    'currencies_used': list(currencies_used),
                    'transaction_types': transaction_types
                },
                'monthly_breakdown': {
                    month: {
                        'count': data['count'],
                        'volume': float(data['volume'])
                    }
                    for month, data in sorted(monthly_breakdown.items())
                }
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to analyze customer transactions: {str(e)}")
    
    # ==================== BALANCE REPORTS ====================
    
    def branch_balance_snapshot(
        self,
        branch_id: str,
        snapshot_date: Optional[date] = None,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        لقطة رصيد الفرع
        Branch balance snapshot at a specific date
        """
        try:
            # Support both "snapshot_date" (current API) and legacy "target_date"
            snapshot_date = snapshot_date or target_date or date.today()
            
            branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
            if not branch:
                raise ReportGenerationError("Branch not found")
            
            balances = self.db.query(BranchBalance).filter(
                BranchBalance.branch_id == branch_id
            ).all()
            
            balance_data = []
            total_value_usd = Decimal('0')  # Assuming USD as base
            
            for balance in balances:
                currency = balance.currency
                balance_data.append({
                    'currency_code': currency.code,
                    'currency_name': currency.name,
                    'balance': float(balance.balance),
                    'last_updated': balance.last_updated.isoformat() if balance.last_updated else None
                })
                
                # Convert to USD for total (simplified - would need exchange rates)
                # total_value_usd += balance.balance * exchange_rate
            
            return {
                'branch': {
                    'id': str(branch.id),
                    'code': branch.code,
                    'name': branch.name
                },
                'snapshot_date': snapshot_date.isoformat(),
                'balances': balance_data,
                'currency_count': len(balance_data)
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate balance snapshot: {str(e)}")
    
    def vault_balance_summary(
        self,
        snapshot_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        ملخص رصيد الخزينة
        Main vault balance summary
        """
        try:
            if snapshot_date is None:
                snapshot_date = date.today()
            
            # Get main vault
            main_vault = self.db.query(Vault).filter(
                Vault.vault_type == 'main',
                Vault.is_active == True
            ).first()
            
            if not main_vault:
                raise ReportGenerationError("Main vault not found")
            
            balances = self.db.query(VaultBalance).filter(
                VaultBalance.vault_id == main_vault.id
            ).all()
            
            balance_data = []
            for balance in balances:
                balance_data.append({
                    'currency_code': balance.currency.code if balance.currency else 'UNK',
                    'currency_name': balance.currency.name if balance.currency else 'Unknown',
                    'balance': float(balance.balance),
                    'last_updated': balance.last_updated.isoformat() if balance.last_updated else None
                })
            
            return {
                'vault': {
                    'id': str(main_vault.id),
                    'type': main_vault.vault_type
                },
                'snapshot_date': snapshot_date.isoformat(),
                'balances': balance_data,
                'currency_count': len(balance_data)
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate vault summary: {str(e)}")
    
    def low_balance_alert_report(
        self,
        threshold_percentage: float = 20.0
    ) -> Dict[str, Any]:
        """
        تقرير تنبيهات الرصيد المنخفض
        Low balance alerts for branches
        """
        try:
            alerts = []
            
            branches = self.db.query(Branch).filter(Branch.is_active == True).all()
            
            for branch in branches:
                balances = self.db.query(BranchBalance).filter(
                    BranchBalance.branch_id == branch.id
                ).all()
                
                for balance in balances:
                    # Simple threshold check (would need configured limits)
                    if balance.balance < Decimal('1000'):  # Simplified threshold
                        alerts.append({
                            'branch': {
                                'id': str(branch.id),
                                'code': branch.code,
                                'name': branch.name
                            },
                            'currency': {
                                'code': balance.currency.code if balance.currency else 'UNK',
                                'name': balance.currency.name if balance.currency else 'Unknown'
                            },
                            'current_balance': float(balance.balance),
                            'severity': 'high' if balance.balance < Decimal('500') else 'medium'
                        })
            
            return {
                'generated_at': datetime.now().isoformat(),
                'alert_count': len(alerts),
                'alerts': alerts
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate low balance alerts: {str(e)}")
    
    def balance_movement_report(
        self,
        branch_id: Optional[str],
        currency_code: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        تقرير حركة الرصيد
        Balance movement tracking for a specific currency
        """
        try:
            filters = [
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.status == TransactionStatus.COMPLETED,
                Currency.code == currency_code,
            ]

            if branch_id:
                filters.append(Transaction.branch_id == branch_id)

            transactions = (
                self.db.query(Transaction)
                .join(Currency, Transaction.currency_id == Currency.id)
                .filter(*filters)
                .order_by(Transaction.transaction_date)
                .all()
            )

            events: List[Dict[str, Any]] = []

            for txn in transactions:
                amount = txn.source_amount or txn.amount or Decimal('0')
                change = -amount if txn.transaction_type in [TransactionType.EXPENSE, TransactionType.EXCHANGE] else amount

                events.append({
                    'raw_date': txn.transaction_date,
                    'transaction_number': txn.transaction_number,
                    'type': txn.transaction_type.value,
                    'description': txn.notes or '',
                    'amount': amount,
                    'debit': amount if change < 0 else Decimal('0'),
                    'credit': amount if change > 0 else Decimal('0'),
                    'change': change,
                })

            if branch_id is None:
                main_vault = self.db.query(Vault).filter(
                    Vault.vault_type == 'main',
                    Vault.is_active == True
                ).first()

                if main_vault:
                    vault_filters = [
                        VaultTransfer.status == VaultTransferStatus.COMPLETED,
                        VaultTransfer.initiated_at >= datetime.combine(start_date, datetime.min.time()),
                        VaultTransfer.initiated_at <= datetime.combine(end_date, datetime.max.time()),
                        Currency.code == currency_code,
                    ]

                    vault_transfers = (
                        self.db.query(VaultTransfer)
                        .join(Currency, VaultTransfer.currency_id == Currency.id)
                        .filter(*vault_filters)
                        .order_by(VaultTransfer.initiated_at)
                        .all()
                    )

                    for transfer in vault_transfers:
                        effective_date = transfer.completed_at or transfer.initiated_at
                        amount = transfer.amount or Decimal('0')

                        if transfer.from_vault_id == main_vault.id:
                            change = -amount
                            movement_type = 'vault_outflow'
                        elif transfer.to_vault_id == main_vault.id:
                            change = amount
                            movement_type = 'vault_inflow'
                        else:
                            continue

                        events.append({
                            'raw_date': effective_date,
                            'transaction_number': transfer.transfer_number,
                            'type': movement_type,
                            'description': transfer.notes or '',
                            'amount': amount,
                            'debit': amount if change < 0 else Decimal('0'),
                            'credit': amount if change > 0 else Decimal('0'),
                            'change': change,
                        })

            events.sort(key=lambda e: e['raw_date'])

            movements = []
            running_balance = Decimal('0')

            for event in events:
                running_balance += event['change']
                movements.append({
                    'date': event['raw_date'].isoformat(),
                    'transaction_number': event['transaction_number'],
                    'type': event['type'],
                    'amount': float(abs(event['change'])),
                    'description': event['description'],
                    'debit': float(event['debit']),
                    'credit': float(event['credit']),
                    'balance': float(running_balance),
                })

            return {
                'branch_id': branch_id or 'all',
                'currency': currency_code,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'movement_count': len(movements),
                'movements': movements
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate balance movement: {str(e)}")
    
    # ==================== USER ACTIVITY REPORTS ====================
    
    def user_activity_log(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        سجل نشاط المستخدم
        User activity log from audit trail
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ReportGenerationError("User not found")
            
            # Get audit logs
            activities = self.db.query(AuditLog).filter(
                AuditLog.user_id == user_id,
                func.date(AuditLog.timestamp) >= start_date,
                func.date(AuditLog.timestamp) <= end_date
            ).order_by(AuditLog.timestamp.desc()).all()
            
            activity_summary = {
                'login': 0,
                'transaction': 0,
                'update': 0,
                'delete': 0,
                'other': 0
            }
            
            activity_details = []
            
            for activity in activities:
                action_type = 'other'
                if 'login' in activity.action.lower():
                    action_type = 'login'
                elif 'transaction' in activity.entity_type.lower():
                    action_type = 'transaction'
                elif 'update' in activity.action.lower():
                    action_type = 'update'
                elif 'delete' in activity.action.lower():
                    action_type = 'delete'
                
                activity_summary[action_type] += 1
                
                activity_details.append({
                    'timestamp': activity.timestamp.isoformat(),
                    'action': activity.action,
                    'entity_type': activity.entity_type,
                    'entity_id': str(activity.entity_id) if activity.entity_id else None,
                    'ip_address': activity.ip_address
                })
            
            return {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'full_name': user.full_name
                },
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': activity_summary,
                'total_activities': len(activities),
                'activities': activity_details[:100]  # Limit to recent 100
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate user activity log: {str(e)}")
    
    def transaction_by_user(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        معاملات المستخدم
        Transactions performed by a specific user
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ReportGenerationError("User not found")
            
            transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            ).all()
            
            summary = {
                'total_count': len(transactions),
                'by_type': {},
                'by_status': {},
                'total_volume': Decimal('0')
            }
            
            for txn in transactions:
                # By type
                txn_type = txn.transaction_type.value
                summary['by_type'][txn_type] = summary['by_type'].get(txn_type, 0) + 1
                
                # By status
                status = txn.status.value
                summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
                
                # Volume
                if txn.status == TransactionStatus.COMPLETED:
                    summary['total_volume'] += txn.source_amount or Decimal('0')
            
            return {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'full_name': user.full_name
                },
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    **summary,
                    'total_volume': float(summary['total_volume'])
                }
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate user transactions: {str(e)}")
    
    def audit_trail_report(
        self,
        entity_type: str,
        entity_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        تقرير مسار التدقيق
        Complete audit trail for an entity
        """
        try:
            query = self.db.query(AuditLog).filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
            
            if start_date:
                query = query.filter(func.date(AuditLog.timestamp) >= start_date)
            if end_date:
                query = query.filter(func.date(AuditLog.timestamp) <= end_date)
            
            audit_logs = query.order_by(AuditLog.timestamp.desc()).all()
            
            trail = []
            for log in audit_logs:
                trail.append({
                    'timestamp': log.timestamp.isoformat(),
                    'action': log.action,
                    'user': {
                        'id': str(log.user_id),
                        'username': log.user.username if log.user else 'Unknown'
                    },
                    'changes': log.changes,
                    'ip_address': log.ip_address
                })
            
            return {
                'entity': {
                    'type': entity_type,
                    'id': entity_id
                },
                'date_range': {
                    'start': start_date.isoformat() if start_date else 'All time',
                    'end': end_date.isoformat() if end_date else 'Present'
                },
                'total_events': len(trail),
                'audit_trail': trail
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate audit trail: {str(e)}")
    
    # ==================== ANALYTICS ====================
    
    def calculate_commission_earned(
        self,
        branch_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        حساب العمولات المكتسبة
        Calculate total commission earned
        """
        try:
            if start_date is None:
                start_date = date.today() - timedelta(days=30)
            if end_date is None:
                end_date = date.today()
            
            query = self.db.query(Transaction).filter(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.status == TransactionStatus.COMPLETED,
                Transaction.commission_amount.isnot(None)
            )

            if branch_id:
                query = query.filter(Transaction.branch_id == branch_id)

            transactions = query.all()

            total_commission = sum(txn.commission_amount for txn in transactions)

            # By transaction type
            by_type = {}
            for txn in transactions:
                txn_type = txn.transaction_type.value
                if txn_type not in by_type:
                    by_type[txn_type] = Decimal('0')
                by_type[txn_type] += txn.commission_amount
            
            return {
                'branch_id': branch_id,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_commission': float(total_commission),
                'transaction_count': len(transactions),
                'average_commission': float(total_commission / len(transactions)) if transactions else 0,
                'by_transaction_type': {k: float(v) for k, v in by_type.items()}
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to calculate commission: {str(e)}")
    
    def identify_high_value_customers(
        self,
        branch_id: Optional[str] = None,
        min_transaction_value: Decimal = Decimal('10000'),
        period_days: int = 90
    ) -> Dict[str, Any]:
        """
        تحديد العملاء ذوي القيمة العالية
        Identify high-value customers based on transaction volume
        """
        try:
            cutoff_date = date.today() - timedelta(days=period_days)
            
            query = self.db.query(
                Customer.id,
                Customer.customer_code,
                Customer.full_name,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.source_amount).label('total_volume')
            ).join(
                Transaction, Transaction.customer_id == Customer.id
            ).filter(
                Transaction.transaction_date >= cutoff_date,
                Transaction.status == TransactionStatus.COMPLETED
            )
            
            if branch_id:
                query = query.filter(Transaction.branch_id == branch_id)
            
            query = query.group_by(Customer.id, Customer.customer_code, Customer.full_name)
            query = query.having(func.sum(Transaction.source_amount) >= min_transaction_value)
            query = query.order_by(func.sum(Transaction.source_amount).desc())
            
            results = query.all()
            
            high_value_customers = []
            for customer_id, code, name, txn_count, volume in results:
                high_value_customers.append({
                    'customer_id': str(customer_id),
                    'customer_code': code,
                    'full_name': name,
                    'transaction_count': txn_count,
                    'total_volume': float(volume or Decimal('0')),
                    'average_transaction': float((volume or Decimal('0')) / txn_count) if txn_count > 0 else 0
                })
            
            return {
                'branch_id': branch_id,
                'period_days': period_days,
                'minimum_value': float(min_transaction_value),
                'customer_count': len(high_value_customers),
                'customers': high_value_customers
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to identify high-value customers: {str(e)}")
    
    def transaction_volume_trends(
        self,
        branch_id: Optional[str] = None,
        period: str = 'daily'  # daily, weekly, monthly
    ) -> Dict[str, Any]:
        """
        اتجاهات حجم المعاملات
        Transaction volume trends over time
        """
        try:
            # Last 30 days for daily, 12 weeks for weekly, 12 months for monthly
            if period == 'daily':
                days = 30
                date_trunc = func.date(Transaction.transaction_date)
            elif period == 'weekly':
                days = 90
                date_trunc = func.date_trunc('week', Transaction.transaction_date)
            else:  # monthly
                days = 365
                date_trunc = func.date_trunc('month', Transaction.transaction_date)
            
            cutoff_date = date.today() - timedelta(days=days)
            
            query = self.db.query(
                date_trunc.label('period'),
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.source_amount).label('volume')
            ).filter(
                Transaction.transaction_date >= cutoff_date,
                Transaction.status == TransactionStatus.COMPLETED
            )
            
            if branch_id:
                query = query.filter(Transaction.branch_id == branch_id)
            
            query = query.group_by('period').order_by('period')
            
            results = query.all()
            
            trends = []
            for period_date, count, volume in results:
                trends.append({
                    'period': period_date.isoformat() if isinstance(period_date, date) else str(period_date),
                    'transaction_count': count,
                    'total_volume': float(volume or Decimal('0'))
                })
            
            return {
                'branch_id': branch_id,
                'period_type': period,
                'data_points': len(trends),
                'trends': trends
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate volume trends: {str(e)}")
    
    def exchange_rate_volatility_analysis(
        self,
        currency_pair: Tuple[str, str],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        تحليل تقلبات سعر الصرف
        Analyze exchange rate volatility for a currency pair
        """
        try:
            from_currency, to_currency = currency_pair
            cutoff_date = date.today() - timedelta(days=period_days)
            
            # Get exchange rates history
            from app.db.models.currency import ExchangeRate as ER
            rates = self.db.query(ER).join(
                Currency, ER.from_currency_id == Currency.id
            ).filter(
                ER.effective_from >= cutoff_date,
                Currency.code == from_currency
            ).order_by(ER.effective_from).all()
            
            # Filter for target currency
            relevant_rates = [
                rate for rate in rates
                if rate.to_currency and rate.to_currency.code == to_currency
            ]
            
            if not relevant_rates:
                return {
                    'currency_pair': f"{from_currency}/{to_currency}",
                    'message': 'No rate data available'
                }
            
            # Calculate volatility metrics
            rate_values = [rate.rate for rate in relevant_rates]
            
            avg_rate = sum(rate_values) / len(rate_values)
            max_rate = max(rate_values)
            min_rate = min(rate_values)
            
            # Standard deviation (simplified)
            variance = sum((r - avg_rate) ** 2 for r in rate_values) / len(rate_values)
            std_dev = variance ** Decimal('0.5')
            
            # Daily changes
            daily_changes = []
            for i in range(1, len(relevant_rates)):
                prev_rate = relevant_rates[i-1].rate
                curr_rate = relevant_rates[i].rate
                change = ((curr_rate - prev_rate) / prev_rate) * 100
                daily_changes.append({
                    'date': relevant_rates[i].effective_from.isoformat(),
                    'rate': float(curr_rate),
                    'change_percent': float(change)
                })
            
            return {
                'currency_pair': f"{from_currency}/{to_currency}",
                'period_days': period_days,
                'statistics': {
                    'average_rate': float(avg_rate),
                    'max_rate': float(max_rate),
                    'min_rate': float(min_rate),
                    'standard_deviation': float(std_dev),
                    'volatility_percent': float((std_dev / avg_rate) * 100) if avg_rate else 0
                },
                'daily_changes': daily_changes
            }
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to analyze rate volatility: {str(e)}")


# ==================== HELPER FUNCTIONS ====================

def format_currency(amount: Decimal, currency_code: str = 'USD') -> str:
    """Format currency for display"""
    return f"{currency_code} {amount:,.2f}"


def calculate_percentage_change(old_value: Decimal, new_value: Decimal) -> Decimal:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return Decimal('0')
    return ((new_value - old_value) / old_value) * 100
