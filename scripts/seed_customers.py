#!/usr/bin/env python3
"""
Seed Customers Script - FIXED VERSION
Creates sample customers with documents and notes
Run this after seed_branches.py

FIXES:
- Changed enum values to lowercase ('individual' not 'INDIVIDUAL')
- Changed risk_level to lowercase ('low' not 'LOW')
- Fixed datetime.now(datetime.UTC).replace(tzinfo=None) deprecation warning

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


# Sample customer data - FIXED ENUM VALUES
SAMPLE_CUSTOMERS = [
    {
        "first_name": "Ahmed",
        "last_name": "Yılmaz",
        "name_ar": "أحمد يلماز",
        "national_id": "12345678901",
        "phone_number": "+905551234567",
        "email": "ahmed.yilmaz@example.com",
        "date_of_birth": date(1985, 3, 15),
        "nationality": "Turkish",
        "address": "Taksim, Beyoğlu",
        "city": "Istanbul",
        "country": "Turkey",
        "customer_type": "individual",  # ✅ lowercase
        "is_verified": True,
        "risk_level": "low",  # ✅ lowercase
        "documents": [
            {
                "document_type": DocumentType.NATIONAL_ID,
                "document_number": "12345678901",
                "issue_date": date(2020, 1, 1),
                "expiry_date": date(2030, 1, 1),
                "is_verified": True,
            }
        ],
        "notes": [
            {
                "note_text": "Regular customer, high transaction volume",
                "is_alert": False
            }
        ]
    },
    {
        "first_name": "Fatma",
        "last_name": "Demir",
        "name_ar": "فاطمة دمير",
        "national_id": "23456789012",
        "phone_number": "+905559876543",
        "email": "fatma.demir@example.com",
        "date_of_birth": date(1990, 7, 22),
        "nationality": "Turkish",
        "address": "Kadıköy, Moda Street 45",
        "city": "Istanbul",
        "country": "Turkey",
        "customer_type": "individual",  # ✅ lowercase
        "is_verified": True,
        "risk_level": "low",  # ✅ lowercase
        "documents": [
            {
                "document_type": DocumentType.NATIONAL_ID,
                "document_number": "23456789012",
                "issue_date": date(2019, 6, 15),
                "expiry_date": date(2029, 6, 15),
                "is_verified": True,
            },
            {
                "document_type": DocumentType.PASSPORT,
                "document_number": "TR987654321",
                "issue_date": date(2021, 1, 10),
                "expiry_date": date(2031, 1, 10),
                "is_verified": True,
            }
        ],
        "notes": [
            {
                "note_text": "Preferred customer, frequent traveler",
                "is_alert": False
            }
        ]
    },
    {
        "first_name": "Mehmet",
        "last_name": "Kaya",
        "name_ar": "محمد كايا",
        "passport_number": "TR123456789",
        "phone_number": "+905557654321",
        "email": "mehmet.kaya@example.com",
        "date_of_birth": date(1982, 11, 30),
        "nationality": "Turkish",
        "address": "Ankara, Çankaya",
        "city": "Ankara",
        "country": "Turkey",
        "customer_type": "individual",  # ✅ lowercase
        "is_verified": False,
        "risk_level": "medium",  # ✅ lowercase
        "documents": [
            {
                "document_type": DocumentType.PASSPORT,
                "document_number": "TR123456789",
                "issue_date": date(2022, 3, 20),
                "expiry_date": date(2032, 3, 20),
                "is_verified": False,
            }
        ],
        "notes": [
            {
                "note_text": "Pending verification - documents under review",
                "is_alert": True
            }
        ]
    },
    {
        "first_name": "Ayşe",
        "last_name": "Şahin",
        "name_ar": "عائشة شاهين",
        "national_id": "34567890123",
        "phone_number": "+905558765432",
        "email": "ayse.sahin@example.com",
        "date_of_birth": date(1995, 4, 18),
        "nationality": "Turkish",
        "address": "İzmir, Karşıyaka",
        "city": "Izmir",
        "country": "Turkey",
        "customer_type": "individual",  # ✅ lowercase
        "is_verified": True,
        "risk_level": "low",  # ✅ lowercase
        "documents": [
            {
                "document_type": DocumentType.NATIONAL_ID,
                "document_number": "34567890123",
                "issue_date": date(2020, 5, 10),
                "expiry_date": date(2030, 5, 10),
                "is_verified": True,
            },
            {
                "document_type": DocumentType.DRIVING_LICENSE,
                "document_number": "B12345678",
                "issue_date": date(2018, 8, 15),
                "expiry_date": date(2028, 8, 15),
                "is_verified": True,
            }
        ],
        "notes": [
            {
                "note_text": "Young professional, growing account",
                "is_alert": False
            }
        ]
    },
    {
        "first_name": "Global Trade",
        "last_name": "Company",
        "name_ar": "شركة التجارة العالمية",
        "national_id": "4567890123456",
        "phone_number": "+905554567890",
        "email": "info@globaltrade.tr",
        "date_of_birth": date(2010, 1, 1),
        "nationality": "Turkish",
        "address": "Istanbul, Maslak Business Center",
        "city": "Istanbul",
        "country": "Turkey",
        "customer_type": "corporate",  # ✅ lowercase
        "is_verified": True,
        "risk_level": "high",  # ✅ lowercase - corporate = higher risk
        "documents": [
            {
                "document_type": DocumentType.COMMERCIAL_REGISTRATION,
                "document_number": "CR123456789",
                "issue_date": date(2010, 1, 1),
                "is_verified": True,
            },
            {
                "document_type": DocumentType.TAX_CERTIFICATE,
                "document_number": "TAX987654321",
                "issue_date": date(2024, 1, 1),
                "expiry_date": date(2025, 1, 1),
                "is_verified": True,
            }
        ],
        "notes": [
            {
                "note_text": "Large volume transactions - enhanced due diligence",
                "is_alert": True
            },
            {
                "note_text": "Monthly compliance review required",
                "is_alert": True
            }
        ]
    },
    {
        "first_name": "Ali",
        "last_name": "Özkan",
        "name_ar": "علي أوزكان",
        "national_id": "45678901234",
        "phone_number": "+905553456789",
        "date_of_birth": date(1988, 9, 5),
        "nationality": "Turkish",
        "address": "Bursa, Osmangazi",
        "city": "Bursa",
        "country": "Turkey",
        "customer_type": "individual",  # ✅ lowercase
        "is_verified": False,
        "risk_level": "low",  # ✅ lowercase
        "documents": [
            {
                "document_type": DocumentType.NATIONAL_ID,
                "document_number": "45678901234",
                "issue_date": date(2021, 2, 14),
                "expiry_date": date(2031, 2, 14),
                "is_verified": False,
            }
        ],
        "notes": [
            {
                "note_text": "New customer - initial verification pending",
                "is_alert": True
            }
        ]
    }
]


async def seed_customers(db: AsyncSession):
    """Seed customers with their documents and notes"""
    
    print("👥 Seeding customers...")
    
    # Get admin user for created_by
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        raise Exception("Admin user not found. Run seed_users.py first.")
    
    print(f"✓ Using admin user: {admin_user.username}")
    
    # Get active branches
    result = await db.execute(
        select(Branch).where(Branch.is_active == True)
    )
    branches = result.scalars().all()
    
    if not branches:
        raise Exception("No branches found. Run seed_branches.py first.")
    
    print(f"✓ Found {len(branches)} branches\n")
    
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
                print(f"⊘ Customer exists: {existing.first_name} {existing.last_name}")
                continue
        
        # Assign random branch
        branch = random.choice(branches)
        
        # Create customer - FIXED datetime
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
            customer_type=customer_data["customer_type"],  # ✅ already lowercase
            risk_level=customer_data.get("risk_level", "low"),  # ✅ already lowercase
            is_active=True,
            is_verified=customer_data.get("is_verified", False),
            registered_by_id=admin_user.id,
            verified_by_id=admin_user.id if customer_data.get("is_verified") else None,
            branch_id=branch.id,
            registered_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None),
            verified_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) if customer_data.get("is_verified") else None,

        )
        
        db.add(customer)
        await db.flush()  # Get customer ID
        
        customers_created += 1
        print(f"✓ Customer: {customer.first_name} {customer.last_name}")
        
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
                verified_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) if doc_data.get("is_verified") else None,
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
    print(f"   • Customers: {customers_created}")
    print(f"   • Documents: {documents_created}")
    print(f"   • Notes: {notes_created}")
    print(f"   • Verified: {sum(1 for c in SAMPLE_CUSTOMERS if c.get('is_verified'))}")
    print(f"   • Pending: {sum(1 for c in SAMPLE_CUSTOMERS if not c.get('is_verified'))}")
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
        
        print("Customers List:")
        print("-" * 60)
        
        for customer in customers:
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
    print("\n🌱 Starting customer data seeding...\n")
    print("=" * 60)
    print("CEMS Customer Seeding")
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