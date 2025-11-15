#!/usr/bin/env python3
"""
Seed Transactions Script - 10X VERSION
Creates sample transactions of all types for testing
Run this after seed_customers.py

ENHANCEMENTS:
- 10x data volume (470+ transactions instead of 47)
- Dynamic transaction generation
- Distributed across last 6 months
- Varied statuses and amounts

Transaction Types:
- Income: Service fees and commissions (130 transactions)
- Expense: Rent, salaries, utilities (100 transactions)
- Exchange: Currency conversions with customers (150 transactions)
- Transfer: Between branches (90 transactions)

Usage:
    python scripts/seed_transactions.py          # Seed transactions
    python scripts/seed_transactions.py --show   # Show transactions summary
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


# Configuration for 10x data
INCOME_COUNT = 130      # 10x from 13
EXPENSE_COUNT = 100     # 10x from 10
EXCHANGE_COUNT = 150    # 10x from 15
TRANSFER_COUNT = 90     # 10x from 9
TOTAL_TRANSACTIONS = 470


# Income categories and descriptions
INCOME_SOURCES = [
    ("Exchange Commission", IncomeCategory.EXCHANGE_COMMISSION),
    ("Transfer Fee", IncomeCategory.TRANSFER_FEE),
    ("Service Fee", IncomeCategory.SERVICE_FEE),
    ("Other Income", IncomeCategory.OTHER),
]

# Expense categories and vendors
EXPENSE_DATA = [
    ("Office Rent", ExpenseCategory.RENT, ["Landlord Properties", "City Real Estate", "Commercial Rentals"]),
    ("Employee Salaries", ExpenseCategory.SALARIES, ["Payroll Department", "HR Services"]),
    ("Utilities", ExpenseCategory.UTILITIES, ["Electric Company", "Water Department", "Telecom Provider"]),
    ("Maintenance", ExpenseCategory.MAINTENANCE, ["Facility Services", "Tech Support", "Cleaning Services"]),
    ("Marketing", ExpenseCategory.MARKETING, ["Ad Agency", "Digital Marketing Co", "Media Services"]),
    ("Office Supplies", ExpenseCategory.SUPPLIES, ["Office Depot", "Stationery Plus", "Supply Store"]),
]


def generate_transaction_date(index: int, total: int) -> datetime:
    """Generate transaction date distributed over last 6 months"""
    days_ago = int((index / total) * 180)  # Distribute over 180 days
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_ago)


def generate_income_transaction(index: int, branches, currencies, users) -> dict:
    """Generate income transaction data"""
    random.seed(1000 + index)

    source, category = random.choice(INCOME_SOURCES)
    branch = random.choice(branches)
    currency = random.choice(list(currencies.values()))
    user = random.choice(users)

    # Amount varies by category
    if category == IncomeCategory.EXCHANGE_COMMISSION:
        amount = Decimal(str(random.uniform(5, 50)))
    elif category == IncomeCategory.TRANSFER_FEE:
        amount = Decimal(str(random.uniform(10, 100)))
    else:
        amount = Decimal(str(random.uniform(20, 500)))

    # 95% completed, 5% pending
    status = TransactionStatus.COMPLETED if index % 20 != 0 else TransactionStatus.PENDING

    return {
        "type": "income",
        "branch_id": branch.id,
        "currency_id": currency.id,
        "amount": round(amount, 2),
        "income_category": category,
        "income_source": f"{source} #{1000 + index}",
        "description": f"Income from {source.lower()}",
        "status": status,
        "user_id": user.id,
        "transaction_date": generate_transaction_date(index, INCOME_COUNT)
    }


def generate_expense_transaction(index: int, branches, currencies, users) -> dict:
    """Generate expense transaction data"""
    random.seed(2000 + index)

    description, category, vendors = random.choice(EXPENSE_DATA)
    vendor = random.choice(vendors)
    branch = random.choice(branches)
    currency = random.choice(list(currencies.values()))
    user = random.choice(users)

    # Amount varies by category
    if category == ExpenseCategory.SALARIES:
        amount = Decimal(str(random.uniform(2000, 10000)))
    elif category == ExpenseCategory.RENT:
        amount = Decimal(str(random.uniform(1000, 5000)))
    elif category == ExpenseCategory.UTILITIES:
        amount = Decimal(str(random.uniform(100, 1000)))
    else:
        amount = Decimal(str(random.uniform(50, 2000)))

    # 10% require approval
    approval_required = (index % 10 == 0)

    # 90% completed, 10% pending
    status = TransactionStatus.COMPLETED if index % 10 != 0 else TransactionStatus.PENDING

    # If approved, set approved_by
    approved_by_id = None
    approved_at = None
    if approval_required and status == TransactionStatus.COMPLETED:
        approved_by_id = user.id
        approved_at = generate_transaction_date(index, EXPENSE_COUNT) + timedelta(hours=2)

    return {
        "type": "expense",
        "branch_id": branch.id,
        "currency_id": currency.id,
        "amount": round(amount, 2),
        "expense_category": category,
        "expense_to": vendor,
        "description": f"{description} - {vendor}",
        "approval_required": approval_required,
        "approved_by_id": approved_by_id,
        "approved_at": approved_at,
        "status": status,
        "user_id": user.id,
        "transaction_date": generate_transaction_date(index, EXPENSE_COUNT)
    }


def generate_exchange_transaction(index: int, branches, currencies, customers, users) -> dict:
    """Generate exchange transaction data"""
    random.seed(3000 + index)

    branch = random.choice(branches)
    user = random.choice(users)

    # Get two different currencies
    currency_list = list(currencies.values())
    from_currency = random.choice(currency_list)
    to_currency = random.choice([c for c in currency_list if c.id != from_currency.id])

    # Customer (80% have customer, 20% walk-in)
    customer = random.choice(customers) if customers and index % 5 != 0 else None

    # Amounts
    from_amount = Decimal(str(random.uniform(100, 10000)))

    # Exchange rate (use a realistic rate or 1.0 if same currency somehow)
    # In reality, this would come from exchange_rates table
    exchange_rate = Decimal(str(random.uniform(0.8, 1.5)))
    to_amount = from_amount * exchange_rate

    # Commission (0.5% to 2%)
    commission_percentage = Decimal(str(random.uniform(0.5, 2.0)))
    commission_amount = from_amount * (commission_percentage / 100)

    # 98% completed, 2% pending
    status = TransactionStatus.COMPLETED if index % 50 != 0 else TransactionStatus.PENDING

    return {
        "type": "exchange",
        "branch_id": branch.id,
        "currency_id": from_currency.id,
        "from_currency_id": from_currency.id,
        "to_currency_id": to_currency.id,
        "from_amount": round(from_amount, 2),
        "to_amount": round(to_amount, 2),
        "exchange_rate_used": round(exchange_rate, 4),
        "commission_percentage": round(commission_percentage, 2),
        "commission_amount": round(commission_amount, 2),
        "customer_id": customer.id if customer else None,
        "description": f"Exchange {from_currency.code} to {to_currency.code}",
        "status": status,
        "user_id": user.id,
        "transaction_date": generate_transaction_date(index, EXCHANGE_COUNT)
    }


def generate_transfer_transaction(index: int, branches, currencies, users) -> dict:
    """Generate transfer transaction data"""
    random.seed(4000 + index)

    # Get two different branches
    from_branch = random.choice(branches)
    to_branch = random.choice([b for b in branches if b.id != from_branch.id])

    currency = random.choice(list(currencies.values()))
    user = random.choice(users)

    # Amount
    amount = Decimal(str(random.uniform(500, 50000)))

    # Transfer type distribution
    transfer_types = [
        (TransferType.BRANCH_TO_BRANCH, 0.6),
        (TransferType.VAULT_TO_BRANCH, 0.2),
        (TransferType.BRANCH_TO_VAULT, 0.2),
    ]
    rand = random.random()
    cumulative = 0
    transfer_type = TransferType.BRANCH_TO_BRANCH
    for ttype, probability in transfer_types:
        cumulative += probability
        if rand < cumulative:
            transfer_type = ttype
            break

    # 92% completed, 8% pending
    status_rand = index % 13
    if status_rand == 0:
        status = TransactionStatus.PENDING
    else:
        status = TransactionStatus.COMPLETED

    return {
        "type": "transfer",
        "from_branch_id": from_branch.id,
        "to_branch_id": to_branch.id,
        "currency_id": currency.id,
        "amount": round(amount, 2),
        "transfer_type": transfer_type,
        "description": f"Transfer from {from_branch.name} to {to_branch.name}",
        "status": status,
        "user_id": user.id,
        "transaction_date": generate_transaction_date(index, TRANSFER_COUNT)
    }


async def seed_transactions(db: AsyncSession):
    """Seed all transaction types"""

    print("\n💱 Seeding transactions (10X VERSION)...")
    print(f"   Target: {TOTAL_TRANSACTIONS} transactions")
    print(f"   - Income: {INCOME_COUNT}")
    print(f"   - Expense: {EXPENSE_COUNT}")
    print(f"   - Exchange: {EXCHANGE_COUNT}")
    print(f"   - Transfer: {TRANSFER_COUNT}")
    print()

    # Get required data
    print("📊 Loading required data...")

    # Get users
    result = await db.execute(select(User).where(User.is_active == True))
    users = list(result.scalars().all())
    if not users:
        raise Exception("No users found. Run seed_data.py first.")

    # Get branches
    result = await db.execute(select(Branch).where(Branch.is_active == True))
    branches = list(result.scalars().all())
    if not branches:
        raise Exception("No branches found. Run seed_branches.py first.")
    if len(branches) < 2:
        raise Exception("Need at least 2 branches for transfers.")

    # Get currencies
    result = await db.execute(select(Currency).where(Currency.is_active == True))
    currencies = {c.code: c for c in result.scalars().all()}
    if len(currencies) < 2:
        raise Exception("Need at least 2 currencies for exchanges.")

    # Get customers
    result = await db.execute(select(Customer).where(Customer.is_active == True))
    customers = list(result.scalars().all())

    print(f"✓ Found {len(users)} users, {len(branches)} branches, {len(currencies)} currencies, {len(customers)} customers\n")

    # Track created transactions
    created_count = 0

    # Create income transactions
    print(f"💰 Creating {INCOME_COUNT} income transactions...")
    for i in range(INCOME_COUNT):
        trans_data = generate_income_transaction(i, branches, currencies, users)

        transaction = IncomeTransaction(
            branch_id=trans_data["branch_id"],
            currency_id=trans_data["currency_id"],
            amount=trans_data["amount"],
            income_category=trans_data["income_category"],
            income_source=trans_data["income_source"],
            description=trans_data["description"],
            status=trans_data["status"],
            user_id=trans_data["user_id"],
            transaction_date=trans_data["transaction_date"],
        )
        db.add(transaction)
        created_count += 1

        if created_count % 50 == 0:
            await db.flush()
            print(f"  Created {created_count} transactions...")

    print(f"✓ Created {INCOME_COUNT} income transactions\n")

    # Create expense transactions
    print(f"💸 Creating {EXPENSE_COUNT} expense transactions...")
    for i in range(EXPENSE_COUNT):
        trans_data = generate_expense_transaction(i, branches, currencies, users)

        transaction = ExpenseTransaction(
            branch_id=trans_data["branch_id"],
            currency_id=trans_data["currency_id"],
            amount=trans_data["amount"],
            expense_category=trans_data["expense_category"],
            expense_to=trans_data["expense_to"],
            description=trans_data["description"],
            approval_required=trans_data["approval_required"],
            approved_by_id=trans_data.get("approved_by_id"),
            approved_at=trans_data.get("approved_at"),
            status=trans_data["status"],
            user_id=trans_data["user_id"],
            transaction_date=trans_data["transaction_date"],
        )
        db.add(transaction)
        created_count += 1

        if created_count % 50 == 0:
            await db.flush()
            print(f"  Created {created_count} transactions...")

    print(f"✓ Created {EXPENSE_COUNT} expense transactions\n")

    # Create exchange transactions
    print(f"💱 Creating {EXCHANGE_COUNT} exchange transactions...")
    for i in range(EXCHANGE_COUNT):
        trans_data = generate_exchange_transaction(i, branches, currencies, customers, users)

        transaction = ExchangeTransaction(
            branch_id=trans_data["branch_id"],
            currency_id=trans_data["currency_id"],
            amount=trans_data["from_amount"],
            from_currency_id=trans_data["from_currency_id"],
            to_currency_id=trans_data["to_currency_id"],
            from_amount=trans_data["from_amount"],
            to_amount=trans_data["to_amount"],
            exchange_rate_used=trans_data["exchange_rate_used"],
            commission_percentage=trans_data["commission_percentage"],
            commission_amount=trans_data["commission_amount"],
            customer_id=trans_data.get("customer_id"),
            description=trans_data["description"],
            status=trans_data["status"],
            user_id=trans_data["user_id"],
            transaction_date=trans_data["transaction_date"],
        )
        db.add(transaction)
        created_count += 1

        if created_count % 50 == 0:
            await db.flush()
            print(f"  Created {created_count} transactions...")

    print(f"✓ Created {EXCHANGE_COUNT} exchange transactions\n")

    # Create transfer transactions
    print(f"🔄 Creating {TRANSFER_COUNT} transfer transactions...")
    for i in range(TRANSFER_COUNT):
        trans_data = generate_transfer_transaction(i, branches, currencies, users)

        transaction = TransferTransaction(
            from_branch_id=trans_data["from_branch_id"],
            to_branch_id=trans_data["to_branch_id"],
            currency_id=trans_data["currency_id"],
            amount=trans_data["amount"],
            transfer_type=trans_data["transfer_type"],
            description=trans_data["description"],
            status=trans_data["status"],
            user_id=trans_data["user_id"],
            transaction_date=trans_data["transaction_date"],
        )
        db.add(transaction)
        created_count += 1

        if created_count % 50 == 0:
            await db.flush()
            print(f"  Created {created_count} transactions...")

    print(f"✓ Created {TRANSFER_COUNT} transfer transactions\n")

    # Commit all
    await db.commit()

    print("=" * 60)
    print("✅ Transaction Seeding Complete!")
    print("=" * 60)
    print()
    print("📊 Summary:")
    print(f"   • Total Created: {created_count} transactions")
    print(f"   • Income: {INCOME_COUNT}")
    print(f"   • Expense: {EXPENSE_COUNT}")
    print(f"   • Exchange: {EXCHANGE_COUNT}")
    print(f"   • Transfer: {TRANSFER_COUNT}")
    print()


async def show_transactions():
    """Display transaction summary"""
    print("=" * 60)
    print("Transaction Summary")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as db:
        # Count by type
        result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.transaction_type == TransactionType.INCOME)
        )
        income_count = result.scalar()

        result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.transaction_type == TransactionType.EXPENSE)
        )
        expense_count = result.scalar()

        result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.transaction_type == TransactionType.EXCHANGE)
        )
        exchange_count = result.scalar()

        result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.transaction_type == TransactionType.TRANSFER)
        )
        transfer_count = result.scalar()

        total = income_count + expense_count + exchange_count + transfer_count

        print(f"Total Transactions: {total}\n")
        print(f"  💰 Income: {income_count}")
        print(f"  💸 Expense: {expense_count}")
        print(f"  💱 Exchange: {exchange_count}")
        print(f"  🔄 Transfer: {transfer_count}")
        print()


async def main():
    """Main seeding function"""
    print("\n🌱 Starting transaction data seeding (10X VERSION)...\n")
    print("=" * 60)
    print("CEMS Transaction Seeding - 10X Data Volume")
    print("=" * 60)

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
    else:
        asyncio.run(main())
