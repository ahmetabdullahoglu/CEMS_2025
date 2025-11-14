#!/usr/bin/env python3
"""
Seed Customers Script - 10X VERSION
Creates sample customers with documents and notes
Run this after seed_branches.py

ENHANCEMENTS:
- 10x data volume (110+ customers instead of 11)
- Dynamic customer generation based on templates
- Varied customer types, risk levels, and verification statuses

Usage:
    python scripts/seed_customers.py          # Seed customers
    python scripts/seed_customers.py --show   # Show existing customers
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.base import AsyncSessionLocal
from app.db.models.customer import (
    Customer, CustomerDocument, CustomerNote,
    CustomerType, RiskLevel, DocumentType
)
from app.db.models.branch import Branch
from app.db.models.user import User


# Configuration for dynamic customer generation
CUSTOMERS_TO_GENERATE = 110  # 10x the original 11

# Turkish first names (for variety)
FIRST_NAMES = [
    "Ahmed", "Mehmet", "Mustafa", "Ali", "Hasan", "Hüseyin", "İbrahim", "Ahmet",
    "Fatma", "Ayşe", "Zeynep", "Elif", "Merve", "Emine", "Hatice", "Esra",
    "Kemal", "Osman", "Yunus", "Emre", "Burak", "Can", "Cem", "Deniz",
    "Selin", "Defne", "Naz", "Yağmur", "Cemre", "Pelin", "Gizem", "Burcu"
]

LAST_NAMES = [
    "Yılmaz", "Demir", "Kaya", "Çelik", "Şahin", "Arslan", "Yıldız", "Öztürk",
    "Aydın", "Özkan", "Koç", "Aslan", "Türk", "Doğan", "Kurt", "Polat",
    "Erdoğan", "Karaca", "Tekin", "Eren", "Güneş", "Ünal", "Çakır", "Kılıç"
]

CITIES = [
    "Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Adana", "Gaziantep",
    "Konya", "Mersin", "Kayseri", "Eskişehir", "Trabzon", "Samsun", "Denizli"
]

# Corporate name templates
CORPORATE_PREFIXES = [
    "Global", "International", "Turkish", "Anatolian", "Istanbul", "Modern",
    "Prime", "Elite", "Professional", "Advanced", "Superior", "Quality"
]

CORPORATE_SUFFIXES = [
    "Trade", "Solutions", "Services", "Technologies", "Enterprises", "Group",
    "Industries", "Commerce", "International", "Holding", "Corporation", "LLC"
]


def generate_customer_data(index: int) -> dict:
    """Generate dynamic customer data based on index"""
    random.seed(index)  # Consistent random data for same index

    # 85% individual, 15% corporate
    is_corporate = (index % 7 == 0)

    if is_corporate:
        # Corporate customer
        company_name = f"{random.choice(CORPORATE_PREFIXES)} {random.choice(CORPORATE_SUFFIXES)}"
        first_name = company_name.split()[0]
        last_name = company_name.split()[1] if len(company_name.split()) > 1 else "Ltd"
        customer_type = "corporate"
        # Corporates have higher risk
        risk_level = random.choice(["medium", "medium", "high"])
    else:
        # Individual customer
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        customer_type = "individual"
        # Most individuals are low risk
        risk_level = random.choice(["low", "low", "low", "low", "medium", "medium", "high"])

    # Generate IDs
    national_id = str(10000000000 + index * 11111).zfill(11)
    passport_number = f"TR{str(100000000 + index * 12345).zfill(9)}"

    # 80% verified, 20% pending
    is_verified = (index % 5 != 0)

    # Generate dates
    birth_year = 1950 + (index % 50)
    birth_month = 1 + (index % 12)
    birth_day = 1 + (index % 28)
    date_of_birth = date(birth_year, birth_month, birth_day)

    city = CITIES[index % len(CITIES)]

    # Generate email (some customers may not have email)
    email = None
    if index % 3 != 2:  # 66% have email
        email = f"{first_name.lower()}.{last_name.lower()}{index}@example.com"

    # Arabic name
    name_ar = f"عميل {index}"

    customer = {
        "first_name": first_name,
        "last_name": last_name,
        "name_ar": name_ar,
        "national_id": national_id if not is_corporate or index % 2 == 0 else None,
        "passport_number": passport_number if index % 3 == 0 else None,
        "phone_number": f"+9055{str(5000000 + index * 1234).zfill(7)}",
        "email": email,
        "date_of_birth": date_of_birth,
        "nationality": "Turkish",
        "address": f"{city}, District {index % 20 + 1}",
        "city": city,
        "country": "Turkey",
        "customer_type": customer_type,
        "is_verified": is_verified,
        "risk_level": risk_level,
        "documents": [],
        "notes": []
    }

    # Add documents based on customer type
    issue_year = 2015 + (index % 9)

    if is_corporate:
        # Commercial registration (all corporates)
        customer["documents"].append({
            "document_type": DocumentType.COMMERCIAL_REGISTRATION,
            "document_number": f"CR{str(100000000 + index * 7777).zfill(9)}",
            "issue_date": date(issue_year, 1, 1),
            "is_verified": is_verified,
        })

        # Tax certificate (all corporates)
        customer["documents"].append({
            "document_type": DocumentType.TAX_CERTIFICATE,
            "document_number": f"TAX{str(100000000 + index * 8888).zfill(9)}",
            "issue_date": date(2024, 1, 1),
            "expiry_date": date(2025, 1, 1),
            "is_verified": is_verified,
        })

        # Corporate notes
        if risk_level == "high":
            customer["notes"].append({
                "note_text": "High-volume transactions - enhanced due diligence required",
                "is_alert": True
            })
        customer["notes"].append({
            "note_text": f"Corporate client established {issue_year}",
            "is_alert": False
        })
    else:
        # Individual documents

        # National ID (80% have it)
        if index % 5 != 4 and customer["national_id"]:
            customer["documents"].append({
                "document_type": DocumentType.NATIONAL_ID,
                "document_number": customer["national_id"],
                "issue_date": date(issue_year, (index % 12) + 1, 1),
                "expiry_date": date(issue_year + 10, (index % 12) + 1, 1),
                "is_verified": is_verified,
            })

        # Passport (30% have it)
        if index % 3 == 0 and customer["passport_number"]:
            customer["documents"].append({
                "document_type": DocumentType.PASSPORT,
                "document_number": customer["passport_number"],
                "issue_date": date(issue_year + 2, (index % 12) + 1, 1),
                "expiry_date": date(issue_year + 12, (index % 12) + 1, 1),
                "is_verified": is_verified,
            })

        # Driving license (20% have it)
        if index % 5 == 0:
            customer["documents"].append({
                "document_type": DocumentType.DRIVING_LICENSE,
                "document_number": f"DL{str(10000000 + index * 9876).zfill(8)}",
                "issue_date": date(issue_year, 6, 15),
                "expiry_date": date(issue_year + 10, 6, 15),
                "is_verified": is_verified,
            })

        # Individual notes
        if not is_verified:
            customer["notes"].append({
                "note_text": "Pending verification - documents under review",
                "is_alert": True
            })
        elif risk_level == "high":
            customer["notes"].append({
                "note_text": "High-risk customer - requires additional monitoring",
                "is_alert": True
            })
        elif index % 10 == 0:
            customer["notes"].append({
                "note_text": "VIP customer - preferred service level",
                "is_alert": False
            })
        else:
            note_templates = [
                "Regular customer with good transaction history",
                "Occasional transactions, good standing",
                "New customer, building relationship",
                "Frequent small transactions",
                "Seasonal transaction pattern observed"
            ]
            customer["notes"].append({
                "note_text": note_templates[index % len(note_templates)],
                "is_alert": False
            })

    return customer


# Generate all customers dynamically
SAMPLE_CUSTOMERS = [generate_customer_data(i) for i in range(CUSTOMERS_TO_GENERATE)]


async def seed_customers(db: AsyncSession):
    """Seed customers with their documents and notes"""

    print("👥 Seeding customers...")

    # Get admin user for created_by
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        raise Exception("Admin user not found. Run seed_data.py first.")

    print(f"✓ Using admin user: {admin_user.username}")

    # Get active branches
    result = await db.execute(
        select(Branch).where(Branch.is_active == True)
    )
    branches = result.scalars().all()

    if not branches:
        raise Exception("No branches found. Run seed_branches.py first.")

    print(f"✓ Found {len(branches)} branches")
    print(f"✓ Generating {len(SAMPLE_CUSTOMERS)} customers...")
    print()

    # Check existing customers
    result = await db.execute(select(func.count(Customer.id)))
    existing_count = result.scalar()

    # Track created records
    customers_created = 0
    documents_created = 0
    notes_created = 0

    for customer_data in SAMPLE_CUSTOMERS:
        # Skip if customer already exists (by national_id or passport)
        filters = []
        if customer_data.get("national_id"):
            filters.append(Customer.national_id == customer_data["national_id"])
        if customer_data.get("passport_number"):
            filters.append(Customer.passport_number == customer_data["passport_number"])

        if filters:
            from sqlalchemy import or_
            result = await db.execute(
                select(Customer).where(or_(*filters))
            )
            existing = result.scalar_one_or_none()
            if existing:
                continue

        # Assign random branch
        branch = random.choice(branches)

        # Create customer
        customer = Customer(
            first_name=customer_data["first_name"],
            last_name=customer_data["last_name"],
            name_ar=customer_data.get("name_ar"),
            national_id=customer_data.get("national_id"),
            passport_number=customer_data.get("passport_number"),
            phone_number=customer_data["phone_number"],
            email=customer_data.get("email"),
            date_of_birth=customer_data["date_of_birth"],
            nationality=customer_data["nationality"],
            address=customer_data["address"],
            city=customer_data["city"],
            country=customer_data["country"],
            customer_type=customer_data["customer_type"],
            risk_level=customer_data.get("risk_level", "low"),
            is_active=True,
            is_verified=customer_data.get("is_verified", False),
            registered_by_id=admin_user.id,
            verified_by_id=admin_user.id if customer_data.get("is_verified") else None,
            branch_id=branch.id,
            registered_at=datetime.now(timezone.utc).replace(tzinfo=None),
            verified_at=datetime.now(timezone.utc).replace(tzinfo=None) if customer_data.get("is_verified") else None,
        )

        db.add(customer)
        await db.flush()  # Get customer ID

        customers_created += 1
        if customers_created % 10 == 0:
            print(f"  Created {customers_created} customers...")

        # Add documents
        for doc_data in customer_data.get("documents", []):
            document = CustomerDocument(
                customer_id=customer.id,
                document_type=doc_data["document_type"],
                document_number=doc_data.get("document_number"),
                issue_date=doc_data.get("issue_date"),
                expiry_date=doc_data.get("expiry_date"),
                is_verified=doc_data.get("is_verified", False),
                verified_by_id=admin_user.id if doc_data.get("is_verified") else None,
                verified_at=datetime.now(timezone.utc).replace(tzinfo=None) if doc_data.get("is_verified") else None,
                uploaded_by_id=admin_user.id,
            )
            db.add(document)
            documents_created += 1

        # Add notes
        for note_data in customer_data.get("notes", []):
            note = CustomerNote(
                customer_id=customer.id,
                note_text=note_data["note_text"],
                is_alert=note_data.get("is_alert", False),
                created_by_id=admin_user.id,
            )
            db.add(note)
            notes_created += 1

    # Commit all changes
    await db.commit()

    print()
    print("=" * 60)
    print("✅ Customer Seeding Complete!")
    print("=" * 60)
    print()
    print("📊 Summary:")
    print(f"   • Total Generated: {len(SAMPLE_CUSTOMERS)} customers")
    print(f"   • New Customers: {customers_created}")
    print(f"   • Documents: {documents_created}")
    print(f"   • Notes: {notes_created}")
    print(f"   • Verified: {sum(1 for c in SAMPLE_CUSTOMERS if c.get('is_verified'))}")
    print(f"   • Pending: {sum(1 for c in SAMPLE_CUSTOMERS if not c.get('is_verified'))}")
    print(f"   • Corporate: {sum(1 for c in SAMPLE_CUSTOMERS if c.get('customer_type') == 'corporate')}")
    print(f"   • Individual: {sum(1 for c in SAMPLE_CUSTOMERS if c.get('customer_type') == 'individual')}")
    print()


async def show_customers():
    """Display all customers"""
    print("=" * 60)
    print("Current Customers")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as db:
        # Get all customers with branch info
        result = await db.execute(
            select(Customer)
            .where(Customer.is_active == True)
            .order_by(Customer.registered_at.desc())
        )
        customers = result.scalars().all()

        if not customers:
            print("No customers found.")
            return

        print(f"Total Customers: {len(customers)}\n")

        # Group by verification status
        verified = [c for c in customers if c.is_verified]
        pending = [c for c in customers if not c.is_verified]

        print(f"✓ Verified: {len(verified)}")
        print(f"⚠ Pending: {len(pending)}\n")

        print("Customers List (showing first 20):")
        print("-" * 60)

        for i, customer in enumerate(customers[:20]):
            status = "✓ Verified" if customer.is_verified else "⚠ Pending"
            risk = f" - Risk: {customer.risk_level}" if customer.risk_level else ""
            print(f"{customer.customer_number}: {customer.full_name}")
            print(f"  {status}{risk}")
            print(f"  Type: {customer.customer_type.title()}")
            print(f"  Phone: {customer.phone_number}")
            if customer.email:
                print(f"  Email: {customer.email}")
            print()


async def main():
    """Main seeding function"""
    print("\n🌱 Starting customer data seeding (10X VERSION)...\n")
    print("=" * 60)
    print("CEMS Customer Seeding - 10X Data Volume")
    print("=" * 60)
    print()

    try:
        async with AsyncSessionLocal() as db:
            await seed_customers(db)

        print("✨ Customer seeding completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        asyncio.run(show_customers())
    else:
        asyncio.run(main())
