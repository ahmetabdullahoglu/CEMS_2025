#!/usr/bin/env python3
"""
Comprehensive Seed Script for CEMS
Generates realistic data at scale for testing the entire application

Generates:
- 30+ Users (admins, managers, tellers)
- 10 Branches across different regions
- 100+ Customers with documents and notes
- 20 Vaults with balances
- 50+ Vault Transfers
- 500+ Transactions (Exchange, Transfer, Income, Expense)
- Exchange rates with history

Usage:
    python scripts/seed_comprehensive.py
    python scripts/seed_comprehensive.py --small   # Generate less data for quick testing
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import random
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from passlib.context import CryptContext

from app.db.base import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.role import Role
from app.db.models.branch import Branch, BranchBalance, RegionEnum
from app.db.models.currency import Currency, ExchangeRate
from app.db.models.customer import (
    Customer, CustomerDocument, CustomerNote,
    CustomerType, RiskLevel, DocumentType
)
from app.db.models.vault import Vault, VaultTransfer, VaultTransferStatus, TransferType
from app.db.models.transaction import (
    Transaction, IncomeTransaction, ExpenseTransaction,
    ExchangeTransaction, TransferTransaction,
    TransactionType, TransactionStatus,
    IncomeCategory, ExpenseCategory
)

# Initialize Faker for multiple locales
fake = Faker(['en_US', 'tr_TR', 'ar_SA'])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Check for --small flag
SMALL_MODE = "--small" in sys.argv
MULTIPLIER = 0.2 if SMALL_MODE else 1.0

# Data sizes based on mode
USERS_COUNT = int(30 * MULTIPLIER) or 10
CUSTOMERS_COUNT = int(150 * MULTIPLIER) or 30
TRANSACTIONS_PER_CUSTOMER = int(5 * MULTIPLIER) or 2
VAULT_TRANSFERS_COUNT = int(50 * MULTIPLIER) or 15


class DataGenerator:
    """Centralized data generation with caching"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.branches: List[Branch] = []
        self.currencies: List[Currency] = []
        self.users: List[User] = []
        self.customers: List[Customer] = []
        self.vaults: List[Vault] = []
        self.roles: Dict[str, Role] = {}

    async def load_existing_data(self):
        """Load existing data from database"""
        print("📂 Loading existing data...")

        # Load roles
        result = await self.db.execute(select(Role))
        for role in result.scalars().all():
            self.roles[role.name] = role

        # Load currencies
        result = await self.db.execute(select(Currency))
        self.currencies = list(result.scalars().all())

        # Load branches
        result = await self.db.execute(select(Branch))
        self.branches = list(result.scalars().all())

        # Load users
        result = await self.db.execute(select(User))
        self.users = list(result.scalars().all())

        # Load vaults
        result = await self.db.execute(select(Vault))
        self.vaults = list(result.scalars().all())

        print(f"  ✓ Loaded {len(self.roles)} roles")
        print(f"  ✓ Loaded {len(self.currencies)} currencies")
        print(f"  ✓ Loaded {len(self.branches)} branches")
        print(f"  ✓ Loaded {len(self.users)} users")
        print(f"  ✓ Loaded {len(self.vaults)} vaults\n")

    def get_currency(self, code: str = None) -> Currency:
        """Get random or specific currency"""
        if code:
            return next((c for c in self.currencies if c.code == code), None)
        return random.choice(self.currencies)

    def get_branch(self) -> Branch:
        """Get random branch"""
        return random.choice(self.branches)

    def get_user(self, role_name: str = None) -> User:
        """Get random user, optionally filtered by role"""
        if role_name:
            filtered = [u for u in self.users if any(r.name == role_name for r in u.roles)]
            return random.choice(filtered) if filtered else random.choice(self.users)
        return random.choice(self.users)

    def get_vault(self, branch_id=None) -> Vault:
        """Get random vault, optionally from specific branch"""
        if branch_id:
            filtered = [v for v in self.vaults if v.branch_id == branch_id]
            return random.choice(filtered) if filtered else random.choice(self.vaults)
        return random.choice(self.vaults)


