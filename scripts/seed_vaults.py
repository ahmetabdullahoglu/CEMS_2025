#!/usr/bin/env python3
"""
Seed Vaults Script - 10X VERSION
Creates initial vault setup with balances and transfers for testing
Run this after seed_branches.py

ENHANCEMENTS:
- 10x vault transfers (40 instead of 4)
- Dynamic transfer generation
- Varied transfer statuses and types

Creates:
- Main Central Vault
- Branch Vaults (one per branch)
- Initial vault balances for major currencies
- Vault transfers (40 transfers with varied statuses)

Usage:
    python scripts/seed_vaults.py          # Seed vaults
    python scripts/seed_vaults.py --show   # Show vaults summary
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.base import AsyncSessionLocal
from app.db.models.vault import (
    Vault, VaultBalance, VaultTransfer,
    VaultType, VaultTransferType, VaultTransferStatus
)
from app.db.models.branch import Branch
from app.db.models.currency import Currency
from app.db.models.user import User


# Configuration for 10x data
VAULT_TRANSFERS_COUNT = 40  # 10x from 4


async def get_required_data(db: AsyncSession):
    """Get all required data for creating vaults"""

    # Get admin user
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if not admin:
        raise Exception("Admin user not found. Please run seed_data.py first.")

    # Get all active branches
    result = await db.execute(select(Branch).where(Branch.is_active == True))
    branches = {b.code: b for b in result.scalars().all()}
    if not branches:
        raise Exception("No branches found. Please run seed_branches.py first.")

    # Get active currencies
    result = await db.execute(select(Currency).where(Currency.is_active == True))
    currencies = {c.code: c for c in result.scalars().all()}
    if not currencies:
        raise Exception("No currencies found. Please run seed_currencies.py first.")

    # Get manager/admin users for approvals
    result = await db.execute(select(User).where(User.is_active == True))
    users = list(result.scalars().all())

    return {
        "admin": admin,
        "branches": branches,
        "currencies": currencies,
        "users": users
    }


async def create_main_vault(db: AsyncSession) -> Vault:
    """Create the main central vault"""

    print("🏦 Creating Main Central Vault...")

    # Check if main vault already exists
    result = await db.execute(
        select(Vault).where(Vault.vault_type == VaultType.MAIN)
    )
    existing_vault = result.scalar_one_or_none()

    if existing_vault:
        print("  ⚠️  Main vault already exists")
        return existing_vault

    # Create main vault
    main_vault = Vault(
        vault_code="V-MAIN",
        name="Main Central Vault",
        vault_type=VaultType.MAIN,
        branch_id=None,  # Main vault is not tied to a branch
        is_active=True,
        description="Central vault for all currency reserves and main operations",
        location="Main Office - Level B2 - Security Room 1"
    )

    db.add(main_vault)
    await db.flush()

    print(f"  ✅ Created: {main_vault.vault_code} - {main_vault.name}")
    return main_vault


async def create_branch_vaults(db: AsyncSession, branches: dict) -> dict:
    """Create vaults for each branch"""

    print("\n🏢 Creating Branch Vaults...")

    branch_vaults = {}

    for branch_code, branch in branches.items():
        # Check if vault already exists for this branch
        result = await db.execute(
            select(Vault).where(
                Vault.branch_id == branch.id,
                Vault.vault_type == VaultType.BRANCH
            )
        )
        existing_vault = result.scalar_one_or_none()

        if existing_vault:
            print(f"  ⚠️  Vault for {branch_code} already exists")
            branch_vaults[branch_code] = existing_vault
            continue

        # Create branch vault
        vault = Vault(
            vault_code=f"V-{branch_code}",
            name=f"{branch.name_en} Vault",
            vault_type=VaultType.BRANCH,
            branch_id=branch.id,
            is_active=True,
            description=f"Vault for {branch.name_en}",
            location=f"{branch.name_en} - Back Office - Secure Area"
        )

        db.add(vault)
        await db.flush()

        branch_vaults[branch_code] = vault
        print(f"  ✅ Created: {vault.vault_code} - {vault.name}")

    return branch_vaults


async def create_vault_balances(
    db: AsyncSession,
    vault: Vault,
    currencies: dict,
    balance_amounts: dict
):
    """Create initial balances for a vault"""

    print(f"\n💰 Creating balances for {vault.vault_code}...")

    for currency_code, amount in balance_amounts.items():
        currency = currencies.get(currency_code)
        if not currency:
            print(f"  ⚠️  Currency {currency_code} not found")
            continue

        # Check if balance already exists
        result = await db.execute(
            select(VaultBalance).where(
                VaultBalance.vault_id == vault.id,
                VaultBalance.currency_id == currency.id
            )
        )
        existing_balance = result.scalar_one_or_none()

        if existing_balance:
            continue

        # Create balance
        balance = VaultBalance(
            vault_id=vault.id,
            currency_id=currency.id,
            amount=amount,
            reserved_amount=Decimal("0.00")
        )

        db.add(balance)

    await db.flush()
    print(f"  ✅ Created balances for {len(balance_amounts)} currencies")


def generate_vault_transfer(index: int, vaults: list, currencies: dict, users: list) -> dict:
    """Generate vault transfer data dynamically"""
    random.seed(5000 + index)

    # Get two different vaults
    from_vault = random.choice(vaults)
    to_vault = random.choice([v for v in vaults if v.id != from_vault.id])

    currency = random.choice(list(currencies.values()))
    user = random.choice(users)

    # Amount varies
    amount = Decimal(str(random.uniform(1000, 100000)))

    # Transfer type distribution
    transfer_type_choices = [
        (VaultTransferType.REPLENISHMENT, 0.4),
        (VaultTransferType.COLLECTION, 0.3),
        (VaultTransferType.REDISTRIBUTION, 0.2),
        (VaultTransferType.EMERGENCY, 0.1),
    ]
    rand = random.random()
    cumulative = 0
    transfer_type = VaultTransferType.REPLENISHMENT
    for ttype, probability in transfer_type_choices:
        cumulative += probability
        if rand < cumulative:
            transfer_type = ttype
            break

    # Status distribution: 70% completed, 15% in-transit, 10% pending, 5% cancelled
    status_rand = index % 20
    if status_rand < 14:
        status = VaultTransferStatus.COMPLETED
    elif status_rand < 17:
        status = VaultTransferStatus.IN_TRANSIT
    elif status_rand < 19:
        status = VaultTransferStatus.PENDING
    else:
        status = VaultTransferStatus.CANCELLED

    # Dates
    days_ago = int((index / VAULT_TRANSFERS_COUNT) * 180)  # Distribute over 6 months
    requested_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_ago)

    approved_by_id = None
    approved_at = None
    completed_at = None
    cancelled_at = None

    # Set timestamps based on status
    if status in [VaultTransferStatus.IN_TRANSIT, VaultTransferStatus.COMPLETED]:
        approved_by_id = user.id
        approved_at = requested_at + timedelta(hours=1)

    if status == VaultTransferStatus.COMPLETED:
        completed_at = approved_at + timedelta(hours=random.randint(2, 24))

    if status == VaultTransferStatus.CANCELLED:
        cancelled_at = requested_at + timedelta(hours=random.randint(1, 48))

    # Notes
    notes = None
    if transfer_type == VaultTransferType.EMERGENCY:
        notes = "Emergency transfer - urgent replenishment required"
    elif status == VaultTransferStatus.CANCELLED:
        notes = "Transfer cancelled - no longer needed"

    return {
        "from_vault_id": from_vault.id,
        "to_vault_id": to_vault.id,
        "currency_id": currency.id,
        "amount": round(amount, 2),
        "transfer_type": transfer_type,
        "status": status,
        "requested_by_id": user.id,
        "approved_by_id": approved_by_id,
        "requested_at": requested_at,
        "approved_at": approved_at,
        "completed_at": completed_at,
        "cancelled_at": cancelled_at,
        "notes": notes
    }


async def create_vault_transfers(
    db: AsyncSession,
    vaults: list,
    currencies: dict,
    users: list
):
    """Create sample vault transfers (10x version)"""

    print(f"\n🔄 Creating {VAULT_TRANSFERS_COUNT} vault transfers...")

    if len(vaults) < 2:
        print("  ⚠️  Need at least 2 vaults for transfers")
        return

    created_count = 0

    for i in range(VAULT_TRANSFERS_COUNT):
        transfer_data = generate_vault_transfer(i, vaults, currencies, users)

        transfer = VaultTransfer(
            from_vault_id=transfer_data["from_vault_id"],
            to_vault_id=transfer_data["to_vault_id"],
            currency_id=transfer_data["currency_id"],
            amount=transfer_data["amount"],
            transfer_type=transfer_data["transfer_type"],
            status=transfer_data["status"],
            requested_by_id=transfer_data["requested_by_id"],
            approved_by_id=transfer_data.get("approved_by_id"),
            requested_at=transfer_data["requested_at"],
            approved_at=transfer_data.get("approved_at"),
            completed_at=transfer_data.get("completed_at"),
            cancelled_at=transfer_data.get("cancelled_at"),
            notes=transfer_data.get("notes")
        )

        db.add(transfer)
        created_count += 1

        if created_count % 10 == 0:
            await db.flush()
            print(f"  Created {created_count} transfers...")

    await db.flush()
    print(f"  ✅ Created {VAULT_TRANSFERS_COUNT} vault transfers")


async def seed_vaults(db: AsyncSession):
    """Main seeding function"""

    print("\n🏦 Seeding vaults (10X VERSION)...\n")
    print("=" * 60)
    print("CEMS Vault Seeding - 10X Data Volume")
    print("=" * 60)
    print()

    # Get required data
    data = await get_required_data(db)

    # Create main vault
    main_vault = await create_main_vault(db)

    # Create branch vaults
    branch_vaults = await create_branch_vaults(db, data["branches"])

    # All vaults list
    all_vaults = [main_vault] + list(branch_vaults.values())

    # Create balances for main vault (higher amounts)
    main_balances = {
        "TRY": Decimal("5000000.00"),
        "USD": Decimal("500000.00"),
        "EUR": Decimal("300000.00"),
        "GBP": Decimal("200000.00"),
        "SAR": Decimal("1000000.00"),
    }
    await create_vault_balances(db, main_vault, data["currencies"], main_balances)

    # Create balances for branch vaults (lower amounts)
    branch_balances = {
        "TRY": Decimal("500000.00"),
        "USD": Decimal("50000.00"),
        "EUR": Decimal("30000.00"),
        "GBP": Decimal("20000.00"),
        "SAR": Decimal("100000.00"),
    }
    for vault in branch_vaults.values():
        await create_vault_balances(db, vault, data["currencies"], branch_balances)

    # Create vault transfers (10x)
    await create_vault_transfers(db, all_vaults, data["currencies"], data["users"])

    # Commit all changes
    await db.commit()

    print()
    print("=" * 60)
    print("✅ Vault Seeding Complete!")
    print("=" * 60)
    print()
    print("📊 Summary:")
    print(f"   • Main Vault: 1")
    print(f"   • Branch Vaults: {len(branch_vaults)}")
    print(f"   • Total Vaults: {len(all_vaults)}")
    print(f"   • Vault Transfers: {VAULT_TRANSFERS_COUNT}")
    print()


async def show_vaults():
    """Display vault summary"""
    print("=" * 60)
    print("Vault Summary")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as db:
        # Count vaults by type
        result = await db.execute(
            select(func.count(Vault.id)).where(Vault.vault_type == VaultType.MAIN)
        )
        main_count = result.scalar()

        result = await db.execute(
            select(func.count(Vault.id)).where(Vault.vault_type == VaultType.BRANCH)
        )
        branch_count = result.scalar()

        # Count transfers by status
        result = await db.execute(
            select(func.count(VaultTransfer.id))
            .where(VaultTransfer.status == VaultTransferStatus.COMPLETED)
        )
        completed_count = result.scalar()

        result = await db.execute(
            select(func.count(VaultTransfer.id))
            .where(VaultTransfer.status == VaultTransferStatus.IN_TRANSIT)
        )
        in_transit_count = result.scalar()

        result = await db.execute(
            select(func.count(VaultTransfer.id))
            .where(VaultTransfer.status == VaultTransferStatus.PENDING)
        )
        pending_count = result.scalar()

        result = await db.execute(select(func.count(VaultTransfer.id)))
        total_transfers = result.scalar()

        print(f"Vaults:")
        print(f"  🏦 Main: {main_count}")
        print(f"  🏢 Branch: {branch_count}")
        print(f"  📊 Total: {main_count + branch_count}\n")

        print(f"Vault Transfers:")
        print(f"  ✅ Completed: {completed_count}")
        print(f"  🚚 In Transit: {in_transit_count}")
        print(f"  ⏳ Pending: {pending_count}")
        print(f"  📊 Total: {total_transfers}")
        print()


async def main():
    """Main entry point"""
    print("\n🌱 Starting vault data seeding (10X VERSION)...\n")

    try:
        async with AsyncSessionLocal() as db:
            await seed_vaults(db)

        print("✨ Vault seeding completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        asyncio.run(show_vaults())
    else:
        asyncio.run(main())
