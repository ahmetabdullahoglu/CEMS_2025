#!/usr/bin/env python3
"""
Seed Transactions Script
Creates sample transactions of all types for testing
Run this after seed_customers.py

Transaction Types:
- Income: Service fees and commissions
- Expense: Rent, salaries, utilities
- Exchange: Currency conversions with customers
- Transfer: Between branches

Usage:
    python scripts/seed_transactions.py          # Seed transactions (skip if exist)
    python scripts/seed_transactions.py --force  # Force seed even if exist
    python scripts/seed_transactions.py --show   # Show transactions summary
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.base import AsyncSessionLocal
from app.db.models.transaction import (
    Transaction, IncomeTransaction, ExpenseTransaction,
    ExchangeTransaction, TransferTransaction,
    TransactionType, TransactionStatus,
    IncomeCategory, ExpenseCategory, TransferType
)
from app.db.models.branch import Branch
from app.db.models.currency import Currency
from app.db.models.customer import Customer
from app.db.models.user import User
from app.services.transaction_service import TransactionService


async def get_required_data(db: AsyncSession):
    """Get all required data for creating transactions"""
    
    # Get admin user
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if not admin:
        raise Exception("Admin user not found. Please run seed_data.py first.")
    
    # Get teller user (if exists)
    result = await db.execute(select(User).where(User.username == "teller"))
    teller = result.scalar_one_or_none()
    
    # Get all branches
    result = await db.execute(select(Branch).where(Branch.is_active == True))
    branches = list(result.scalars().all())
    if not branches:
        raise Exception("No branches found. Please run seed_branches.py first.")
    
    # Get currencies
    result = await db.execute(select(Currency).where(Currency.is_active == True))
    currencies = {c.code: c for c in result.scalars().all()}
    if not currencies:
        raise Exception("No currencies found. Please run seed_currencies.py first.")
    
    # Get customers
    result = await db.execute(
        select(Customer).where(Customer.is_active == True).limit(5)
    )
    customers = list(result.scalars().all())
    
    return {
        "admin": admin,
        "teller": teller or admin,
        "branches": branches,
        "currencies": currencies,
        "customers": customers
    }


async def create_income_transactions(
    db: AsyncSession,
    service: TransactionService,
    data: dict
) -> int:
    """Create sample income transactions"""
    
    print("💰 Creating income transactions...")
    
    branches = data["branches"]
    currencies = data["currencies"]
    customers = data["customers"]
    user = data["teller"]
    
    income_scenarios = [
        {
            "amount": Decimal("150.50"),
            "currency": "USD",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "International money transfer service fee",
            "reference": "SVC-001",
        },
        {
            "amount": Decimal("75.00"),
            "currency": "EUR",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "Currency exchange service fee",
            "reference": "SVC-002",
        },
        {
            "amount": Decimal("250.00"),
            "currency": "USD",
            "category": IncomeCategory.COMMISSION,
            "source": "Monthly commission from partner bank",
            "reference": "COM-001",
        },
        {
            "amount": Decimal("3500.00"),
            "currency": "TRY",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "Bulk transaction processing fee",
            "reference": "SVC-003",
        },
        {
            "amount": Decimal("120.00"),
            "currency": "USD",
            "category": IncomeCategory.OTHER,
            "source": "Document verification fee",
            "reference": "DOC-001",
        },
        # ========== ADDITIONAL INCOME SCENARIOS (DOUBLE DATA) ==========
        {
            "amount": Decimal("200.00"),
            "currency": "USD",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "Account opening fee",
            "reference": "SVC-004",
        },
        {
            "amount": Decimal("180.00"),
            "currency": "EUR",
            "category": IncomeCategory.COMMISSION,
            "source": "Foreign exchange commission",
            "reference": "COM-002",
        },
        {
            "amount": Decimal("95.50"),
            "currency": "USD",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "Wire transfer processing fee",
            "reference": "SVC-005",
        },
        {
            "amount": Decimal("4200.00"),
            "currency": "TRY",
            "category": IncomeCategory.COMMISSION,
            "source": "Monthly agent commission",
            "reference": "COM-003",
        },
        {
            "amount": Decimal("85.00"),
            "currency": "GBP",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "Premium service consultation fee",
            "reference": "SVC-006",
        },
        # ========== ADDITIONAL INCOME WITH EGP ==========
        {
            "amount": Decimal("2500.00"),
            "currency": "EGP",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "Egyptian client money transfer fee",
            "reference": "SVC-007",
        },
        {
            "amount": Decimal("350.00"),
            "currency": "SAR",
            "category": IncomeCategory.COMMISSION,
            "source": "Saudi exchange commission",
            "reference": "COM-004",
        },
        {
            "amount": Decimal("1800.00"),
            "currency": "EGP",
            "category": IncomeCategory.SERVICE_FEE,
            "source": "Multi-currency account opening fee",
            "reference": "SVC-008",
        },
    ]
    
    created = 0
    for scenario in income_scenarios:
        try:
            branch = random.choice(branches)
            customer = random.choice(customers) if customers else None
            currency = currencies[scenario["currency"]]
            
            income = await service.create_income(
                branch_id=branch.id,
                amount=scenario["amount"],
                currency_id=currency.id,
                category=scenario["category"],
                user_id=user.id,
                customer_id=customer.id if customer else None,
                reference_number=scenario["reference"],
                notes=f"Sample income - {scenario['source']}"
            )
            
            created += 1
            print(f"  ✅ {income.transaction_number}: {scenario['amount']} {scenario['currency']}")
            print(f"     {scenario['category'].value} - {branch.code}")
            
        except Exception as e:
            print(f"  ⚠️  Failed to create income: {str(e)}")
    
    print()
    return created


async def create_expense_transactions(
    db: AsyncSession,
    service: TransactionService,
    data: dict
) -> int:
    """Create sample expense transactions"""
    
    print("💸 Creating expense transactions...")
    
    branches = data["branches"]
    currencies = data["currencies"]
    admin = data["admin"]
    teller = data["teller"]
    
    expense_scenarios = [
        {
            "amount": Decimal("15000.00"),
            "currency": "TRY",
            "category": ExpenseCategory.RENT,
            "payee": "Building Management Company",
            "reference": "RENT-JAN-2025",
            "requires_approval": True,
        },
        {
            "amount": Decimal("25000.00"),
            "currency": "TRY",
            "category": ExpenseCategory.SALARY,
            "payee": "Staff Salaries - January",
            "reference": "SAL-JAN-2025",
            "requires_approval": True,
        },
        {
            "amount": Decimal("1500.00"),
            "currency": "TRY",
            "category": ExpenseCategory.UTILITIES,
            "payee": "Electricity & Water Provider",
            "reference": "UTIL-JAN-2025",
            "requires_approval": False,
        },
        {
            "amount": Decimal("800.00"),
            "currency": "TRY",
            "category": ExpenseCategory.SUPPLIES,
            "payee": "Office Supplies Store",
            "reference": "SUP-001",
            "requires_approval": False,
        },
        {
            "amount": Decimal("2500.00"),
            "currency": "TRY",
            "category": ExpenseCategory.MAINTENANCE,
            "payee": "IT Support & Maintenance",
            "reference": "MAINT-001",
            "requires_approval": True,
        },
        # ========== ADDITIONAL EXPENSE SCENARIOS (DOUBLE DATA) ==========
        {
            "amount": Decimal("3500.00"),
            "currency": "TRY",
            "category": ExpenseCategory.OTHER,
            "payee": "Security Services Company",
            "reference": "SEC-JAN-2025",
            "requires_approval": True,
        },
        {
            "amount": Decimal("5000.00"),
            "currency": "TRY",
            "category": ExpenseCategory.OTHER,
            "payee": "Marketing & Advertising Agency",
            "reference": "MKT-001",
            "requires_approval": True,
        },
        {
            "amount": Decimal("4500.00"),
            "currency": "TRY",
            "category": ExpenseCategory.OTHER,
            "payee": "Legal & Accounting Firm",
            "reference": "PROF-001",
            "requires_approval": True,
        },
        {
            "amount": Decimal("1200.00"),
            "currency": "TRY",
            "category": ExpenseCategory.UTILITIES,
            "payee": "Internet & Phone Services",
            "reference": "COMM-JAN-2025",
            "requires_approval": False,
        },
        {
            "amount": Decimal("2800.00"),
            "currency": "TRY",
            "category": ExpenseCategory.OTHER,
            "payee": "Staff Training & Development",
            "reference": "TRAIN-001",
            "requires_approval": True,
        },
    ]
    
    created = 0
    for scenario in expense_scenarios:
        try:
            branch = random.choice(branches)
            currency = currencies[scenario["currency"]]
            
            expense = await service.create_expense(
                branch_id=branch.id,
                amount=scenario["amount"],
                currency_id=currency.id,
                category=scenario["category"],
                payee=scenario["payee"],
                user_id=teller.id,
                reference_number=scenario["reference"],
                requires_approval=scenario["requires_approval"],
                notes=f"Sample expense - {scenario['payee']}"
            )
            
            # Approve some expenses
            if scenario["requires_approval"] and random.choice([True, False]):
                await service.approve_expense_transaction(
                    transaction_id=expense.id,
                    approver_id=admin.id,
                    approval_notes="Approved - Sample transaction"
                )
                status = "✓ Approved"
            else:
                status = "⏳ Pending" if scenario["requires_approval"] else "✓ Completed"
            
            created += 1
            print(f"  ✅ {expense.transaction_number}: {scenario['amount']} {scenario['currency']}")
            print(f"     {scenario['category'].value} - {branch.code} - {status}")
            
        except Exception as e:
            print(f"  ⚠️  Failed to create expense: {str(e)}")
    
    print()
    return created


async def create_exchange_transactions(
    db: AsyncSession,
    service: TransactionService,
    data: dict
) -> int:
    """Create sample exchange transactions"""
    
    print("💱 Creating exchange transactions...")
    
    branches = data["branches"]
    currencies = data["currencies"]
    customers = data["customers"]
    user = data["teller"]
    
    if not customers:
        print("  ⚠️  No customers found. Skipping exchanges.")
        print()
        return 0
    
    exchange_scenarios = [
        {
            "from_currency": "USD",
            "to_currency": "TRY",
            "from_amount": Decimal("100.00"),
            "rate": Decimal("32.50"),
            "commission": Decimal("0.015"),
        },
        {
            "from_currency": "EUR",
            "to_currency": "TRY",
            "from_amount": Decimal("200.00"),
            "rate": Decimal("35.20"),
            "commission": Decimal("0.015"),
        },
        {
            "from_currency": "TRY",
            "to_currency": "USD",
            "from_amount": Decimal("10000.00"),
            "rate": Decimal("0.0308"),
            "commission": Decimal("0.02"),
        },
        {
            "from_currency": "USD",
            "to_currency": "EUR",
            "from_amount": Decimal("500.00"),
            "rate": Decimal("0.92"),
            "commission": Decimal("0.01"),
        },
        {
            "from_currency": "GBP",
            "to_currency": "TRY",
            "from_amount": Decimal("150.00"),
            "rate": Decimal("41.50"),
            "commission": Decimal("0.015"),
        },
        # ========== ADDITIONAL EXCHANGE SCENARIOS (DOUBLE DATA) ==========
        {
            "from_currency": "SAR",
            "to_currency": "TRY",
            "from_amount": Decimal("1000.00"),
            "rate": Decimal("8.67"),
            "commission": Decimal("0.015"),
        },
        {
            "from_currency": "AED",
            "to_currency": "EUR",
            "from_amount": Decimal("500.00"),
            "rate": Decimal("0.251"),
            "commission": Decimal("0.01"),
        },
        {
            "from_currency": "JPY",
            "to_currency": "USD",
            "from_amount": Decimal("50000.00"),
            "rate": Decimal("0.0067"),
            "commission": Decimal("0.01"),
        },
        {
            "from_currency": "EUR",
            "to_currency": "GBP",
            "from_amount": Decimal("300.00"),
            "rate": Decimal("0.86"),
            "commission": Decimal("0.01"),
        },
        {
            "from_currency": "TRY",
            "to_currency": "EUR",
            "from_amount": Decimal("8000.00"),
            "rate": Decimal("0.0283"),
            "commission": Decimal("0.02"),
        },
        # ========== ADDITIONAL EXCHANGE WITH EGP ==========
        {
            "from_currency": "EGP",
            "to_currency": "USD",
            "from_amount": Decimal("10000.00"),
            "rate": Decimal("0.0204"),
            "commission": Decimal("0.015"),
        },
        {
            "from_currency": "USD",
            "to_currency": "EGP",
            "from_amount": Decimal("200.00"),
            "rate": Decimal("49.00"),
            "commission": Decimal("0.015"),
        },
        {
            "from_currency": "EGP",
            "to_currency": "TRY",
            "from_amount": Decimal("5000.00"),
            "rate": Decimal("0.663"),
            "commission": Decimal("0.02"),
        },
        {
            "from_currency": "SAR",
            "to_currency": "EGP",
            "from_amount": Decimal("2000.00"),
            "rate": Decimal("13.07"),
            "commission": Decimal("0.015"),
        },
        {
            "from_currency": "EGP",
            "to_currency": "EUR",
            "from_amount": Decimal("8000.00"),
            "rate": Decimal("0.0188"),
            "commission": Decimal("0.015"),
        },
    ]
    
    created = 0
    for scenario in exchange_scenarios:
        try:
            branch = random.choice(branches)
            customer = random.choice(customers)
            from_curr = currencies[scenario["from_currency"]]
            to_curr = currencies[scenario["to_currency"]]
            
            exchange = await service.create_exchange(
                branch_id=branch.id,
                customer_id=customer.id,
                from_currency_id=from_curr.id,
                to_currency_id=to_curr.id,
                from_amount=scenario["from_amount"],
                user_id=user.id,
                notes=f"Sample exchange - {customer.first_name}"
            )

            created += 1
            print(f"  ✅ {exchange.transaction_number}")
            print(f"     {exchange.from_amount} {scenario['from_currency']} → "
                  f"{exchange.to_amount:.2f} {scenario['to_currency']}")
            print(f"     Rate: {exchange.exchange_rate_used}, Commission: {exchange.commission_amount:.2f}")
            print(f"     Customer: {customer.customer_number} - {branch.code}")
            
        except Exception as e:
            print(f"  ⚠️  Failed to create exchange: {str(e)}")
    
    print()
    return created


async def create_transfer_transactions(
    db: AsyncSession,
    service: TransactionService,
    data: dict
) -> int:
    """Create sample transfer transactions"""
    
    print("🔄 Creating transfer transactions...")
    
    branches = data["branches"]
    currencies = data["currencies"]
    admin = data["admin"]
    teller = data["teller"]
    
    if len(branches) < 2:
        print("  ⚠️  Need at least 2 branches for transfers. Skipping.")
        print()
        return 0
    
    transfer_scenarios = [
        {
            "amount": Decimal("10000.00"),
            "currency": "TRY",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "Monthly cash allocation",
        },
        {
            "amount": Decimal("5000.00"),
            "currency": "USD",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "Foreign currency distribution",
        },
        {
            "amount": Decimal("3000.00"),
            "currency": "EUR",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "EUR cash replenishment",
        },
        # ========== ADDITIONAL TRANSFER SCENARIOS (DOUBLE DATA) ==========
        {
            "amount": Decimal("15000.00"),
            "currency": "TRY",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "Weekly branch cash balance adjustment",
        },
        {
            "amount": Decimal("2500.00"),
            "currency": "USD",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "USD reserve replenishment",
        },
        {
            "amount": Decimal("1800.00"),
            "currency": "GBP",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "GBP currency distribution",
        },
        # ========== ADDITIONAL TRANSFERS WITH EGP & OTHER CURRENCIES ==========
        {
            "amount": Decimal("50000.00"),
            "currency": "EGP",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "EGP cash replenishment for Egyptian clients",
        },
        {
            "amount": Decimal("8000.00"),
            "currency": "SAR",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "SAR reserve distribution",
        },
        {
            "amount": Decimal("7500.00"),
            "currency": "AED",
            "transfer_type": TransferType.BRANCH_TO_BRANCH,
            "notes": "AED currency balance adjustment",
        },
    ]
    
    created = 0
    for scenario in transfer_scenarios:
        try:
            # Pick two different branches
            from_branch, to_branch = random.sample(branches, 2)
            currency = currencies[scenario["currency"]]
            
            # Initiate transfer
            transfer = await service.create_transfer(
                from_branch_id=from_branch.id,
                to_branch_id=to_branch.id,
                amount=scenario["amount"],
                currency_id=currency.id,
                transfer_type=scenario["transfer_type"],
                user_id=teller.id,
                reference_number=f"TRF-{created+1:03d}",
                notes=scenario["notes"]
            )
            
            # Complete some transfers
            if random.choice([True, True, False]):  # 66% chance
                await service.receive_transfer(
                    transaction_id=transfer.id,
                    received_by_id=admin.id,
                    receipt_notes="Transfer received and verified"
                )
                status = "✓ Completed"
            else:
                status = "⏳ Pending Receipt"
            
            created += 1
            print(f"  ✅ {transfer.transaction_number}")
            print(f"     {scenario['amount']} {scenario['currency']}")
            print(f"     {from_branch.code} → {to_branch.code} - {status}")
            
        except Exception as e:
            print(f"  ⚠️  Failed to create transfer: {str(e)}")
    
    print()
    return created


async def seed_transactions(db: AsyncSession, force: bool = False):
    """Main seeding function for transactions"""

    print("💳 Seeding transactions...")
    print()

    # Check if transactions already exist
    result = await db.execute(select(func.count(Transaction.id)))
    existing_count = result.scalar_one()

    if existing_count > 0:
        print(f"  ℹ️  {existing_count} transactions already exist, skipping seeding.")
        print(f"     (Use --force flag to add more transactions)")
        return

    # Get required data
    try:
        data = await get_required_data(db)
    except Exception as e:
        print(f"❌ {str(e)}")
        return

    print(f"✓ Found {len(data['branches'])} branches")
    print(f"✓ Found {len(data['currencies'])} currencies")
    print(f"✓ Found {len(data['customers'])} customers")
    print(f"✓ Using users: {data['admin'].username}, {data['teller'].username}")
    print()
    
    # Initialize service
    service = TransactionService(db)
    
    # Create transactions
    income_count = await create_income_transactions(db, service, data)
    expense_count = await create_expense_transactions(db, service, data)
    exchange_count = await create_exchange_transactions(db, service, data)
    transfer_count = await create_transfer_transactions(db, service, data)
    
    print("=" * 60)
    print("✅ Transaction seeding completed!")
    print()
    print("📊 Summary:")
    print(f"   💰 Income transactions: {income_count}")
    print(f"   💸 Expense transactions: {expense_count}")
    print(f"   💱 Exchange transactions: {exchange_count}")
    print(f"   🔄 Transfer transactions: {transfer_count}")
    print(f"   📝 Total: {income_count + expense_count + exchange_count + transfer_count}")
    print()


async def show_transactions():
    """Display transaction summary"""
    print("=" * 60)
    print("Transaction Summary")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as db:
        # Get transaction counts by type
        result = await db.execute(
            select(
                Transaction.transaction_type,
                func.count(Transaction.id).label('count')
            )
            .group_by(Transaction.transaction_type)
        )
        by_type = {row[0].value: row[1] for row in result.all()}
        
        # Get transaction counts by status
        result = await db.execute(
            select(
                Transaction.status,
                func.count(Transaction.id).label('count')
            )
            .group_by(Transaction.status)
        )
        by_status = {row[0].value: row[1] for row in result.all()}
        
        # Get total amount by currency
        result = await db.execute(
            select(
                Currency.code,
                func.sum(Transaction.amount).label('total')
            )
            .join(Currency, Transaction.currency_id == Currency.id)
            .group_by(Currency.code)
        )
        by_currency = {row[0]: float(row[1]) for row in result.all()}
        
        print("By Type:")
        for trans_type, count in by_type.items():
            print(f"  {trans_type.title()}: {count}")
        print()
        
        print("By Status:")
        for status, count in by_status.items():
            print(f"  {status.title()}: {count}")
        print()
        
        print("Total Amounts by Currency:")
        for currency, total in by_currency.items():
            print(f"  {currency}: {total:,.2f}")
        print()
        
        # Get recent transactions
        result = await db.execute(
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )
        recent = result.scalars().all()
        
        print("Recent Transactions (Last 10):")
        print("-" * 60)
        for trans in recent:
            print(f"{trans.transaction_number}: {trans.transaction_type.value}")
            print(f"  Amount: {trans.amount} | Status: {trans.status.value}")
            print(f"  Date: {trans.created_at.strftime('%Y-%m-%d %H:%M')}")
            print()


async def main():
    """Main function"""
    print("\n🌱 Starting transaction data seeding...\n")
    print("=" * 60)
    print("CEMS Transaction Seeding")
    print("=" * 60)
    print()
    
    try:
        async with AsyncSessionLocal() as db:
            await seed_transactions(db)
        
        print("✨ Transaction seeding completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        asyncio.run(show_transactions())
    elif len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("⚠️  Force mode: Will add transactions even if they exist")
        asyncio.run(main())
    else:
        asyncio.run(main())