async def seed_users(gen: DataGenerator):
    """Create diverse user base"""
    print(f"👥 Creating {USERS_COUNT} users...")

    # Check if users already exist (besides admin)
    result = await gen.db.execute(
        select(func.count(User.id)).where(User.username != "admin")
    )
    existing_count = result.scalar()

    if existing_count > 0:
        print(f"  ⚠️  {existing_count} users already exist. Skipping...")
        return

    user_data = []
    roles_distribution = {
        "admin": 2,  # 2 admins
        "manager": int(10 * MULTIPLIER) or 3,  # 10 managers (or 3 in small mode)
        "teller": USERS_COUNT - 12 if not SMALL_MODE else 5,  # Rest are tellers
    }

    counter = 1
    for role_name, count in roles_distribution.items():
        role = gen.roles.get(role_name)
        if not role:
            continue

        for i in range(count):
            username = f"{role_name}{counter:02d}"
            full_name = fake.name()

            user = User(
                username=username,
                email=f"{username}@cems.com",
                hashed_password=pwd_context.hash("Password@123"),
                full_name=full_name,
                phone_number=fake.phone_number()[:20],
                is_active=True,
                is_superuser=(role_name == "admin"),
            )
            user.roles.append(role)

            # Assign to random branch
            if gen.branches:
                user.branches.append(random.choice(gen.branches))

            user_data.append(user)
            counter += 1

    gen.db.add_all(user_data)
    await gen.db.commit()
    print(f"  ✓ Created {len(user_data)} users")

    # Reload users
    await gen.load_existing_data()


async def seed_customers(gen: DataGenerator):
    """Create realistic customer base with documents and notes"""
    print(f"👤 Creating {CUSTOMERS_COUNT} customers...")

    # Check existing
    result = await gen.db.execute(select(func.count(Customer.id)))
    existing = result.scalar()
    if existing >= CUSTOMERS_COUNT:
        print(f"  ⚠️  {existing} customers already exist. Skipping...")
        return

    nationalities = ["Turkish", "Syrian", "Iraqi", "Egyptian", "Saudi", "Emirati", "Lebanese"]
    cities = ["Istanbul", "Ankara", "Izmir", "Bursa", "Antalya"]

    customers = []
    for i in range(CUSTOMERS_COUNT):
        is_individual = random.random() < 0.85  # 85% individual, 15% corporate
        nationality = random.choice(nationalities)
        branch = gen.get_branch()
        user = gen.get_user()

        if is_individual:
            first_name = fake.first_name()
            last_name = fake.last_name()
            customer_type = CustomerType.INDIVIDUAL
        else:
            first_name = fake.company()
            last_name = ""
            customer_type = CustomerType.CORPORATE

        customer = Customer(
            customer_number=f"CUS{datetime.now().year}{i+1000:05d}",
            first_name=first_name,
            last_name=last_name,
            name_ar=fake.name(),
            national_id=f"{random.randint(10000000000, 99999999999)}" if is_individual else None,
            tax_number=None if is_individual else f"T{random.randint(1000000000, 9999999999)}",
            phone_number=fake.phone_number()[:20],
            email=fake.email(),
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80) if is_individual else None,
            nationality=nationality,
            address=fake.address()[:200],
            city=random.choice(cities),
            country="Turkey",
            postal_code=fake.postcode()[:10],
            customer_type=customer_type,
            risk_level=random.choices(
                [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH],
                weights=[70, 25, 5]
            )[0],
            is_verified=random.random() < 0.9,  # 90% verified
            is_active=True,
            branch_id=branch.id,
            registered_by_id=user.id,
            verified_by_id=user.id if random.random() < 0.9 else None,
            verified_at=datetime.now(timezone.utc).replace(tzinfo=None) if random.random() < 0.9 else None,
            registration_date=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=random.randint(1, 730)),
        )

        customers.append(customer)

        # Add documents (1-3 per customer)
        doc_count = random.randint(1, 3)
        for _ in range(doc_count):
            doc_type = random.choice(list(DocumentType))
            issue_date = fake.date_between(start_date="-5y", end_date="today")
            expiry_date = issue_date + timedelta(days=random.randint(365, 3650))

            doc = CustomerDocument(
                customer=customer,
                document_type=doc_type,
                document_number=f"{doc_type.value.upper()}{random.randint(100000, 999999)}",
                document_url=f"/documents/{customer.customer_number}/{doc_type.value}_{fake.uuid4()}.pdf",
                issue_date=issue_date,
                expiry_date=expiry_date,
                is_verified=random.random() < 0.85,
                verified_by_id=user.id if random.random() < 0.85 else None,
                verified_at=datetime.now(timezone.utc).replace(tzinfo=None) if random.random() < 0.85 else None,
                uploaded_by_id=user.id,
            )
            customer.documents.append(doc)

        # Add notes (0-3 per customer)
        note_count = random.randint(0, 3)
        for _ in range(note_count):
            is_alert = random.random() < 0.1  # 10% alerts
            note = CustomerNote(
                customer=customer,
                note_text=fake.sentence(nb_words=random.randint(5, 20)),
                is_alert=is_alert,
                created_by_id=user.id,
            )
            customer.notes.append(note)

    gen.db.add_all(customers)
    await gen.db.commit()
    print(f"  ✓ Created {len(customers)} customers with documents and notes")

    # Reload customers
    result = await gen.db.execute(select(Customer))
    gen.customers = list(result.scalars().all())


