#!/usr/bin/env python3
"""
Seed Customers Script
Creates sample customers with documents and notes
Run this after seed_branches.py

Usage:
    python scripts/seed_customers.py          # Seed customers
    python scripts/seed_customers.py --show   # Show existing customers
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
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


# Sample customer data
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
        "customer_type": "individual",
        "is_verified": True,
        "risk_level": "low",
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
        "customer_type": "individual",
        "is_verified": True,
        "risk_level": "low",
        "documents": [
            {
                "document_type": DocumentType.NATIONAL_ID,
                "document_number": "23456789012",
                "issue_date": date(2019, 6, 15),
                "expiry_date": date(2029, 6, 15),
                "is_verified": True,
            },
            {
                "document_type": DocumentType.UTILITY_BILL,
                "issue_date": date(2024, 12, 1),
                "is_verified": True,
            }
        ],
        "notes": []
    },
    {
        "first_name": "Mohammed",
        "last_name": "Al-Farsi",
        "name_ar": "محمد الفارسي",
        "passport_number": "A12345678",
        "phone_number": "+966501234567",
        "email": "m.alfarsi@example.com",
        "date_of_birth": date(1988, 11, 10),
        "nationality": "Saudi Arabian",
        "address": "Riyadh, Al Malaz District",
        "city": "Riyadh",
        "country": "Saudi Arabia",
        "customer_type": "individual",
        "is_verified": True,
        "risk_level": "medium",
        "documents": [
            {
                "document_type": DocumentType.PASSPORT,
                "document_number": "A12345678",
                "issue_date": date(2020, 5, 10),
                "expiry_date": date(2025, 5, 10),
                "is_verified": True,
            }
        ],
        "notes": [
            {
                "note_text": "International customer - medium risk due to large transfers",
                "is_alert": True
            }
        ]
    },
    {
        "first_name": "Sarah",
        "last_name": "Johnson",
        "name_ar": "سارة جونسون",
        "passport_number": "P87654321",
        "phone_number": "+447890123456",
        "email": "sarah.johnson@example.com",
        "date_of_birth": date(1992, 4, 18),
        "nationality": "British",
        "address": "London, Baker Street 221B",
        "city": "London",
        "country": "United Kingdom",
        "customer_type": "individual",
        "is_verified": False,
        "risk_level": None,
        "documents": [
            {
                "document_type": DocumentType.PASSPORT,
                "document_number": "P87654321",
                "issue_date": date(2022, 3, 1),
                "expiry_date": date(2032, 3, 1),
                "is_verified": False,
            }
        ],
        "notes": [
            {
                "note_text": "New customer - pending KYC verification",
                "is_alert": True
            }
        ]
    },
    {
        "first_name": "Global Trading",
        "last_name": "Company Ltd",
        "name_ar": "شركة التجارة العالمية المحدودة",
        "national_id": "34567890123",
        "phone_number": "+905551111222",
        "email": "info@globaltrading.com",
        "date_of_birth": date(2010, 1, 1),  # Company registration date
        "nationality": "Turkish",
        "address": "Ankara, Kızılay Business Center",
        "city": "Ankara",
        "country": "Turkey",
        "customer_type": "corporate",
        "is_verified": True,
        "risk_level": "medium",
        "documents": [
            {
                "document_type": DocumentType.COMMERCIAL_REGISTRATION,
                "document_number": "TR-12345-2010",
                "issue_date": date(2010, 1, 1),
                "is_verified": True,
            },
            {
                "document_type": DocumentType.TAX_CERTIFICATE,
                "document_number": "TAX-98765",
                "issue_date": date(2024, 1, 1),
                "expiry_date": date(2024, 12, 31),
                "is_verified": True,
            }
        ],
        "notes": [
            {
                "note_text": "Corporate customer - requires manager approval for large transactions",
                "is_alert": True
            }
        ]
    },
    {
        "first_name": "Ali",
        "last_name": "Kaya",
        "name_ar": "علي كايا",
        "national_id": "45678901234",
        "phone_number": "+905552223344",
        "email": "ali.kaya@example.com",
        "date_of_birth": date(1995, 9, 5),
        "nationality": "Turkish",
        "address": "Izmir, Alsancak",
        "city": "Izmir",
        "country": "Turkey",
        "customer_type": "individual",
        "is_verified": False,
        "risk_level": None,
        "documents": [
            {
                "document_type": DocumentType.NATIONAL_ID,
                "document_number": "45678901234",
                "issue_date": date(2021, 9, 5),
                "expiry_date": date(2031, 9, 5),
                "is_verified": False,
            }
        ],
        "notes": []
    },
    {
        "first_name": "Layla",
        "last_name": "Hassan",
        "name_ar": "ليلى حسان",
        "passport_number": "E55555555",
        "phone_number": "+971501234567",
        "email": "layla.hassan@example.com",
        "date_of_birth": date(1987, 12, 25),
        "nationality": "Emirati",
        "address": "Dubai, Business Bay",
        "city": "Dubai",
        "country": "UAE",
        "customer_type": "individual",
        "is_verified": True,
        "risk_level": "low",
        "documents": [
            {
                "document_type": DocumentType.PASSPORT,
                "document_number": "E55555555",
                "issue_date": date(2021, 1, 10),
                "expiry_date": date(2026, 1, 10),
                "is_verified": True,
            },
            {
                "document_type": DocumentType.BANK_STATEMENT,
                "issue_date": date(2024, 11, 1),
                "is_verified": True,
            }
        ],
        "notes": []
    },
    {
        "first_name": "Omar",
        "last_name": "Özkan",
        "name_ar": "عمر أوزكان",
        "national_id": "56789012345",
        "phone_number": "+905553334455",
        "date_of_birth": date(1993, 6, 30),
        "nationality": "Turkish",
        "address": "Antalya, Lara Beach",
        "city": "Antalya",
        "country": "Turkey",
        "customer_type": "individual",
        "is_verified": False,
        "risk_level": None,
        "documents": [],
        "notes": [
            {
                "note_text": "Walk-in customer - needs to upload documents",
                "is_alert": True
            }
        ]
    },
]


async def get_admin_user(db: AsyncSession) -> User:
    """Get admin user for customer registration"""
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        print("❌ Admin user not found. Please run seed_data.py first.")
        raise Exception("Admin user required for seeding customers")
    
    return admin_user


async def get_branches(db: AsyncSession) -> list[Branch]:
    """Get all branches"""
    result = await db.execute(
        select(Branch).where(Branch.is_active == True)
    )
    branches = result.scalars().all()
    
    if not branches:
        print("❌ No branches found. Please run seed_branches.py first.")
        raise Exception("Branches required for seeding customers")
    
    return list(branches)


async def seed_customers(db: AsyncSession):
    """Seed customers with documents and notes"""
    
    print("👥 Seeding customers...")
    
    # Get admin user and branches
    admin_user = await get_admin_user(db)
    branches = await get_branches(db)
    
    print(f"✓ Using admin user: {admin_user.username}")
    print(f"✓ Found {len(branches)} branches\n")
    
    # Check if customers already exist
    result = await db.execute(
        select(func.count(Customer.id))
    )
    existing_count = result.scalar_one()
    
    if existing_count > 0:
        print(f"⚠️  {existing_count} customers already exist. Skipping...")
        return
    
    # Create customers
    customers_created = 0
    documents_created = 0
    notes_created = 0
    
    for customer_data in SAMPLE_CUSTOMERS:
        # Extract nested data
        documents_data = customer_data.pop("documents", [])
        notes_data = customer_data.pop("notes", [])
        
        # Assign random branch
        branch = random.choice(branches)
        
        # Create customer
        customer = Customer(
            **customer_data,
            branch_id=branch.id,
            registered_by_id=admin_user.id,
            verified_by_id=admin_user.id if customer_data.get("is_verified") else None,
            verified_at=datetime.utcnow() if customer_data.get("is_verified") else None,
        )
        db.add(customer)
        await db.flush()  # Get customer ID
        
        customers_created += 1
        print(f"✅ Created customer: {customer.customer_number} - {customer.first_name} {customer.last_name}")
        print(f"   📍 Branch: {branch.code}")
        print(f"   📞 Phone: {customer.phone_number}")
        print(f"   {'✓ Verified' if customer.is_verified else '⚠ Not verified'}")
        
        # Create documents
        if documents_data:
            for doc_data in documents_data:
                document = CustomerDocument(
                    customer_id=customer.id,
                    document_url=f"/storage/customers/{customer.customer_number}/{doc_data['document_type'].value}.pdf",
                    uploaded_by_id=admin_user.id,
                    verified_by_id=admin_user.id if doc_data.get("is_verified") else None,
                    verified_at=datetime.utcnow() if doc_data.get("is_verified") else None,
                    **doc_data
                )
                db.add(document)
                documents_created += 1
                print(f"   📄 Document: {doc_data['document_type'].value}")
        
        # Create notes
        if notes_data:
            for note_data in notes_data:
                note = CustomerNote(
                    customer_id=customer.id,
                    created_by_id=admin_user.id,
                    **note_data
                )
                db.add(note)
                notes_created += 1
                alert_marker = "🚨" if note_data.get("is_alert") else "📝"
                print(f"   {alert_marker} Note: {note_data['note_text'][:50]}...")
        
        print()
    
    await db.commit()
    
    print("=" * 60)
    print("✅ Customer seeding completed successfully!")
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