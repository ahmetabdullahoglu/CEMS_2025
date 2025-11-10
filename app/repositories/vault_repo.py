# app/repositories/vault_repo.py
"""
Vault Repository
================
Data access layer for vault operations
Phase 7: Vault Management
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.vault import Vault, VaultBalance, VaultTransfer, VaultTransferStatus
from app.db.models.branch import Branch
from app.db.models.currency import Currency
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VaultRepository:
    """Repository for vault data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== VAULT CRUD ====================

    async def get_by_id(
        self, vault_id: UUID, load_relations: bool = True
    ) -> Optional[Vault]:
        """Get vault by ID"""
        query = select(Vault).where(Vault.id == vault_id)

        if load_relations:
            query = query.options(
                selectinload(Vault.branch),
                selectinload(Vault.balances)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Vault]:
        """Get vault by code"""
        query = select(Vault).where(Vault.code == code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        branch_id: Optional[UUID] = None,
        is_active: Optional[bool] = True
    ) -> List[Vault]:
        """List all vaults with optional filters"""
        query = select(Vault)

        if branch_id:
            query = query.where(Vault.branch_id == branch_id)
        if is_active is not None:
            query = query.where(Vault.is_active == is_active)

        query = query.options(
            selectinload(Vault.branch),
            selectinload(Vault.balances)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==================== VAULT BALANCE OPERATIONS ====================

    async def get_balance(
        self, vault_id: UUID, currency_id: UUID
    ) -> Optional[VaultBalance]:
        """Get vault balance for specific currency"""
        query = select(VaultBalance).where(
            and_(
                VaultBalance.vault_id == vault_id,
                VaultBalance.currency_id == currency_id
            )
        ).options(
            selectinload(VaultBalance.currency)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_balances(self, vault_id: UUID) -> List[VaultBalance]:
        """Get all balances for a vault"""
        query = select(VaultBalance).where(
            VaultBalance.vault_id == vault_id
        ).options(
            selectinload(VaultBalance.currency)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==================== VAULT TRANSFER OPERATIONS ====================

    async def get_transfer(self, transfer_id: UUID) -> Optional[VaultTransfer]:
        """Get vault transfer by ID"""
        query = select(VaultTransfer).where(
            VaultTransfer.id == transfer_id
        ).options(
            selectinload(VaultTransfer.from_vault),
            selectinload(VaultTransfer.to_vault),
            selectinload(VaultTransfer.currency),
            selectinload(VaultTransfer.initiated_by),
            selectinload(VaultTransfer.approved_by)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_transfers(
        self,
        vault_id: Optional[UUID] = None,
        status: Optional[VaultTransferStatus] = None,
        limit: int = 100
    ) -> List[VaultTransfer]:
        """List vault transfers"""
        query = select(VaultTransfer)

        filters = []
        if vault_id:
            filters.append(
                or_(
                    VaultTransfer.from_vault_id == vault_id,
                    VaultTransfer.to_vault_id == vault_id
                )
            )
        if status:
            filters.append(VaultTransfer.status == status)

        if filters:
            query = query.where(and_(*filters))

        query = query.options(
            selectinload(VaultTransfer.from_vault),
            selectinload(VaultTransfer.to_vault),
            selectinload(VaultTransfer.currency)
        ).order_by(VaultTransfer.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_pending_transfers(self, vault_id: UUID) -> List[VaultTransfer]:
        """Get pending transfers for approval"""
        query = select(VaultTransfer).where(
            and_(
                or_(
                    VaultTransfer.from_vault_id == vault_id,
                    VaultTransfer.to_vault_id == vault_id
                ),
                VaultTransfer.status == VaultTransferStatus.PENDING
            )
        ).options(
            selectinload(VaultTransfer.from_vault),
            selectinload(VaultTransfer.to_vault),
            selectinload(VaultTransfer.currency),
            selectinload(VaultTransfer.initiated_by)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==================== STATISTICS ====================

    async def get_total_value_by_vault(
        self, vault_id: UUID
    ) -> Decimal:
        """Get total value across all currencies in vault"""
        query = select(
            func.sum(VaultBalance.balance)
        ).where(
            VaultBalance.vault_id == vault_id
        )

        result = await self.db.execute(query)
        total = result.scalar()
        return total or Decimal("0.00")