async def seed_vaults(gen: DataGenerator):
    """Create vaults for each branch"""
    print("🏦 Creating vaults...")

    # Check existing
    if gen.vaults:
        print(f"  ⚠️  {len(gen.vaults)} vaults already exist. Skipping...")
        return

    vault_types = ["Main Vault", "Cash Vault", "Foreign Currency Vault", "Reserve Vault"]
    vaults = []

    for branch in gen.branches:
        # Each branch gets 2-3 vaults
        for i, vault_type in enumerate(vault_types[:random.randint(2, 3)]):
            vault = Vault(
                name=f"{branch.name_en} - {vault_type}",
                code=f"{branch.code}-V{i+1:02d}",
                branch_id=branch.id,
                vault_type=vault_type,
                location=f"Floor {random.randint(1, 3)}, Room {random.randint(1, 10)}",
                is_active=True,
                max_capacity=Decimal(random.randint(500000, 2000000)),
            )
            vaults.append(vault)

            # Add balances for each currency
            for currency in gen.currencies[:random.randint(3, 6)]:
                balance = Decimal(random.uniform(10000, 500000)).quantize(Decimal("0.01"))
                vault.balances[currency.code] = balance

    gen.db.add_all(vaults)
    await gen.db.commit()
    print(f"  ✓ Created {len(vaults)} vaults")

    await gen.load_existing_data()


async def seed_vault_transfers(gen: DataGenerator):
    """Create vault transfer history"""
    print(f"💸 Creating {VAULT_TRANSFERS_COUNT} vault transfers...")

    if not gen.vaults or len(gen.vaults) < 2:
        print("  ⚠️  Not enough vaults. Skipping...")
        return

    transfers = []
    for i in range(VAULT_TRANSFERS_COUNT):
        from_vault = random.choice(gen.vaults)
        # Choose different vault
        to_vault = random.choice([v for v in gen.vaults if v.id != from_vault.id])

        currency = gen.get_currency()
        amount = Decimal(random.uniform(1000, 50000)).quantize(Decimal("0.01"))

        transfer_type = random.choice(list(TransferType))
        status = random.choices(
            [VaultTransferStatus.COMPLETED, VaultTransferStatus.IN_TRANSIT, VaultTransferStatus.PENDING, VaultTransferStatus.CANCELLED],
            weights=[70, 15, 10, 5]
        )[0]

        initiated_by = gen.get_user()
        approved_by = gen.get_user("manager") if status != VaultTransferStatus.PENDING else None
        received_by = gen.get_user() if status == VaultTransferStatus.COMPLETED else None

        initiated_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=random.randint(0, 90))
        approved_at = initiated_at + timedelta(hours=random.randint(1, 24)) if approved_by else None
        completed_at = approved_at + timedelta(hours=random.randint(1, 48)) if status == VaultTransferStatus.COMPLETED else None

        transfer = VaultTransfer(
            transfer_number=f"VT{datetime.now().year}{i+1:06d}",
            from_vault_id=from_vault.id,
            to_vault_id=to_vault.id if transfer_type != TransferType.BRANCH_TO_VAULT else None,
            to_branch_id=to_vault.branch_id if transfer_type == TransferType.VAULT_TO_BRANCH else None,
            currency_id=currency.id,
            amount=amount,
            transfer_type=transfer_type,
            status=status,
            initiated_by=initiated_by.id,
            approved_by=approved_by.id if approved_by else None,
            received_by=received_by.id if received_by else None,
            initiated_at=initiated_at,
            approved_at=approved_at,
            completed_at=completed_at,
            notes=fake.sentence() if random.random() < 0.3 else None,
        )
        transfers.append(transfer)

    gen.db.add_all(transfers)
    await gen.db.commit()
    print(f"  ✓ Created {len(transfers)} vault transfers")


