"""
Seed data for Branch Management Module
Creates sample branches with balances for testing

Usage:
    python scripts/seed_branches.py
"""

import asyncio
import sys
from pathlib import Path
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


from app.db.models.branch import Branch, BranchBalance, RegionEnum
from app.db.models.currency import Currency


async def seed_branches(db: AsyncSession):
    """
    Seed sample branches with balances
    """
    
    print("🌱 Starting branch data seeding...")
    
    # Get currencies (assuming they're already seeded)
    stmt = select(Currency).where(Currency.code == "TRY")
    result = await db.execute(stmt)
    try_currency = result.scalar_one_or_none()
    
    stmt = select(Currency).where(Currency.code == "USD")
    result = await db.execute(stmt)
    usd_currency = result.scalar_one_or_none()
    
    stmt = select(Currency).where(Currency.code == "EUR")
    result = await db.execute(stmt)
    eur_currency = result.scalar_one_or_none()
    
    if not try_currency or not usd_currency or not eur_currency:
        raise Exception("Currencies not found. Please seed currencies first.")
    
    # Check if branches already exist
    stmt = select(func.count()).select_from(Branch)
    result = await db.execute(stmt)
    existing_branches = result.scalar()
    
    if existing_branches > 0:
        print(f"⚠️  Branches already exist ({existing_branches} branches found). Skipping seed.")
        return
    
    # ==================== Create Branches ====================
    
    branches_data = [
        {
            "code": "BR001",
            "name_en": "Main Branch - Taksim",
            "name_ar": "الفرع الرئيسي - تقسيم",
            "region": RegionEnum.ISTANBUL_EUROPEAN,
            "address": "Taksim Square, Beyoğlu",
            "city": "Istanbul",
            "phone": "+905551234567",
            "email": "taksim@cems.com",
            "is_main_branch": True,
            "opening_balance_date": datetime.utcnow() - timedelta(days=365),
        },
        {
            "code": "BR002",
            "name_en": "Kadıköy Branch",
            "name_ar": "فرع كاديكوي",
            "region": RegionEnum.ISTANBUL_ASIAN,
            "address": "Kadıköy Center, Moda Street 45",
            "city": "Istanbul",
            "phone": "+905551234568",
            "email": "kadikoy@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=180),
        },
        {
            "code": "BR003",
            "name_en": "Ankara Kızılay Branch",
            "name_ar": "فرع أنقرة - كيزيلاي",
            "region": RegionEnum.ANKARA,
            "address": "Kızılay Square, Atatürk Boulevard 123",
            "city": "Ankara",
            "phone": "+903121234567",
            "email": "kizilay@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=90),
        },
        {
            "code": "BR004",
            "name_en": "Izmir Konak Branch",
            "name_ar": "فرع إزمير - كوناك",
            "region": RegionEnum.IZMIR,
            "address": "Konak Pier, Atatürk Street 78",
            "city": "Izmir",
            "phone": "+902321234567",
            "email": "konak@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=60),
        },
        {
            "code": "BR005",
            "name_en": "Bursa Osmangazi Branch",
            "name_ar": "فرع بورصة - عثمان غازي",
            "region": RegionEnum.BURSA,
            "address": "Osmangazi District, Kent Meydanı 15",
            "city": "Bursa",
            "phone": "+902241234567",
            "email": "osmangazi@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=30),
        },
    ]
    
    branches = []
    for branch_data in branches_data:
        branch = Branch(
            id=uuid.uuid4(),
            **branch_data
        )
        db.add(branch)
        branches.append(branch)
        print(f"✅ Created branch: {branch.code} - {branch.name_en}")
    
    await db.flush()  # Flush to get branch IDs
    
    # ==================== Create Branch Balances ====================
    
    print("\n💰 Creating branch balances...")
    
    balance_configs = [
        # Main Branch (BR001) - Highest balances
        {
            "branch": branches[0],
            "balances": [
                {
                    "currency": try_currency,
                    "balance": Decimal("500000.00"),
                    "reserved": Decimal("50000.00"),
                    "min_threshold": Decimal("100000.00"),
                    "max_threshold": Decimal("1000000.00"),
                },
                {
                    "currency": usd_currency,
                    "balance": Decimal("150000.00"),
                    "reserved": Decimal("10000.00"),
                    "min_threshold": Decimal("30000.00"),
                    "max_threshold": Decimal("300000.00"),
                },
                {
                    "currency": eur_currency,
                    "balance": Decimal("120000.00"),
                    "reserved": Decimal("8000.00"),
                    "min_threshold": Decimal("25000.00"),
                    "max_threshold": Decimal("250000.00"),
                },
            ]
        },
        # Kadıköy Branch (BR002)
        {
            "branch": branches[1],
            "balances": [
                {
                    "currency": try_currency,
                    "balance": Decimal("250000.00"),
                    "reserved": Decimal("25000.00"),
                    "min_threshold": Decimal("50000.00"),
                    "max_threshold": Decimal("500000.00"),
                },
                {
                    "currency": usd_currency,
                    "balance": Decimal("75000.00"),
                    "reserved": Decimal("5000.00"),
                    "min_threshold": Decimal("15000.00"),
                    "max_threshold": Decimal("150000.00"),
                },
                {
                    "currency": eur_currency,
                    "balance": Decimal("60000.00"),
                    "reserved": Decimal("4000.00"),
                    "min_threshold": Decimal("12000.00"),
                    "max_threshold": Decimal("120000.00"),
                },
            ]
        },
        # Ankara Branch (BR003)
        {
            "branch": branches[2],
            "balances": [
                {
                    "currency": try_currency,
                    "balance": Decimal("300000.00"),
                    "reserved": Decimal("30000.00"),
                    "min_threshold": Decimal("60000.00"),
                    "max_threshold": Decimal("600000.00"),
                },
                {
                    "currency": usd_currency,
                    "balance": Decimal("90000.00"),
                    "reserved": Decimal("6000.00"),
                    "min_threshold": Decimal("18000.00"),
                    "max_threshold": Decimal("180000.00"),
                },
                {
                    "currency": eur_currency,
                    "balance": Decimal("70000.00"),
                    "reserved": Decimal("5000.00"),
                    "min_threshold": Decimal("14000.00"),
                    "max_threshold": Decimal("140000.00"),
                },
            ]
        },
        # Izmir Branch (BR004)
        {
            "branch": branches[3],
            "balances": [
                {
                    "currency": try_currency,
                    "balance": Decimal("200000.00"),
                    "reserved": Decimal("20000.00"),
                    "min_threshold": Decimal("40000.00"),
                    "max_threshold": Decimal("400000.00"),
                },
                {
                    "currency": usd_currency,
                    "balance": Decimal("60000.00"),
                    "reserved": Decimal("4000.00"),
                    "min_threshold": Decimal("12000.00"),
                    "max_threshold": Decimal("120000.00"),
                },
                {
                    "currency": eur_currency,
                    "balance": Decimal("50000.00"),
                    "reserved": Decimal("3000.00"),
                    "min_threshold": Decimal("10000.00"),
                    "max_threshold": Decimal("100000.00"),
                },
            ]
        },
        # Bursa Branch (BR005) - Newest, lowest balances
        {
            "branch": branches[4],
            "balances": [
                {
                    "currency": try_currency,
                    "balance": Decimal("150000.00"),
                    "reserved": Decimal("15000.00"),
                    "min_threshold": Decimal("30000.00"),
                    "max_threshold": Decimal("300000.00"),
                },
                {
                    "currency": usd_currency,
                    "balance": Decimal("45000.00"),
                    "reserved": Decimal("3000.00"),
                    "min_threshold": Decimal("9000.00"),
                    "max_threshold": Decimal("90000.00"),
                },
                {
                    "currency": eur_currency,
                    "balance": Decimal("35000.00"),
                    "reserved": Decimal("2000.00"),
                    "min_threshold": Decimal("7000.00"),
                    "max_threshold": Decimal("70000.00"),
                },
            ]
        },
    ]
    
    for config in balance_configs:
        branch = config["branch"]
        for balance_data in config["balances"]:
            branch_balance = BranchBalance(
                id=uuid.uuid4(),
                branch_id=branch.id,
                currency_id=balance_data["currency"].id,
                balance=balance_data["balance"],
                reserved_balance=balance_data["reserved"],
                minimum_threshold=balance_data["min_threshold"],
                maximum_threshold=balance_data["max_threshold"],
                last_updated=datetime.utcnow(),
            )
            db.add(branch_balance)
            print(f"  💵 {branch.code} - {balance_data['currency'].code}: "
                  f"{balance_data['balance']} (Available: {balance_data['balance'] - balance_data['reserved']})")
    
    # Commit all changes
    await db.commit()
    
    print("\n✨ Branch seeding completed successfully!")
    print(f"   📊 Total branches: {len(branches)}")
    print(f"   💰 Total balances: {len(branches) * 3}")
    
    # Print summary
    print("\n📋 Branch Summary:")
    for branch in branches:
        status = "🏛️  MAIN" if branch.is_main_branch else "🏢"
        print(f"   {status} {branch.code}: {branch.name_en} ({branch.region.value})")


