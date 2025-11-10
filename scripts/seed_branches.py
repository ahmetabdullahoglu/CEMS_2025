#!/usr/bin/env python3
"""
Seed script for Branch data
Creates sample branches with initial balances
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
from app.db.models.branch import Branch, BranchBalance, RegionEnum
from app.db.models.currency import Currency


async def seed_branches(db: AsyncSession):
    """Seed branches with initial data"""
    
    print("📍 Seeding branches...")
    
    # Get currencies
    result = await db.execute(select(Currency).where(Currency.code.in_(["TRY", "USD", "EUR"])))
    currencies = {c.code: c for c in result.scalars().all()}
    
    if not currencies:
        print("❌ No currencies found. Please run seed_currencies.py first.")
        return
    
    # Check if branches already exist
    result = await db.execute(select(Branch))
    if result.scalars().first():
        print("⚠️  Branches already exist. Skipping...")
        return
    
    # Branch data - using RegionEnum members (will be converted to values by Model)
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
            "balances": {
                "TRY": Decimal("500000.00"),
                "USD": Decimal("50000.00"),
                "EUR": Decimal("30000.00"),
            }
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
            "balances": {
                "TRY": Decimal("300000.00"),
                "USD": Decimal("25000.00"),
                "EUR": Decimal("15000.00"),
            }
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
            "balances": {
                "TRY": Decimal("250000.00"),
                "USD": Decimal("20000.00"),
                "EUR": Decimal("10000.00"),
            }
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
            "balances": {
                "TRY": Decimal("200000.00"),
                "USD": Decimal("15000.00"),
                "EUR": Decimal("8000.00"),
            }
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
            "balances": {
                "TRY": Decimal("150000.00"),
                "USD": Decimal("12000.00"),
                "EUR": Decimal("6000.00"),
            }
        },
        # ========== ADDITIONAL BRANCHES (DOUBLE DATA) ==========
        {
            "code": "BR006",
            "name_en": "Antalya Muratpaşa Branch",
            "name_ar": "فرع أنطاليا - موراتباشا",
            "region": RegionEnum.ANTALYA,
            "address": "Muratpaşa Boulevard, Lara 90",
            "city": "Antalya",
            "phone": "+902421234567",
            "email": "muratpasa@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=45),
            "balances": {
                "TRY": Decimal("180000.00"),
                "USD": Decimal("18000.00"),
                "EUR": Decimal("9000.00"),
            }
        },
        {
            "code": "BR007",
            "name_en": "Adana Seyhan Branch",
            "name_ar": "فرع أضنة - سيحان",
            "region": RegionEnum.ADANA,
            "address": "Seyhan District, İnönü Street 45",
            "city": "Adana",
            "phone": "+903221234567",
            "email": "seyhan@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=50),
            "balances": {
                "TRY": Decimal("170000.00"),
                "USD": Decimal("16000.00"),
                "EUR": Decimal("8000.00"),
            }
        },
        {
            "code": "BR008",
            "name_en": "Gaziantep Şahinbey Branch",
            "name_ar": "فرع غازي عنتاب - شاهين بي",
            "region": RegionEnum.GAZIANTEP,
            "address": "Şahinbey Center, 100.Yıl Boulevard 120",
            "city": "Gaziantep",
            "phone": "+903421234567",
            "email": "sahinbey@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=55),
            "balances": {
                "TRY": Decimal("160000.00"),
                "USD": Decimal("14000.00"),
                "EUR": Decimal("7500.00"),
            }
        },
        {
            "code": "BR009",
            "name_en": "Konya Selçuklu Branch",
            "name_ar": "فرع قونية - سلجوقلو",
            "region": RegionEnum.KONYA,
            "address": "Selçuklu Center, Mevlana Street 78",
            "city": "Konya",
            "phone": "+903321234567",
            "email": "selcuklu@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=65),
            "balances": {
                "TRY": Decimal("140000.00"),
                "USD": Decimal("13000.00"),
                "EUR": Decimal("6500.00"),
            }
        },
        {
            "code": "BR010",
            "name_en": "Mersin Akdeniz Branch",
            "name_ar": "فرع مرسين - أكدينيز",
            "region": RegionEnum.MERSIN,
            "address": "Akdeniz District, Harbour Avenue 55",
            "city": "Mersin",
            "phone": "+903241234567",
            "email": "akdeniz@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=75),
            "balances": {
                "TRY": Decimal("135000.00"),
                "USD": Decimal("11000.00"),
                "EUR": Decimal("5500.00"),
            }
        }
    ]
    
    # Create branches
    for branch_data in branches_data:
        # Extract balances data
        balances_data = branch_data.pop("balances")
        
        # Create branch
        branch = Branch(**branch_data)
        db.add(branch)
        await db.flush()  # Get branch ID
        
        print(f"✅ Created branch: {branch.code} - {branch.name_en}")
        
        # Create balances for each currency
        for currency_code, balance_amount in balances_data.items():
            currency = currencies.get(currency_code)
            if currency:
                branch_balance = BranchBalance(
                    branch_id=branch.id,
                    currency_id=currency.id,
                    balance=balance_amount,
                    reserved_balance=Decimal("0"),
                    minimum_threshold=balance_amount * Decimal("0.1"),  # 10% of opening
                    maximum_threshold=balance_amount * Decimal("5.0"),   # 500% of opening
                    last_reconciled_at=datetime.utcnow()
                )
                db.add(branch_balance)
                print(f"   💰 {currency_code}: {balance_amount:,.2f}")
    
    await db.commit()
    print(f"\n✅ Successfully seeded {len(branches_data)} branches")


async def main():
    """Main seeding function"""
    print("\n🌱 Starting branch data seeding...\n")
    
    try:
        async with AsyncSessionLocal() as db:
            await seed_branches(db)
        
        print("\n✨ Branch seeding completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())