async def seed_transactions(gen: DataGenerator):
    """Create realistic transaction history"""
    total_transactions = CUSTOMERS_COUNT * TRANSACTIONS_PER_CUSTOMER
    print(f"💳 Creating {total_transactions} transactions...")

    if not gen.customers:
        print("  ⚠️  No customers found. Skipping...")
        return

    transaction_counter = 1

    for customer in gen.customers[:CUSTOMERS_COUNT]:
        branch = next((b for b in gen.branches if b.id == customer.branch_id), gen.get_branch())
        user = gen.get_user()

        for _ in range(TRANSACTIONS_PER_CUSTOMER):
            trans_type = random.choices(
                [TransactionType.EXCHANGE, TransactionType.TRANSFER, TransactionType.INCOME, TransactionType.EXPENSE],
                weights=[60, 20, 10, 10]
            )[0]

            trans_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=random.randint(0, 180))
            status = random.choices(
                [TransactionStatus.COMPLETED, TransactionStatus.PENDING, TransactionStatus.CANCELLED],
                weights=[85, 10, 5]
            )[0]

            if trans_type == TransactionType.EXCHANGE:
                from_currency = gen.get_currency()
                to_currency = random.choice([c for c in gen.currencies if c.id != from_currency.id])
                from_amount = Decimal(random.uniform(100, 10000)).quantize(Decimal("0.01"))

                # Simple exchange rate calculation
                rate = Decimal(random.uniform(0.5, 2.0)).quantize(Decimal("0.0001"))
                to_amount = (from_amount * rate).quantize(Decimal("0.01"))
                commission_pct = Decimal(random.uniform(0.5, 2.5)).quantize(Decimal("0.01"))
                commission_amt = (from_amount * commission_pct / 100).quantize(Decimal("0.01"))

                trans = ExchangeTransaction(
                    transaction_number=f"TRX-{datetime.now().year}-{transaction_counter:05d}",
                    transaction_type=TransactionType.EXCHANGE,
                    branch_id=branch.id,
                    user_id=user.id,
                    customer_id=customer.id,
                    currency_id=from_currency.id,
                    amount=from_amount,
                    from_currency_id=from_currency.id,
                    to_currency_id=to_currency.id,
                    from_amount=from_amount,
                    to_amount=to_amount,
                    exchange_rate_used=rate,
                    commission_percentage=commission_pct,
                    commission_amount=commission_amt,
                    status=status,
                    transaction_date=trans_date,
                    completed_at=trans_date + timedelta(minutes=5) if status == TransactionStatus.COMPLETED else None,
                    notes=fake.sentence() if random.random() < 0.2 else None,
                )

            elif trans_type == TransactionType.TRANSFER:
                currency = gen.get_currency()
                amount = Decimal(random.uniform(500, 20000)).quantize(Decimal("0.01"))
                from_branch = branch
                to_branch = random.choice([b for b in gen.branches if b.id != from_branch.id])

                trans = TransferTransaction(
                    transaction_number=f"TRX-{datetime.now().year}-{transaction_counter:05d}",
                    transaction_type=TransactionType.TRANSFER,
                    branch_id=from_branch.id,
                    user_id=user.id,
                    customer_id=customer.id,
                    currency_id=currency.id,
                    amount=amount,
                    from_branch_id=from_branch.id,
                    to_branch_id=to_branch.id,
                    transfer_type=TransferType.BRANCH_TO_BRANCH,
                    status=status,
                    transaction_date=trans_date,
                    completed_at=trans_date + timedelta(hours=1) if status == TransactionStatus.COMPLETED else None,
                    notes=f"Transfer from {from_branch.name_en} to {to_branch.name_en}",
                )

            elif trans_type == TransactionType.INCOME:
                currency = gen.get_currency()
                amount = Decimal(random.uniform(100, 5000)).quantize(Decimal("0.01"))
                category = random.choice(list(IncomeCategory))

                trans = IncomeTransaction(
                    transaction_number=f"TRX-{datetime.now().year}-{transaction_counter:05d}",
                    transaction_type=TransactionType.INCOME,
                    branch_id=branch.id,
                    user_id=user.id,
                    customer_id=customer.id,
                    currency_id=currency.id,
                    amount=amount,
                    income_category=category,
                    income_source=fake.company(),
                    status=status,
                    transaction_date=trans_date,
                    completed_at=trans_date if status == TransactionStatus.COMPLETED else None,
                )

            else:  # EXPENSE
                currency = gen.get_currency()
                amount = Decimal(random.uniform(100, 8000)).quantize(Decimal("0.01"))
                category = random.choice(list(ExpenseCategory))
                requires_approval = amount > 5000

                trans = ExpenseTransaction(
                    transaction_number=f"TRX-{datetime.now().year}-{transaction_counter:05d}",
                    transaction_type=TransactionType.EXPENSE,
                    branch_id=branch.id,
                    user_id=user.id,
                    customer_id=customer.id,
                    currency_id=currency.id,
                    amount=amount,
                    expense_category=category,
                    expense_to=fake.company(),
                    approval_required=requires_approval,
                    approved_by_id=gen.get_user("manager").id if requires_approval and status == TransactionStatus.COMPLETED else None,
                    approved_at=trans_date if requires_approval and status == TransactionStatus.COMPLETED else None,
                    status=status,
                    transaction_date=trans_date,
                    completed_at=trans_date if status == TransactionStatus.COMPLETED else None,
                )

            gen.db.add(trans)
            transaction_counter += 1

            # Commit in batches to avoid memory issues
            if transaction_counter % 100 == 0:
                await gen.db.commit()
                print(f"  ... {transaction_counter}/{total_transactions} transactions created")

    await gen.db.commit()
    print(f"  ✓ Created {transaction_counter-1} transactions")