async def seed_sample_alerts(db: AsyncSession):
    """
    Create sample alerts for testing
    """
    from app.db.models.branch import BranchAlert, BalanceAlertType, AlertSeverity
    
    print("\n🚨 Creating sample alerts...")
    
    # Get a branch
    stmt = select(Branch).where(Branch.code == "BR005")
    result = await db.execute(stmt)
    branch = result.scalar_one_or_none()
    
    if not branch:
        print("⚠️  Branch BR005 not found. Skipping alerts.")
        return
    
    # Get TRY currency
    stmt = select(Currency).where(Currency.code == "TRY")
    result = await db.execute(stmt)
    try_currency = result.scalar_one_or_none()
    
    # Create low balance alert for Bursa branch
    alert = BranchAlert(
        id=uuid.uuid4(),
        branch_id=branch.id,
        currency_id=try_currency.id,
        alert_type=BalanceAlertType.LOW_BALANCE,
        severity=AlertSeverity.WARNING,
        title="Low Balance Warning",
        message=f"Balance for {branch.name_en} has fallen below recommended threshold",
        triggered_at=datetime.utcnow() - timedelta(hours=2),
        is_resolved=False,
    )
    db.add(alert)
    print(f"  🚨 Created alert: {alert.title}")
    
    await db.commit()
    print("✅ Sample alerts created successfully!")


# ==================== Main Execution ====================

if __name__ == "__main__":
    from app.db.base import AsyncSessionLocal
    
    async def main():
        async with AsyncSessionLocal() as db:
            try:
                # Seed branches
                await seed_branches(db)
                
                # Seed sample alerts
                await seed_sample_alerts(db)
                
            except Exception as e:
                print(f"❌ Error during seeding: {str(e)}")
                await db.rollback()
                raise
    
    asyncio.run(main())