"""
Seed Customers Script
Creates sample customers with documents and notes.
Run this *after* database migrations and user/branch seeding.

Usage:
  python scripts/seed_customers.py        # seed data
  python scripts/seed_customers.py --show # list customers
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# ---- Project imports (adjust paths if your app layout differs) ----
from app.db.base import AsyncSessionLocal
from app.db.models.customer import (
    Customer,
    CustomerDocument,
    CustomerNote,
    CustomerType,
    RiskLevel,
    DocumentType,
)
from app.db.models.user import User
from app.db.models.branch import Branch


# ---- Sample data --------------------------------------------------

SAMPLE_CUSTOMERS = [
    {
        "first_name": "Ahmed",
        "last_name": "Al-Hassan",
        "name_ar": "أحمد الحسن",
        "national_id": "1234567890",
        "phone_number": "+966501234567",
        "email": "ahmed.hassan@example.com",
        "date_of_birth": date(1985, 3, 15),
        "nationality": "Saudi",
        "address": "King Fahd Road, Al Olaya District",
        "city": "Riyadh",
        "country": "Saudi Arabia",
        "customer_type": CustomerType.INDIVIDUAL,
        "risk_level": RiskLevel.LOW,
        "registered_days_ago": 30,
        "is_active": True,
        "is_verified": True,
        "verified_days_ago": 25,
        "documents": [
            {
                "type": DocumentType.NATIONAL_ID,
                "number": "1234567890",
                "url": "/documents/customers/ahmed_hassan/national_id.pdf",
                "issue_date": date(2020, 1, 1),
                "expiry_date": date(2030, 1, 1),
                "verified": True,
                "notes": "National ID verified and valid",
            },
            {
                "type": DocumentType.UTILITY_BILL,
                "url": "/documents/customers/ahmed_hassan/utility_bill.pdf",
                "issue_date": date(2024, 12, 1),
                "expiry_date": date(2025, 12, 1),
                "verified": True,
                "notes": "Address verified through utility bill",
            },
        ],
        "notes": [
            {
                "text": "VIP customer, frequent large transactions. KYC up to date.",
                "is_alert": False,
                "days_ago": 10,
            }
        ],
    },
    {
        "first_name": "Mohammed",
        "last_name": "Ali",
        "name_ar": "محمد علي",
        "passport_number": "E87654321",
        "phone_number": "+966511112222",
        "email": "m.ali@example.com",
        "date_of_birth": date(1990, 7, 20),
        "nationality": "Egyptian",
        "address": "Al Faisaliah Tower",
        "city": "Riyadh",
        "country": "Saudi Arabia",
        "customer_type": CustomerType.INDIVIDUAL,
        "risk_level": RiskLevel.MEDIUM,
        "registered_days_ago": 60,
        "is_active": True,
        "is_verified": False,
        "documents": [
            {
                "type": DocumentType.PASSPORT,
                "number": "E87654321",
                "url": "/documents/customers/mohammed_ali/passport.pdf",
                "issue_date": date(2020, 3, 15),
                "expiry_date": date(2030, 3, 15),
                "verified": True,
            }
        ],
        "notes": [
            {
                "text": "Regular customer, mostly small transactions.",
                "is_alert": False,
                "days_ago": 15,
            }
        ],
    },
    {
        "first_name": "Al Noor Trading",
        "last_name": "",
        "name_ar": "النور للتجارة",
        "phone_number": "+966533334444",
        "email": "ops@alnoortrading.example.com",
        "nationality": "Saudi",
        "address": "Industrial Area, Warehouse 12",
        "city": "Jeddah",
        "country": "Saudi Arabia",
        "customer_type": CustomerType.CORPORATE,
        "risk_level": RiskLevel.HIGH,
        "registered_days_ago": 120,
        "is_active": True,
        "is_verified": False,
        "documents": [
            {
                "type": DocumentType.COMMERCIAL_REGISTRATION,
                "number": "CR-4455667788",
                "url": "/documents/customers/al_noor/cr.pdf",
                "issue_date": date(2022, 5, 10),
                "expiry_date": date(2026, 5, 10),
                "verified": False,
                "notes": "Pending verification of commercial registration",
            }
        ],
        "notes": [
            {
                "text": "Flagged for enhanced due diligence due to industry risk.",
                "is_alert": True,
                "days_ago": 3,
            }
        ],
    },
    {
        "first_name": "Fatima",
        "last_name": "Alshehri",
        "name_ar": "فاطمة الشهري",
        "national_id": "2233445566",
        "phone_number": "+966544445555",
        "email": "fatima.alshehri@example.com",
        "date_of_birth": date(1995, 11, 5),
        "nationality": "Saudi",
        "address": "King Abdulaziz Road",
        "city": "Dammam",
        "country": "Saudi Arabia",
        "customer_type": CustomerType.INDIVIDUAL,
        "risk_level": RiskLevel.LOW,
        "registered_days_ago": 180,
        "is_active": False,
        "is_verified": False,
    },
]


# ---- Helpers ------------------------------------------------------

@dataclass
class SeedStats:
    customers: int = 0
    documents: int = 0
    notes: int = 0


def _ago(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


async def get_admin_user(db: AsyncSession) -> User:
    """Get admin user for customer registration."""
    result = await db.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        print("❌ Admin user not found. Please run seed users first.")
        raise RuntimeError("Admin user not found")

    return admin_user


async def get_first_branch(db: AsyncSession) -> Branch:
    """Get a default branch to associate with the customers."""
    result = await db.execute(select(Branch).order_by(Branch.id.asc()).limit(1))
    first_branch = result.scalar_one_or_none()

    if not first_branch:
        print("❌ No branches found. Please run seed branches first.")
        raise RuntimeError("Branch required for seeding customers")

    return first_branch


async def _get_existing_customer(
    db: AsyncSession,
    national_id: Optional[str],
    passport_number: Optional[str],
) -> Optional[Customer]:
    stmt = select(Customer)
    if national_id and passport_number:
        stmt = stmt.where(
            (Customer.national_id == national_id)
            | (Customer.passport_number == passport_number)
        )
    elif national_id:
        stmt = stmt.where(Customer.national_id == national_id)
    elif passport_number:
        stmt = stmt.where(Customer.passport_number == passport_number)
    else:
        return None

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_customers(db: AsyncSession, admin_user: User, branch: Branch) -> SeedStats:
    """Create sample customers with documents and notes (idempotent)."""
    print("Creating sample customers...")

    stats = SeedStats()

    # Single transaction for all inserts
    #async with db.begin():
    async def create_customers(
        db: AsyncSession,
        admin_user: User,
        branch: Branch
    ) -> int:
        """Create sample customers with documents and notes"""
        print("Creating sample customers...")
        
        customers_created = 0
        for raw in SAMPLE_CUSTOMERS:
            national_id = raw.get("national_id")
            passport_number = raw.get("passport_number")

            existing = await _get_existing_customer(db, national_id, passport_number)

            if existing:
                customer = existing
                # Optional: update a few mutable fields to keep data fresh
                customer.phone_number = raw.get("phone_number", customer.phone_number)
                customer.email = raw.get("email", customer.email)
                customer.address = raw.get("address", customer.address)
                customer.city = raw.get("city", customer.city)
                customer.country = raw.get("country", customer.country)
                customer.is_active = raw.get("is_active", customer.is_active)
                customer.is_verified = raw.get("is_verified", customer.is_verified)
            else:
                customer = Customer(
                    id=None,  # let DB default/UUID generate if mapped so
                    first_name=raw.get("first_name"),
                    last_name=raw.get("last_name"),
                    name_ar=raw.get("name_ar"),
                    national_id=national_id,
                    passport_number=passport_number,
                    phone_number=raw.get("phone_number"),
                    email=raw.get("email"),
                    date_of_birth=raw.get("date_of_birth"),
                    nationality=raw.get("nationality"),
                    address=raw.get("address"),
                    city=raw.get("city"),
                    country=raw.get("country"),
                    customer_type=raw.get("customer_type"),
                    risk_level=raw.get("risk_level"),
                    is_active=raw.get("is_active", True),
                    is_verified=raw.get("is_verified", False),
                    created_at=_ago(raw.get("registered_days_ago", 0))
                    if raw.get("registered_days_ago") is not None
                    else func.now(),
                    verified_at=(
                        _ago(raw["verified_days_ago"])
                        if raw.get("is_verified") and raw.get("verified_days_ago") is not None
                        else None
                    ),
                    created_by_id=admin_user.id,
                    branch_id=branch.id,
                )
                db.add(customer)
                stats.customers += 1

            # Documents (idempotent on (type, number/url))
            for d in raw.get("documents", []):
                # Try to find existing document by unique-ish natural key
                doc_key_clause = [CustomerDocument.customer_id == customer.id, CustomerDocument.type == d["type"]]
                if d.get("number"):
                    doc_key_clause.append(CustomerDocument.number == d["number"])
                elif d.get("url"):
                    doc_key_clause.append(CustomerDocument.url == d["url"])

                existing_doc = (
                    await db.execute(select(CustomerDocument).where(*doc_key_clause).limit(1))
                ).scalar_one_or_none()

                if existing_doc:
                    # Minimal updates to keep fresh
                    existing_doc.issue_date = d.get("issue_date", existing_doc.issue_date)
                    existing_doc.expiry_date = d.get("expiry_date", existing_doc.expiry_date)
                    existing_doc.verified = d.get("verified", existing_doc.verified)
                    if d.get("notes"):
                        existing_doc.notes = d["notes"]
                else:
                    doc = CustomerDocument(
                        customer_id=customer.id,
                        type=d["type"],
                        number=d.get("number"),
                        url=d.get("url"),
                        issue_date=d.get("issue_date"),
                        expiry_date=d.get("expiry_date"),
                        verified=d.get("verified", False),
                        notes=d.get("notes"),
                    )
                    db.add(doc)
                    stats.documents += 1

            # Notes (idempotent: avoid exact duplicates by text+is_alert)
            for n in raw.get("notes", []):
                text = n["text"].strip()
                is_alert = bool(n.get("is_alert", False))

                existing_note = (
                    await db.execute(
                        select(CustomerNote)
                        .where(
                            CustomerNote.customer_id == customer.id,
                            CustomerNote.text == text,
                            CustomerNote.is_alert == is_alert,
                        )
                        .limit(1)
                    )
                ).scalar_one_or_none()

                if existing_note:
                    # Refresh created_at optionally to relative recency if requested
                    if n.get("days_ago") is not None:
                        existing_note.created_at = _ago(int(n["days_ago"]))
                else:
                    note = CustomerNote(
                        customer_id=customer.id,
                        text=text,
                        is_alert=is_alert,
                        created_at=_ago(int(n["days_ago"])) if n.get("days_ago") is not None else func.now(),
                    )
                    db.add(note)
                    stats.notes += 1

    print(
        f"✓ Successfully processed customers. "
        f"Created/updated: {stats.customers} customers, {stats.documents} documents, {stats.notes} notes\n"
    )
    return stats


async def seed_customers() -> None:
    """Main seeding function."""
    print("=" * 60)
    print("CEMS Customer Seeding")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as db:
        try:
            # Lookups
            admin_user = await get_admin_user(db)
            print(f"✓ Using admin user: {admin_user.username}\n")

            branch = await get_first_branch(db)
            #print(f"✓ Using branch: {branch.name}\n")
            print(f"✓ Using branch: {branch.name_en}\n")

            # Seed
            await create_customers(db, admin_user, branch)

            print("=" * 60)
            print("✓ Customer seeding completed successfully!")
            print("=" * 60)
        except IntegrityError as ie:
            await db.rollback()
            print("❌ IntegrityError during seeding:", ie.orig if hasattr(ie, "orig") else ie)
            raise
        except Exception as exc:
            await db.rollback()
            print("❌ Error during seeding:", exc)
            raise


async def show_customers() -> None:
    """Quick listing helper."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                Customer.id,
                Customer.first_name,
                Customer.last_name,
                Customer.email,
                Customer.is_active,
                Customer.is_verified,
            ).order_by(Customer.created_at.desc())
        )
        rows = result.all()
        if not rows:
            print("No customers found.")
            return

        print(f"Found {len(rows)} customers:")
        for r in rows:
            print(
                f"- {r.id} | {r.first_name} {r.last_name} | {r.email or '-'} "
                f"| active={r.is_active} | verified={r.is_verified}"
            )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        asyncio.run(show_customers())
    else:
        asyncio.run(seed_customers())