async def main():
    """Main seeding function"""
    print("=" * 70)
    print("🌱 COMPREHENSIVE DATA SEEDING FOR CEMS")
    if SMALL_MODE:
        print("📦 SMALL MODE: Generating reduced dataset for quick testing")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        try:
            gen = DataGenerator(db)
            await gen.load_existing_data()

            # Ensure base data exists
            if not gen.roles:
                print("❌ No roles found. Please run: python scripts/seed_data.py")
                return

            if not gen.currencies:
                print("❌ No currencies found. Please run: python scripts/seed_currencies.py")
                return

            if not gen.branches:
                print("❌ No branches found. Please run: python scripts/seed_branches.py")
                return

            # Seed comprehensive data
            await seed_users(gen)
            await seed_vaults(gen)
            await seed_customers(gen)
            await seed_vault_transfers(gen)
            await seed_transactions(gen)

            print()
            print("=" * 70)
            print("✅ COMPREHENSIVE SEEDING COMPLETED!")
            print("=" * 70)
            print(f"📊 Summary:")
            print(f"  - Users: {len(gen.users)}")
            print(f"  - Branches: {len(gen.branches)}")
            print(f"  - Vaults: {len(gen.vaults)}")
            print(f"  - Customers: {len(gen.customers)}")
            print(f"  - Vault Transfers: ~{VAULT_TRANSFERS_COUNT}")
            print(f"  - Transactions: ~{CUSTOMERS_COUNT * TRANSACTIONS_PER_CUSTOMER}")
            print()
            print("🚀 Your CEMS database is now ready for comprehensive testing!")
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    print()
    asyncio.run(main())
