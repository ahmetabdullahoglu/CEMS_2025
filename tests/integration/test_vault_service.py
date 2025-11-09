"""
Vault Service Integration Tests
Tests all vault operations including transfers, approvals, and reconciliation
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.vault_service import VaultService
from app.db.models.vault import (
    Vault, VaultBalance, VaultTransfer,
    VaultType, VaultTransferType, VaultTransferStatus
)
from app.db.models.branch import Branch, BranchBalance
from app.db.models.currency import Currency
from app.db.models.user import User
from app.db.models.role import Role
from app.schemas.vault import (
    VaultCreate, VaultUpdate,
    VaultToVaultTransferCreate, VaultToBranchTransferCreate,
    BranchToVaultTransferCreate, TransferApproval,
    VaultReconciliationRequest
)


@pytest.fixture
async def vault_service(db_session: AsyncSession):
    """Create vault service instance"""
    return VaultService(db_session)


@pytest.fixture
async def test_currency(db_session: AsyncSession):
    """Create test currency"""
    currency = Currency(
        code="USD",
        name_en="US Dollar",
        name_ar="الدولار الأمريكي",
        symbol="$",
        is_base=True,
        is_active=True
    )
    db_session.add(currency)
    await db_session.commit()
    await db_session.refresh(currency)
    return currency


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create test user with manager role"""
    role = Role(
        name="MANAGER",
        description="Manager role",
        permissions=["vault:transfer", "vault:approve"]
    )
    db_session.add(role)
    await db_session.commit()

    user = User(
        username="test_manager",
        email="manager@test.com",
        hashed_password="hashed_password",
        full_name="Test Manager",
        is_active=True
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def main_vault(db_session: AsyncSession):
    """Create main vault"""
    vault = Vault(
        vault_code="V-MAIN",
        name="Main Vault",
        vault_type=VaultType.MAIN,
        is_active=True
    )
    db_session.add(vault)
    await db_session.commit()
    await db_session.refresh(vault)
    return vault


@pytest.fixture
async def test_branch(db_session: AsyncSession):
    """Create test branch"""
    from app.db.models.branch import RegionEnum

    branch = Branch(
        branch_code="BR-001",
        name_en="Test Branch",
        name_ar="فرع تجريبي",
        region=RegionEnum.ISTANBUL_EUROPEAN,
        is_active=True
    )
    db_session.add(branch)
    await db_session.commit()
    await db_session.refresh(branch)
    return branch


@pytest.fixture
async def branch_vault(db_session: AsyncSession, test_branch):
    """Create branch vault"""
    vault = Vault(
        vault_code="V-BR001",
        name="Test Branch Vault",
        vault_type=VaultType.BRANCH,
        branch_id=test_branch.id,
        is_active=True
    )
    db_session.add(vault)
    await db_session.commit()
    await db_session.refresh(vault)
    return vault


class TestVaultManagement:
    """Test vault CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_main_vault(self, vault_service, main_vault):
        """Test getting main vault"""
        vault = await vault_service.get_main_vault()
        assert vault.id == main_vault.id
        assert vault.vault_type == VaultType.MAIN

    @pytest.mark.asyncio
    async def test_get_main_vault_not_found(self, vault_service):
        """Test getting main vault when it doesn't exist"""
        with pytest.raises(HTTPException) as exc_info:
            await vault_service.get_main_vault()
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_main_vault(self, vault_service):
        """Test creating main vault"""
        vault_data = VaultCreate(
            vault_code="V-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            description="Central vault",
            location="Main Office"
        )
        vault = await vault_service.create_vault(vault_data)

        assert vault.vault_code == "V-MAIN"
        assert vault.vault_type == VaultType.MAIN
        assert vault.branch_id is None

    @pytest.mark.asyncio
    async def test_create_duplicate_main_vault(self, vault_service, main_vault):
        """Test creating duplicate main vault should fail"""
        vault_data = VaultCreate(
            vault_code="V-MAIN2",
            name="Another Main Vault",
            vault_type=VaultType.MAIN
        )

        with pytest.raises(HTTPException) as exc_info:
            await vault_service.create_vault(vault_data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_branch_vault(self, vault_service, test_branch):
        """Test creating branch vault"""
        vault_data = VaultCreate(
            vault_code="V-BR001",
            name="Branch Vault",
            vault_type=VaultType.BRANCH,
            branch_id=test_branch.id
        )
        vault = await vault_service.create_vault(vault_data)

        assert vault.vault_code == "V-BR001"
        assert vault.vault_type == VaultType.BRANCH
        assert vault.branch_id == test_branch.id

    @pytest.mark.asyncio
    async def test_update_vault(self, vault_service, main_vault):
        """Test updating vault"""
        update_data = VaultUpdate(
            name="Updated Main Vault",
            description="Updated description"
        )
        vault = await vault_service.update_vault(main_vault.id, update_data)

        assert vault.name == "Updated Main Vault"
        assert vault.description == "Updated description"


class TestVaultBalance:
    """Test vault balance operations"""

    @pytest.mark.asyncio
    async def test_get_vault_balance_creates_zero_balance(
        self, vault_service, main_vault, test_currency
    ):
        """Test getting balance creates zero balance if not exists"""
        balances = await vault_service.get_vault_balance(
            main_vault.id,
            test_currency.id
        )

        assert len(balances) == 1
        assert balances[0].balance == Decimal('0.00')

    @pytest.mark.asyncio
    async def test_update_vault_balance_add(
        self, vault_service, main_vault, test_currency
    ):
        """Test adding to vault balance"""
        balance = await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('10000.00'),
            operation='add'
        )

        assert balance.balance == Decimal('10000.00')

    @pytest.mark.asyncio
    async def test_update_vault_balance_subtract(
        self, vault_service, main_vault, test_currency
    ):
        """Test subtracting from vault balance"""
        # First add some balance
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('10000.00'),
            operation='add'
        )

        # Then subtract
        balance = await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('3000.00'),
            operation='subtract'
        )

        assert balance.balance == Decimal('7000.00')

    @pytest.mark.asyncio
    async def test_update_vault_balance_insufficient_funds(
        self, vault_service, main_vault, test_currency
    ):
        """Test subtracting more than available should fail"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('1000.00'),
            operation='add'
        )

        with pytest.raises(HTTPException) as exc_info:
            await vault_service.update_vault_balance(
                main_vault.id,
                test_currency.id,
                Decimal('2000.00'),
                operation='subtract'
            )
        assert exc_info.value.status_code == 400


class TestVaultTransfers:
    """Test vault transfer operations"""

    @pytest.mark.asyncio
    async def test_transfer_vault_to_vault_small_amount(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test small transfer (auto-approved)"""
        # Add balance to source vault
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('100000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('5000.00'),
            notes="Test transfer"
        )

        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)

        assert transfer.transfer_type == VaultTransferType.VAULT_TO_VAULT
        assert transfer.status == VaultTransferStatus.IN_TRANSIT  # Auto-approved
        assert transfer.amount == Decimal('5000.00')
        assert transfer.approved_by == test_user.id

        # Check balances updated
        source_balance = (await vault_service.get_vault_balance(
            main_vault.id, test_currency.id
        ))[0]
        dest_balance = (await vault_service.get_vault_balance(
            branch_vault.id, test_currency.id
        ))[0]

        assert source_balance.balance == Decimal('95000.00')
        assert dest_balance.balance == Decimal('5000.00')

    @pytest.mark.asyncio
    async def test_transfer_vault_to_vault_large_amount(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test large transfer (requires approval)"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('200000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('75000.00'),  # Above threshold
            notes="Large transfer"
        )

        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)

        assert transfer.status == VaultTransferStatus.PENDING  # Needs approval
        assert transfer.approved_by is None

        # Balances should not change yet
        source_balance = (await vault_service.get_vault_balance(
            main_vault.id, test_currency.id
        ))[0]
        assert source_balance.balance == Decimal('200000.00')

    @pytest.mark.asyncio
    async def test_transfer_insufficient_balance(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test transfer with insufficient balance"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('1000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('2000.00')
        )

        with pytest.raises(HTTPException) as exc_info:
            await vault_service.transfer_vault_to_vault(transfer_data, test_user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_transfer_to_branch(
        self, vault_service, main_vault, test_branch, test_currency, test_user, db_session
    ):
        """Test transfer from vault to branch"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('50000.00'),
            operation='add'
        )

        transfer_data = VaultToBranchTransferCreate(
            vault_id=main_vault.id,
            branch_id=test_branch.id,
            currency_id=test_currency.id,
            amount=Decimal('10000.00'),
            notes="Branch funding"
        )

        transfer = await vault_service.transfer_to_branch(transfer_data, test_user)

        assert transfer.transfer_type == VaultTransferType.VAULT_TO_BRANCH
        assert transfer.to_branch_id == test_branch.id
        assert transfer.amount == Decimal('10000.00')


class TestTransferWorkflow:
    """Test transfer approval workflow"""

    @pytest.mark.asyncio
    async def test_approve_transfer(
        self, vault_service, main_vault, branch_vault, test_currency, test_user, db_session
    ):
        """Test approving a pending transfer"""
        # Create pending transfer
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('200000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('75000.00')  # Above threshold
        )

        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)
        assert transfer.status == VaultTransferStatus.PENDING

        # Approve it
        approval_data = TransferApproval(
            approved=True,
            notes="Approved for business needs"
        )

        approved_transfer = await vault_service.approve_transfer(
            transfer.id,
            approval_data,
            test_user
        )

        assert approved_transfer.status == VaultTransferStatus.IN_TRANSIT
        assert approved_transfer.approved_by == test_user.id
        assert approved_transfer.approved_at is not None

        # Check balances updated
        source_balance = (await vault_service.get_vault_balance(
            main_vault.id, test_currency.id
        ))[0]
        dest_balance = (await vault_service.get_vault_balance(
            branch_vault.id, test_currency.id
        ))[0]

        assert source_balance.balance == Decimal('125000.00')
        assert dest_balance.balance == Decimal('75000.00')

    @pytest.mark.asyncio
    async def test_reject_transfer(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test rejecting a pending transfer"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('200000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('75000.00')
        )

        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)

        # Reject it
        approval_data = TransferApproval(
            approved=False,
            notes="Insufficient justification"
        )

        rejected_transfer = await vault_service.approve_transfer(
            transfer.id,
            approval_data,
            test_user
        )

        assert rejected_transfer.status == VaultTransferStatus.CANCELLED
        assert rejected_transfer.rejection_reason == "Insufficient justification"

        # Balance should remain unchanged
        source_balance = (await vault_service.get_vault_balance(
            main_vault.id, test_currency.id
        ))[0]
        assert source_balance.balance == Decimal('200000.00')

    @pytest.mark.asyncio
    async def test_complete_transfer(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test completing an in-transit transfer"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('50000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('10000.00')
        )

        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)
        assert transfer.status == VaultTransferStatus.IN_TRANSIT

        # Complete it
        completed_transfer = await vault_service.complete_transfer(transfer.id, test_user)

        assert completed_transfer.status == VaultTransferStatus.COMPLETED
        assert completed_transfer.received_by == test_user.id
        assert completed_transfer.completed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_pending_transfer(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test cancelling a pending transfer"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('200000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('75000.00')
        )

        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)
        assert transfer.status == VaultTransferStatus.PENDING

        # Cancel it
        cancelled_transfer = await vault_service.cancel_transfer(
            transfer.id,
            "No longer needed",
            test_user
        )

        assert cancelled_transfer.status == VaultTransferStatus.CANCELLED
        assert cancelled_transfer.rejection_reason == "No longer needed"

    @pytest.mark.asyncio
    async def test_cancel_in_transit_transfer_reverses_balance(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test cancelling in-transit transfer reverses balance changes"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('50000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('10000.00')
        )

        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)
        assert transfer.status == VaultTransferStatus.IN_TRANSIT

        # Verify balance changed
        source_balance_before = (await vault_service.get_vault_balance(
            main_vault.id, test_currency.id
        ))[0]
        assert source_balance_before.balance == Decimal('40000.00')

        # Cancel it
        await vault_service.cancel_transfer(transfer.id, "Error in amount", test_user)

        # Verify balance reversed
        source_balance_after = (await vault_service.get_vault_balance(
            main_vault.id, test_currency.id
        ))[0]
        assert source_balance_after.balance == Decimal('50000.00')


class TestTransferHistory:
    """Test transfer history and queries"""

    @pytest.mark.asyncio
    async def test_get_transfer_history_all(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test getting all transfer history"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('100000.00'),
            operation='add'
        )

        # Create multiple transfers
        for i in range(3):
            transfer_data = VaultToVaultTransferCreate(
                from_vault_id=main_vault.id,
                to_vault_id=branch_vault.id,
                currency_id=test_currency.id,
                amount=Decimal(f'{1000 * (i + 1)}.00')
            )
            await vault_service.transfer_vault_to_vault(transfer_data, test_user)

        transfers, total = await vault_service.get_transfer_history()

        assert total == 3
        assert len(transfers) == 3

    @pytest.mark.asyncio
    async def test_get_transfer_history_by_vault(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test filtering transfer history by vault"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('100000.00'),
            operation='add'
        )

        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('5000.00')
        )
        await vault_service.transfer_vault_to_vault(transfer_data, test_user)

        transfers, total = await vault_service.get_transfer_history(vault_id=main_vault.id)

        assert total >= 1
        assert all(
            t.from_vault_id == main_vault.id or t.to_vault_id == main_vault.id
            for t in transfers
        )

    @pytest.mark.asyncio
    async def test_get_transfer_history_by_status(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test filtering transfer history by status"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('100000.00'),
            operation='add'
        )

        # Create completed transfer
        transfer_data = VaultToVaultTransferCreate(
            from_vault_id=main_vault.id,
            to_vault_id=branch_vault.id,
            currency_id=test_currency.id,
            amount=Decimal('5000.00')
        )
        transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)
        await vault_service.complete_transfer(transfer.id, test_user)

        transfers, total = await vault_service.get_transfer_history(
            status=VaultTransferStatus.COMPLETED
        )

        assert total >= 1
        assert all(t.status == VaultTransferStatus.COMPLETED for t in transfers)


class TestReconciliation:
    """Test vault reconciliation"""

    @pytest.mark.asyncio
    async def test_reconcile_vault_balance(
        self, vault_service, main_vault, test_currency, test_user
    ):
        """Test vault reconciliation"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('50000.00'),
            operation='add'
        )

        reconciliation_data = VaultReconciliationRequest(
            vault_id=main_vault.id,
            currency_id=test_currency.id,
            notes="Monthly reconciliation"
        )

        result = await vault_service.reconcile_vault_balance(
            reconciliation_data,
            test_user
        )

        assert result['vault_id'] == main_vault.id
        assert len(result['results']) >= 1
        assert result['total_discrepancies'] == 0  # No discrepancies in test

    @pytest.mark.asyncio
    async def test_reconcile_all_currencies(
        self, vault_service, main_vault, test_currency, test_user, db_session
    ):
        """Test reconciling all currencies"""
        # Add another currency
        eur = Currency(
            code="EUR",
            name_en="Euro",
            name_ar="اليورو",
            symbol="€",
            is_active=True
        )
        db_session.add(eur)
        await db_session.commit()

        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('50000.00'),
            operation='add'
        )
        await vault_service.update_vault_balance(
            main_vault.id,
            eur.id,
            Decimal('30000.00'),
            operation='add'
        )

        reconciliation_data = VaultReconciliationRequest(
            vault_id=main_vault.id,
            notes="Full reconciliation"
        )

        result = await vault_service.reconcile_vault_balance(
            reconciliation_data,
            test_user
        )

        assert len(result['results']) == 2  # Both currencies


