#!/usr/bin/env python3
"""Branch Seeding Script - Final Fixed Version"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionLocal
from app.db.models.branch import Branch, BranchBalance
from app.db.models.currency import Currency

async def seed_branches(db: AsyncSession):
    print("📍 Seeding branches...")
    
    # Get currencies
    try_result = await db.execute(select(Currency).where(Currency.code == "TRY"))
    try_currency = try_result.scalar_one_or_none()
    
    usd_result = await db.execute(select(Currency).where(Currency.code == "USD"))
    usd_currency = usd_result.scalar_one_or_none()
    
    eur_result = await db.execute(select(Currency).where(Currency.code == "EUR"))
    eur_currency = eur_result.scalar_one_or_none()
    
    if not all([try_currency, usd_currency, eur_currency]):
        print("❌ Error: Required currencies not found!")
        return
    
    count_result = await db.execute(select(func.count()).select_from(Branch))
    if count_result.scalar() > 0:
        print("⚠️  Branches already exist. Skipping...")
        return
    
    # ✅ USE STRING VALUES DIRECTLY
    branches_data = [
        {
            "code": "BR001",
            "name_en": "Main Branch - Taksim",
            "name_ar": "الفرع الرئيسي - تقسيم",
            "region": "Istanbul_European",  # ✅ String value
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
            "region": "Istanbul_Asian",
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
            "region": "Ankara",
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
            "region": "Izmir",
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
            "region": "Bursa",
            "address": "Osmangazi District, Kent Meydanı 15",
            "city": "Bursa",
            "phone": "+902241234567",
            "email": "osmangazi@cems.com",
            "is_main_branch": False,
            "opening_balance_date": datetime.utcnow() - timedelta(days=30),
        },
    ]
    
    branches = []
    for data in branches_data:
        branch = Branch(**data)
        db.add(branch)
        branches.append(branch)
        print(f"✅ Created branch: {data['code']} - {data['name_en']}")
    
    await db.flush()
    
    print("\n💰 Creating branch balances...")
    
    balances_data = [
        {"branch": branches[0], "balances": [
            {"currency": try_currency, "balance": Decimal("500000.00"), "reserved": Decimal("50000.00"), "min_threshold": Decimal("100000.00"), "max_threshold": Decimal("1000000.00")},
            {"currency": usd_currency, "balance": Decimal("150000.00"), "reserved": Decimal("10000.00"), "min_threshold": Decimal("30000.00"), "max_threshold": Decimal("300000.00")},
            {"currency": eur_currency, "balance": Decimal("120000.00"), "reserved": Decimal("8000.00"), "min_threshold": Decimal("25000.00"), "max_threshold": Decimal("250000.00")},
        ]},
        {"branch": branches[1], "balances": [
            {"currency": try_currency, "balance": Decimal("250000.00"), "reserved": Decimal("25000.00"), "min_threshold": Decimal("50000.00"), "max_threshold": Decimal("500000.00")},
            {"currency": usd_currency, "balance": Decimal("75000.00"), "reserved": Decimal("5000.00"), "min_threshold": Decimal("15000.00"), "max_threshold": Decimal("150000.00")},
            {"currency": eur_currency, "balance": Decimal("60000.00"), "reserved": Decimal("4000.00"), "min_threshold": Decimal("12000.00"), "max_threshold": Decimal("120000.00")},
        ]},
        {"branch": branches[2], "balances": [
            {"currency": try_currency, "balance": Decimal("300000.00"), "reserved": Decimal("30000.00"), "min_threshold": Decimal("60000.00"), "max_threshold": Decimal("600000.00")},
            {"currency": usd_currency, "balance": Decimal("90000.00"), "reserved": Decimal("7000.00"), "min_threshold": Decimal("18000.00"), "max_threshold": Decimal("180000.00")},
            {"currency": eur_currency, "balance": Decimal("70000.00"), "reserved": Decimal("5000.00"), "min_threshold": Decimal("15000.00"), "max_threshold": Decimal("150000.00")},
        ]},
        {"branch": branches[3], "balances": [
            {"currency": try_currency, "balance": Decimal("200000.00"), "reserved": Decimal("20000.00"), "min_threshold": Decimal("40000.00"), "max_threshold": Decimal("400000.00")},
            {"currency": usd_currency, "balance": Decimal("60000.00"), "reserved": Decimal("4000.00"), "min_threshold": Decimal("12000.00"), "max_threshold": Decimal("120000.00")},
            {"currency": eur_currency, "balance": Decimal("50000.00"), "reserved": Decimal("3000.00"), "min_threshold": Decimal("10000.00"), "max_threshold": Decimal("100000.00")},
        ]},
        {"branch": branches[4], "balances": [
            {"currency": try_currency, "balance": Decimal("150000.00"), "reserved": Decimal("15000.00"), "min_threshold": Decimal("30000.00"), "max_threshold": Decimal("300000.00")},
            {"currency": usd_currency, "balance": Decimal("45000.00"), "reserved": Decimal("3000.00"), "min_threshold": Decimal("9000.00"), "max_threshold": Decimal("90000.00")},
            {"currency": eur_currency, "balance": Decimal("35000.00"), "reserved": Decimal("2000.00"), "min_threshold": Decimal("7000.00"), "max_threshold": Decimal("70000.00")},
        ]},
    ]
    
    balance_count = 0
    for branch_data in balances_data:
        for balance_data in branch_data["balances"]:
            balance = BranchBalance(
                branch_id=branch_data["branch"].id,
                currency_id=balance_data["currency"].id,
                balance=balance_data["balance"],
                reserved_balance=balance_data["reserved"],
                minimum_threshold=balance_data["min_threshold"],
                maximum_threshold=balance_data["max_threshold"],
            )
            db.add(balance)
            balance_count += 1
    
    await db.commit()
    print(f"✅ Created {balance_count} branch balances")
    print(f"\n🎉 Successfully seeded {len(branches)} branches!")

async def main():
    print("🌱 Starting branch data seeding...\n")
    try:
        async with AsyncSessionLocal() as db:
            await seed_branches(db)
        print("\n✅ Branch seeding completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
