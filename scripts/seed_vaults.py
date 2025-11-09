#!/usr/bin/env python3
"""
Seed Vaults Script
Creates initial vault setup with balances for testing
Run this after seed_branches.py

Creates:
- Main Central Vault
- Branch Vaults (one per branch)
- Initial vault balances for major currencies
- Sample vault transfers (completed and pending)

Usage:
    python scripts/seed_vaults.py          # Seed vaults
    python scripts/seed_vaults.py --show   # Show vaults summary
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.db.models.vault import Vault, VaultBalance, VaultTransfer, VaultType, VaultTransferType, VaultTransferStatus
from app.db.models.branch import Branch
from app.db.models.currency import Currency
from app.db.models.user import User


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
    
    return {
        "admin": admin,
        "branches": branches,
        "currencies": currencies
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
            print(f"  ⚠️  Currency {currency_code} not found, skipping")
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
            print(f"  ⚠️  Balance for {currency_code} already exists")
            continue
        
        # Create balance
        balance = VaultBalance(
            vault_id=vault.id,
            currency_id=currency.id,
            balance=amount,
            last_updated=datetime.utcnow()
        )
        
        db.add(balance)
        print(f"  ✅ {currency_code}: {amount:,.2f}")


async def create_sample_transfers(
    db: AsyncSession,
    main_vault: Vault,
    branch_vaults: dict,
    branches: dict,
    currencies: dict,
    admin: User
):
    """Create sample vault transfers for testing"""
    
    print("\n🔄 Creating sample vault transfers...")
    
    # Check if transfers already exist
    result = await db.execute(select(VaultTransfer))
    if result.scalars().first():
        print("  ⚠️  Transfers already exist, skipping")
        return
    
    # Completed transfer: Main vault to BR001
    if "BR001" in branch_vaults and "USD" in currencies:
        transfer1 = VaultTransfer(
            transfer_number="VTR-20250109-00001",
            from_vault_id=main_vault.id,
            to_vault_id=None,
            to_branch_id=branches["BR001"].id,
            currency_id=currencies["USD"].id,
            amount=Decimal("50000.00"),
            transfer_type=VaultTransferType.VAULT_TO_BRANCH,
            status=VaultTransferStatus.COMPLETED,
            initiated_by=admin.id,
            approved_by=admin.id,
            received_by=admin.id,
            initiated_at=datetime.utcnow() - timedelta(days=7),
            approved_at=datetime.utcnow() - timedelta(days=7),
            completed_at=datetime.utcnow() - timedelta(days=7),
            notes="Initial branch funding - January 2025"
        )
        db.add(transfer1)
        print(f"  ✅ Completed: VTR-20250109-00001 - $50,000 to BR001")
    
    # Completed transfer: Main vault to BR002
    if "BR002" in branch_vaults and "EUR" in currencies:
        transfer2 = VaultTransfer(
            transfer_number="VTR-20250109-00002",
            from_vault_id=main_vault.id,
            to_vault_id=None,
            to_branch_id=branches["BR002"].id,
            currency_id=currencies["EUR"].id,
            amount=Decimal("30000.00"),
            transfer_type=VaultTransferType.VAULT_TO_BRANCH,
            status=VaultTransferStatus.COMPLETED,
            initiated_by=admin.id,
            approved_by=admin.id,
            received_by=admin.id,
            initiated_at=datetime.utcnow() - timedelta(days=5),
            approved_at=datetime.utcnow() - timedelta(days=5),
            completed_at=datetime.utcnow() - timedelta(days=5),
            notes="European currency allocation"
        )
        db.add(transfer2)
        print(f"  ✅ Completed: VTR-20250109-00002 - €30,000 to BR002")
    
    # Pending transfer: Main vault to BR003 (requires approval)
    if "BR003" in branch_vaults and "USD" in currencies:
        transfer3 = VaultTransfer(
            transfer_number="VTR-20250110-00001",
            from_vault_id=main_vault.id,
            to_vault_id=None,
            to_branch_id=branches["BR003"].id,
            currency_id=currencies["USD"].id,
            amount=Decimal("75000.00"),  # Large amount - requires approval
            transfer_type=VaultTransferType.VAULT_TO_BRANCH,
            status=VaultTransferStatus.PENDING,
            initiated_by=admin.id,
            approved_by=None,
            received_by=None,
            initiated_at=datetime.utcnow() - timedelta(hours=2),
            approved_at=None,
            completed_at=None,
            notes="Weekly funding allocation - pending manager approval"
        )
        db.add(transfer3)
        print(f"  ✅ Pending: VTR-20250110-00001 - $75,000 to BR003 (needs approval)")
    
    # In-transit transfer: BR001 returning excess cash
    if "BR001" in branch_vaults and "TRY" in currencies:
        transfer4 = VaultTransfer(
            transfer_number="VTR-20250110-00002",
            from_vault_id=branch_vaults["BR001"].id,
            to_vault_id=main_vault.id,
            to_branch_id=None,
            currency_id=currencies["TRY"].id,
            amount=Decimal("100000.00"),
            transfer_type=VaultTransferType.VAULT_TO_VAULT,
            status=VaultTransferStatus.IN_TRANSIT,
            initiated_by=admin.id,
            approved_by=admin.id,
            received_by=None,
            initiated_at=datetime.utcnow() - timedelta(hours=1),
            approved_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=None,
            notes="Excess TRY cash return to main vault"
        )
        db.add(transfer4)
        print(f"  ✅ In-Transit: VTR-20250110-00002 - ₺100,000 from BR001 to Main")


async def show_summary(db: AsyncSession):
    """Display summary of seeded vaults"""
    
    print("\n" + "="*60)
    print("📊 VAULT SEEDING SUMMARY")
    print("="*60)
    
    # Count vaults
    result = await db.execute(select(Vault))
    all_vaults = result.scalars().all()
    
    main_vaults = [v for v in all_vaults if v.vault_type == VaultType.MAIN]
    branch_vaults = [v for v in all_vaults if v.vault_type == VaultType.BRANCH]
    
    print(f"\n🏦 Vaults Created:")
    print(f"   Main Vaults: {len(main_vaults)}")
    print(f"   Branch Vaults: {len(branch_vaults)}")
    print(f"   Total: {len(all_vaults)}")
    
    # Count balances
    result = await db.execute(select(VaultBalance))
    balances = result.scalars().all()
    print(f"\n💰 Balances Created: {len(balances)}")
    
    # Count transfers
    result = await db.execute(select(VaultTransfer))
    transfers = result.scalars().all()
    
    completed = len([t for t in transfers if t.status == VaultTransferStatus.COMPLETED])
    pending = len([t for t in transfers if t.status == VaultTransferStatus.PENDING])
    in_transit = len([t for t in transfers if t.status == VaultTransferStatus.IN_TRANSIT])
    
    print(f"\n🔄 Transfers Created: {len(transfers)}")
    print(f"   Completed: {completed}")
    print(f"   Pending: {pending}")
    print(f"   In-Transit: {in_transit}")
    
    print("\n" + "="*60)
    print("✨ Vault seeding completed successfully!")
    print("="*60)


async def seed_vaults(db: AsyncSession):
    """Main seeding function"""
    
    # Get required data
    data = await get_required_data(db)
    
    # Create main vault
    main_vault = await create_main_vault(db)
    
    # Create main vault balances (large reserves)
    main_balances = {
        "USD": Decimal("1000000.00"),  # $1M
        "EUR": Decimal("500000.00"),   # €500K
        "TRY": Decimal("5000000.00"),  # ₺5M
        "GBP": Decimal("300000.00"),   # £300K
        "SAR": Decimal("2000000.00"),  # SAR 2M
        "AED": Decimal("2000000.00"),  # AED 2M
    }
    await create_vault_balances(db, main_vault, data["currencies"], main_balances)
    
    # Create branch vaults
    branch_vaults = await create_branch_vaults(db, data["branches"])
    
    # Create balances for each branch vault
    branch_balances = {
        "USD": Decimal("50000.00"),
        "EUR": Decimal("30000.00"),
        "TRY": Decimal("200000.00"),
        "GBP": Decimal("20000.00"),
    }
    
    for vault in branch_vaults.values():
        await create_vault_balances(db, vault, data["currencies"], branch_balances)
    
    # Create sample transfers
    await create_sample_transfers(
        db,
        main_vault,
        branch_vaults,
        data["branches"],
        data["currencies"],
        data["admin"]
    )
    
    # Commit all changes
    await db.commit()
    
    # Show summary
    await show_summary(db)


async def main():
    """Main function"""
    
    # Check for --show flag
    show_only = "--show" in sys.argv
    
    if show_only:
        print("\n📊 Displaying vault summary...\n")
        async with AsyncSessionLocal() as db:
            await show_summary(db)
        return
    
    print("\n🌱 Starting vault data seeding...\n")
    print("="*60)
    
    try:
        async with AsyncSessionLocal() as db:
            await seed_vaults(db)
        
        print("\n🎉 Vault seeding process completed!")
        print("\n💡 Next steps:")
        print("   1. Run: python scripts/seed_vaults.py --show")
        print("   2. Test API: http://localhost:8000/docs")
        print("   3. Try vault endpoints: GET /api/v1/vault")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