class TestStatistics:
    """Test vault statistics"""

    @pytest.mark.asyncio
    async def test_get_vault_statistics(
        self, vault_service, main_vault, test_currency, test_user
    ):
        """Test getting vault statistics"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('100000.00'),
            operation='add'
        )

        stats = await vault_service.get_vault_statistics(main_vault.id)

        assert stats['vault_id'] == main_vault.id
        assert stats['currency_count'] >= 1
        assert stats['total_balance_usd_equivalent'] > 0

    @pytest.mark.asyncio
    async def test_get_transfer_summary(
        self, vault_service, main_vault, branch_vault, test_currency, test_user
    ):
        """Test transfer summary statistics"""
        await vault_service.update_vault_balance(
            main_vault.id,
            test_currency.id,
            Decimal('100000.00'),
            operation='add'
        )

        # Create transfers
        for i in range(3):
            transfer_data = VaultToVaultTransferCreate(
                from_vault_id=main_vault.id,
                to_vault_id=branch_vault.id,
                currency_id=test_currency.id,
                amount=Decimal('5000.00')
            )
            transfer = await vault_service.transfer_vault_to_vault(transfer_data, test_user)
            await vault_service.complete_transfer(transfer.id, test_user)

        summary = await vault_service.get_transfer_summary(vault_id=main_vault.id)

        assert summary['total_transfers'] >= 3
        assert summary['completed_transfers'] >= 3
        assert summary['total_amount_transferred'] >= Decimal('15000.00')
