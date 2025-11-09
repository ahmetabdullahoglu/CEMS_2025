"""
Vault Service
Handles all vault operations including transfers, approvals, and reconciliation
"""
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.db.models.vault import (
    Vault, VaultBalance, VaultTransfer,
    VaultType, VaultTransferType, VaultTransferStatus,
    VaultTransferNumberGenerator
)
from app.db.models.branch import Branch, BranchBalance
from app.db.models.currency import Currency
from app.db.models.user import User
from app.schemas.vault import (
    VaultCreate, VaultUpdate,
    VaultToVaultTransferCreate, VaultToBranchTransferCreate,
    BranchToVaultTransferCreate, TransferApproval,
    VaultReconciliationRequest
)
from app.core.constants import (
    TRANSFER_APPROVAL_THRESHOLD,
    MAX_TRANSFER_AMOUNT,
    MIN_VAULT_BALANCE
)


class VaultService:
    """Service for vault operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== VAULT MANAGEMENT ====================
    
    def get_main_vault(self) -> Vault:
        """Get the main vault (there should be only one)"""
        vault = self.db.query(Vault).filter(
            Vault.vault_type == VaultType.MAIN,
            Vault.is_active == True
        ).first()
        
        if not vault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Main vault not found"
            )
        
        return vault
    
    def get_vault_by_id(self, vault_id: UUID) -> Vault:
        """Get vault by ID"""
        vault = self.db.query(Vault).filter(
            Vault.id == vault_id,
            Vault.is_active == True
        ).first()
        
        if not vault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vault {vault_id} not found"
            )
        
        return vault
    
    def get_branch_vault(self, branch_id: UUID) -> Optional[Vault]:
        """Get vault for a specific branch"""
        return self.db.query(Vault).filter(
            Vault.branch_id == branch_id,
            Vault.vault_type == VaultType.BRANCH,
            Vault.is_active == True
        ).first()
    
    def create_vault(self, vault_data: VaultCreate) -> Vault:
        """Create new vault"""
        # Validate main vault uniqueness
        if vault_data.vault_type == VaultType.MAIN:
            existing_main = self.db.query(Vault).filter(
                Vault.vault_type == VaultType.MAIN
            ).first()
            
            if existing_main:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Main vault already exists"
                )
        
        # Validate branch exists if branch vault
        if vault_data.vault_type == VaultType.BRANCH:
            if not vault_data.branch_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Branch ID required for branch vault"
                )
            
            branch = self.db.query(Branch).filter(
                Branch.id == vault_data.branch_id
            ).first()
            
            if not branch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Branch not found"
                )
        
        vault = Vault(**vault_data.dict())
        self.db.add(vault)
        self.db.commit()
        self.db.refresh(vault)
        
        return vault
    
    def update_vault(self, vault_id: UUID, vault_data: VaultUpdate) -> Vault:
        """Update vault information"""
        vault = self.get_vault_by_id(vault_id)
        
        for field, value in vault_data.dict(exclude_unset=True).items():
            setattr(vault, field, value)
        
        self.db.commit()
        self.db.refresh(vault)
        
        return vault
    
    # ==================== BALANCE MANAGEMENT ====================
    
    def get_vault_balance(
        self,
        vault_id: UUID,
        currency_id: Optional[UUID] = None
    ) -> List[VaultBalance]:
        """Get vault balance(s)"""
        query = self.db.query(VaultBalance).filter(
            VaultBalance.vault_id == vault_id
        )
        
        if currency_id:
            query = query.filter(VaultBalance.currency_id == currency_id)
        
        balances = query.all()
        
        if not balances and currency_id:
            # Create zero balance if doesn't exist
            currency = self.db.query(Currency).filter(
                Currency.id == currency_id
            ).first()
            
            if not currency:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Currency not found"
                )
            
            balance = VaultBalance(
                vault_id=vault_id,
                currency_id=currency_id,
                balance=Decimal('0.00')
            )
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)
            balances = [balance]
        
        return balances
    
    def update_vault_balance(
        self,
        vault_id: UUID,
        currency_id: UUID,
        amount: Decimal,
        operation: str = 'add'  # 'add' or 'subtract'
    ) -> VaultBalance:
        """
        Update vault balance
        operation: 'add' to increase, 'subtract' to decrease
        """
        balance = self.db.query(VaultBalance).filter(
            VaultBalance.vault_id == vault_id,
            VaultBalance.currency_id == currency_id
        ).first()
        
        if not balance:
            # Create new balance
            balance = VaultBalance(
                vault_id=vault_id,
                currency_id=currency_id,
                balance=Decimal('0.00')
            )
            self.db.add(balance)
        
        if operation == 'add':
            balance.balance += amount
        elif operation == 'subtract':
            if balance.balance < amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance in vault"
                )
            balance.balance -= amount
        else:
            raise ValueError(f"Invalid operation: {operation}")
        
        balance.last_updated = datetime.utcnow()
        self.db.commit()
        self.db.refresh(balance)
        
        return balance
    
    def get_vault_total_value_usd(self, vault_id: UUID) -> Decimal:
        """Calculate total vault value in USD equivalent"""
        balances = self.get_vault_balance(vault_id)
        total_usd = Decimal('0.00')
        
        for balance in balances:
            currency = balance.currency
            if currency.code == 'USD':
                total_usd += balance.balance
            else:
                # Get exchange rate to USD
                from app.services.currency_service import CurrencyService
                currency_service = CurrencyService(self.db)
                rate = currency_service.get_exchange_rate(
                    currency.id,
                    self._get_usd_currency_id()
                )
                total_usd += balance.balance * rate
        
        return total_usd
    
    def _get_usd_currency_id(self) -> UUID:
        """Helper to get USD currency ID"""
        usd = self.db.query(Currency).filter(
            Currency.code == 'USD'
        ).first()
        if not usd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="USD currency not found"
            )
        return usd.id
    
    # ==================== TRANSFER OPERATIONS ====================
    
    def transfer_vault_to_vault(
        self,
        transfer_data: VaultToVaultTransferCreate,
        user: User
    ) -> VaultTransfer:
        """Transfer between two vaults"""
        # Validate vaults
        from_vault = self.get_vault_by_id(transfer_data.from_vault_id)
        to_vault = self.get_vault_by_id(transfer_data.to_vault_id)
        
        # Validate currency
        currency = self.db.query(Currency).filter(
            Currency.id == transfer_data.currency_id
        ).first()
        if not currency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currency not found"
            )
        
        # Check source vault balance
        from_balance = self.db.query(VaultBalance).filter(
            VaultBalance.vault_id == from_vault.id,
            VaultBalance.currency_id == currency.id
        ).first()
        
        if not from_balance or from_balance.balance < transfer_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance in source vault"
            )
        
        # Create transfer
        transfer_number = VaultTransferNumberGenerator.generate(self.db)
        
        transfer = VaultTransfer(
            transfer_number=transfer_number,
            from_vault_id=from_vault.id,
            to_vault_id=to_vault.id,
            currency_id=currency.id,
            amount=transfer_data.amount,
            transfer_type=VaultTransferType.VAULT_TO_VAULT,
            status=VaultTransferStatus.PENDING,
            initiated_by=user.id,
            notes=transfer_data.notes
        )
        
        # Check if approval needed
        if transfer_data.amount >= TRANSFER_APPROVAL_THRESHOLD:
            transfer.status = VaultTransferStatus.PENDING
        else:
            # Auto-approve small transfers
            transfer.status = VaultTransferStatus.IN_TRANSIT
            transfer.approved_by = user.id
            transfer.approved_at = datetime.utcnow()
        
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        
        # Execute transfer if approved
        if transfer.status == VaultTransferStatus.IN_TRANSIT:
            self._execute_vault_transfer(transfer)
        
        return transfer
    
    def transfer_to_branch(
        self,
        transfer_data: VaultToBranchTransferCreate,
        user: User
    ) -> VaultTransfer:
        """Transfer from vault to branch"""
        vault = self.get_vault_by_id(transfer_data.vault_id)
        
        # Validate branch
        branch = self.db.query(Branch).filter(
            Branch.id == transfer_data.branch_id,
            Branch.is_active == True
        ).first()
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
        
        # Validate currency
        currency = self.db.query(Currency).filter(
            Currency.id == transfer_data.currency_id
        ).first()
        if not currency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currency not found"
            )
        
        # Check vault balance
        vault_balance = self.db.query(VaultBalance).filter(
            VaultBalance.vault_id == vault.id,
            VaultBalance.currency_id == currency.id
        ).first()
        
        if not vault_balance or vault_balance.balance < transfer_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance in vault"
            )
        
        # Create transfer
        transfer_number = VaultTransferNumberGenerator.generate(self.db)
        
        transfer = VaultTransfer(
            transfer_number=transfer_number,
            from_vault_id=vault.id,
            to_branch_id=branch.id,
            currency_id=currency.id,
            amount=transfer_data.amount,
            transfer_type=VaultTransferType.VAULT_TO_BRANCH,
            status=VaultTransferStatus.PENDING,
            initiated_by=user.id,
            notes=transfer_data.notes
        )
        
        # Check approval requirement
        if transfer_data.amount >= TRANSFER_APPROVAL_THRESHOLD:
            transfer.status = VaultTransferStatus.PENDING
        else:
            transfer.status = VaultTransferStatus.IN_TRANSIT
            transfer.approved_by = user.id
            transfer.approved_at = datetime.utcnow()
        
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    def transfer_from_branch(
        self,
        transfer_data: BranchToVaultTransferCreate,
        user: User
    ) -> VaultTransfer:
        """Transfer from branch to vault"""
        vault = self.get_vault_by_id(transfer_data.vault_id)
        
        # Validate branch
        branch = self.db.query(Branch).filter(
            Branch.id == transfer_data.branch_id,
            Branch.is_active == True
        ).first()
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
        
        # Validate currency
        currency = self.db.query(Currency).filter(
            Currency.id == transfer_data.currency_id
        ).first()
        if not currency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currency not found"
            )
        
        # Check branch balance
        branch_balance = self.db.query(BranchBalance).filter(
            BranchBalance.branch_id == branch.id,
            BranchBalance.currency_id == currency.id
        ).first()
        
        if not branch_balance or branch_balance.balance < transfer_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance in branch"
            )
        
        # Get or create branch vault
        branch_vault = self.get_branch_vault(branch.id)
        if not branch_vault:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch vault not found"
            )
        
        # Create transfer
        transfer_number = VaultTransferNumberGenerator.generate(self.db)
        
        transfer = VaultTransfer(
            transfer_number=transfer_number,
            from_vault_id=branch_vault.id,
            to_vault_id=vault.id,
            currency_id=currency.id,
            amount=transfer_data.amount,
            transfer_type=VaultTransferType.BRANCH_TO_VAULT,
            status=VaultTransferStatus.PENDING,
            initiated_by=user.id,
            notes=transfer_data.notes
        )
        
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    # ==================== TRANSFER WORKFLOW ====================
    
    def approve_transfer(
        self,
        transfer_id: UUID,
        approval_data: TransferApproval,
        user: User
    ) -> VaultTransfer:
        """Approve a pending transfer"""
        transfer = self.db.query(VaultTransfer).filter(
            VaultTransfer.id == transfer_id
        ).first()
        
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status != VaultTransferStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transfer is not pending (current status: {transfer.status})"
            )
        
        # Check user has approval permission (should be manager+)
        if not self._can_approve_transfer(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to approve transfer"
            )
        
        if approval_data.approved:
            transfer.status = VaultTransferStatus.IN_TRANSIT
            transfer.approved_by = user.id
            transfer.approved_at = datetime.utcnow()
            
            # Execute the transfer
            self._execute_vault_transfer(transfer)
        else:
            transfer.status = VaultTransferStatus.CANCELLED
            transfer.rejection_reason = approval_data.notes
            transfer.cancelled_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    def complete_transfer(
        self,
        transfer_id: UUID,
        user: User
    ) -> VaultTransfer:
        """Complete a transfer (mark as received)"""
        transfer = self.db.query(VaultTransfer).filter(
            VaultTransfer.id == transfer_id
        ).first()
        
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status != VaultTransferStatus.IN_TRANSIT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer is not in transit"
            )
        
        transfer.status = VaultTransferStatus.COMPLETED
        transfer.received_by = user.id
        transfer.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    def cancel_transfer(
        self,
        transfer_id: UUID,
        reason: str,
        user: User
    ) -> VaultTransfer:
        """Cancel a pending transfer"""
        transfer = self.db.query(VaultTransfer).filter(
            VaultTransfer.id == transfer_id
        ).first()
        
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status not in [VaultTransferStatus.PENDING, VaultTransferStatus.IN_TRANSIT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel pending or in-transit transfers"
            )
        
        # Reverse balance changes if already executed
        if transfer.status == VaultTransferStatus.IN_TRANSIT:
            self._reverse_vault_transfer(transfer)
        
        transfer.status = VaultTransferStatus.CANCELLED
        transfer.rejection_reason = reason
        transfer.cancelled_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    def _execute_vault_transfer(self, transfer: VaultTransfer):
        """Execute the actual balance changes for a transfer"""
        # Deduct from source vault
        self.update_vault_balance(
            transfer.from_vault_id,
            transfer.currency_id,
            transfer.amount,
            operation='subtract'
        )
        
        # Add to destination (vault or branch)
        if transfer.to_vault_id:
            self.update_vault_balance(
                transfer.to_vault_id,
                transfer.currency_id,
                transfer.amount,
                operation='add'
            )
        elif transfer.to_branch_id:
            # Update branch balance
            from app.services.branch_service import BranchService
            branch_service = BranchService(self.db)
            branch_service.update_branch_balance(
                transfer.to_branch_id,
                transfer.currency_id,
                transfer.amount,
                operation='add'
            )
    
    def _reverse_vault_transfer(self, transfer: VaultTransfer):
        """Reverse a transfer (for cancellations)"""
        # Add back to source vault
        self.update_vault_balance(
            transfer.from_vault_id,
            transfer.currency_id,
            transfer.amount,
            operation='add'
        )
        
        # Deduct from destination
        if transfer.to_vault_id:
            self.update_vault_balance(
                transfer.to_vault_id,
                transfer.currency_id,
                transfer.amount,
                operation='subtract'
            )
        elif transfer.to_branch_id:
            from app.services.branch_service import BranchService
            branch_service = BranchService(self.db)
            branch_service.update_branch_balance(
                transfer.to_branch_id,
                transfer.currency_id,
                transfer.amount,
                operation='subtract'
            )
    
    def _can_approve_transfer(self, user: User) -> bool:
        """Check if user can approve transfers"""
        # Should check for manager or admin role
        return any(
            role.name in ['MANAGER', 'ADMIN', 'SUPER_ADMIN']
            for role in user.roles
        )
    
    # ==================== TRANSFER HISTORY ====================
    
    def get_transfer_history(
        self,
        vault_id: Optional[UUID] = None,
        branch_id: Optional[UUID] = None,
        status: Optional[VaultTransferStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[VaultTransfer], int]:
        """Get transfer history with filters"""
        query = self.db.query(VaultTransfer)
        
        # Apply filters
        if vault_id:
            query = query.filter(
                or_(
                    VaultTransfer.from_vault_id == vault_id,
                    VaultTransfer.to_vault_id == vault_id
                )
            )
        
        if branch_id:
            query = query.filter(VaultTransfer.to_branch_id == branch_id)
        
        if status:
            query = query.filter(VaultTransfer.status == status)
        
        if date_from:
            query = query.filter(VaultTransfer.initiated_at >= date_from)
        
        if date_to:
            query = query.filter(VaultTransfer.initiated_at <= date_to)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        transfers = query.order_by(
            VaultTransfer.initiated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return transfers, total
    
    # ==================== RECONCILIATION ====================
    
    def reconcile_vault_balance(
        self,
        reconciliation_data: VaultReconciliationRequest,
        user: User
    ) -> Dict:
        """
        Perform vault balance reconciliation
        Compare system balance with physical count
        """
        vault = self.get_vault_by_id(reconciliation_data.vault_id)
        
        if reconciliation_data.currency_id:
            # Reconcile specific currency
            balances = [self.get_vault_balance(
                vault.id,
                reconciliation_data.currency_id
            )[0]]
        else:
            # Reconcile all currencies
            balances = self.get_vault_balance(vault.id)
        
        results = []
        total_discrepancies = 0
        
        for balance in balances:
            result = {
                'vault_id': vault.id,
                'vault_code': vault.vault_code,
                'currency_id': balance.currency_id,
                'currency_code': balance.currency.code,
                'system_balance': balance.balance,
                'physical_count': None,  # Would be input from physical count
                'discrepancy': None,
                'last_reconciled_at': datetime.utcnow(),
                'reconciled_by': user.username
            }
            
            # In real implementation, physical count would be provided
            # For now, we assume system balance is correct
            result['physical_count'] = balance.balance
            result['discrepancy'] = Decimal('0.00')
            
            results.append(result)
        
        return {
            'vault_id': vault.id,
            'vault_code': vault.vault_code,
            'vault_name': vault.name,
            'reconciliation_date': datetime.utcnow(),
            'results': results,
            'total_discrepancies': total_discrepancies,
            'notes': reconciliation_data.notes
        }
    
    # ==================== STATISTICS & REPORTING ====================
    
    def get_vault_statistics(self, vault_id: UUID) -> Dict:
        """Get comprehensive vault statistics"""
        vault = self.get_vault_by_id(vault_id)
        balances = self.get_vault_balance(vault_id)
        
        # Count pending transfers
        pending_in = self.db.query(VaultTransfer).filter(
            VaultTransfer.to_vault_id == vault_id,
            VaultTransfer.status.in_([
                VaultTransferStatus.PENDING,
                VaultTransferStatus.IN_TRANSIT
            ])
        ).count()
        
        pending_out = self.db.query(VaultTransfer).filter(
            VaultTransfer.from_vault_id == vault_id,
            VaultTransfer.status.in_([
                VaultTransferStatus.PENDING,
                VaultTransferStatus.IN_TRANSIT
            ])
        ).count()
        
        # Get last transfer date
        last_transfer = self.db.query(VaultTransfer).filter(
            or_(
                VaultTransfer.from_vault_id == vault_id,
                VaultTransfer.to_vault_id == vault_id
            )
        ).order_by(VaultTransfer.initiated_at.desc()).first()
        
        return {
            'vault_id': vault.id,
            'vault_code': vault.vault_code,
            'vault_name': vault.name,
            'total_balance_usd_equivalent': self.get_vault_total_value_usd(vault_id),
            'currency_count': len(balances),
            'pending_transfers_in': pending_in,
            'pending_transfers_out': pending_out,
            'last_transfer_date': last_transfer.initiated_at if last_transfer else None,
            'last_reconciliation_date': None  # Would track this separately
        }
    
    def get_transfer_summary(
        self,
        vault_id: Optional[UUID] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict:
        """Get transfer summary statistics"""
        if not period_start:
            period_start = datetime.utcnow() - timedelta(days=30)
        if not period_end:
            period_end = datetime.utcnow()
        
        query = self.db.query(VaultTransfer).filter(
            VaultTransfer.initiated_at.between(period_start, period_end)
        )
        
        if vault_id:
            query = query.filter(
                or_(
                    VaultTransfer.from_vault_id == vault_id,
                    VaultTransfer.to_vault_id == vault_id
                )
            )
        
        transfers = query.all()
        
        total_count = len(transfers)
        completed = sum(1 for t in transfers if t.status == VaultTransferStatus.COMPLETED)
        pending = sum(1 for t in transfers if t.status == VaultTransferStatus.PENDING)
        cancelled = sum(1 for t in transfers if t.status == VaultTransferStatus.CANCELLED)
        
        total_amount = sum(t.amount for t in transfers if t.status == VaultTransferStatus.COMPLETED)
        avg_amount = total_amount / completed if completed > 0 else Decimal('0.00')
        
        return {
            'period_start': period_start,
            'period_end': period_end,
            'total_transfers': total_count,
            'completed_transfers': completed,
            'pending_transfers': pending,
            'cancelled_transfers': cancelled,
            'total_amount_transferred': total_amount,
            'average_transfer_amount': avg_amount
        }
