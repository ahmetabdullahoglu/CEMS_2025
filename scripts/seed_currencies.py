"""
Seed Currencies Script
Creates default currencies and exchange rates
Run this after database migrations
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.db.models.currency import Currency, ExchangeRate
from app.db.models.user import User


# Default currencies to seed
DEFAULT_CURRENCIES = [
    {
        "code": "USD",
        "name_en": "US Dollar",
        "name_ar": "دولار أمريكي",
        "symbol": "$",
        "is_base_currency": True,  # USD as base currency
        "decimal_places": 2,
    },
    {
        "code": "EUR",
        "name_en": "Euro",
        "name_ar": "يورو",
        "symbol": "€",
        "is_base_currency": False,
        "decimal_places": 2,
    },
    {
        "code": "TRY",
        "name_en": "Turkish Lira",
        "name_ar": "ليرة تركية",
        "symbol": "₺",
        "is_base_currency": False,
        "decimal_places": 2,
    },
    {
        "code": "GBP",
        "name_en": "British Pound Sterling",
        "name_ar": "جنيه إسترليني",
        "symbol": "£",
        "is_base_currency": False,
        "decimal_places": 2,
    },
    {
        "code": "SAR",
        "name_en": "Saudi Riyal",
        "name_ar": "ريال سعودي",
        "symbol": "﷼",
        "is_base_currency": False,
        "decimal_places": 2,
    },
    {
        "code": "AED",
        "name_en": "UAE Dirham",
        "name_ar": "درهم إماراتي",
        "symbol": "د.إ",
        "is_base_currency": False,
        "decimal_places": 2,
    },
    {
        "code": "JPY",
        "name_en": "Japanese Yen",
        "name_ar": "ين ياباني",
        "symbol": "¥",
        "is_base_currency": False,
        "decimal_places": 0,  # Yen doesn't use decimal places
    },
]


# Sample exchange rates (USD as base) - EXPANDED WITH MORE PAIRS
SAMPLE_EXCHANGE_RATES = [
    # EUR rates
    {"from": "USD", "to": "EUR", "rate": Decimal("0.92"), "buy_rate": Decimal("0.91"), "sell_rate": Decimal("0.93")},
    {"from": "EUR", "to": "USD", "rate": Decimal("1.087"), "buy_rate": Decimal("1.08"), "sell_rate": Decimal("1.09")},

    # TRY rates
    {"from": "USD", "to": "TRY", "rate": Decimal("32.50"), "buy_rate": Decimal("32.40"), "sell_rate": Decimal("32.60")},
    {"from": "TRY", "to": "USD", "rate": Decimal("0.0308"), "buy_rate": Decimal("0.0307"), "sell_rate": Decimal("0.0309")},

    # GBP rates
    {"from": "USD", "to": "GBP", "rate": Decimal("0.79"), "buy_rate": Decimal("0.78"), "sell_rate": Decimal("0.80")},
    {"from": "GBP", "to": "USD", "rate": Decimal("1.266"), "buy_rate": Decimal("1.25"), "sell_rate": Decimal("1.28")},

    # SAR rates
    {"from": "USD", "to": "SAR", "rate": Decimal("3.75"), "buy_rate": Decimal("3.74"), "sell_rate": Decimal("3.76")},
    {"from": "SAR", "to": "USD", "rate": Decimal("0.267"), "buy_rate": Decimal("0.265"), "sell_rate": Decimal("0.269")},

    # AED rates
    {"from": "USD", "to": "AED", "rate": Decimal("3.67"), "buy_rate": Decimal("3.66"), "sell_rate": Decimal("3.68")},
    {"from": "AED", "to": "USD", "rate": Decimal("0.272"), "buy_rate": Decimal("0.270"), "sell_rate": Decimal("0.274")},

    # JPY rates
    {"from": "USD", "to": "JPY", "rate": Decimal("149.50"), "buy_rate": Decimal("149.00"), "sell_rate": Decimal("150.00")},
    {"from": "JPY", "to": "USD", "rate": Decimal("0.0067"), "buy_rate": Decimal("0.0066"), "sell_rate": Decimal("0.0068")},

    # EUR to other currencies
    {"from": "EUR", "to": "TRY", "rate": Decimal("35.33"), "buy_rate": Decimal("35.20"), "sell_rate": Decimal("35.50")},
    {"from": "TRY", "to": "EUR", "rate": Decimal("0.0283"), "buy_rate": Decimal("0.0282"), "sell_rate": Decimal("0.0284")},
    {"from": "EUR", "to": "GBP", "rate": Decimal("0.86"), "buy_rate": Decimal("0.85"), "sell_rate": Decimal("0.87")},
    {"from": "GBP", "to": "EUR", "rate": Decimal("1.163"), "buy_rate": Decimal("1.15"), "sell_rate": Decimal("1.18")},
    {"from": "EUR", "to": "SAR", "rate": Decimal("4.08"), "buy_rate": Decimal("4.05"), "sell_rate": Decimal("4.10")},
    {"from": "SAR", "to": "EUR", "rate": Decimal("0.245"), "buy_rate": Decimal("0.244"), "sell_rate": Decimal("0.247")},
    {"from": "EUR", "to": "AED", "rate": Decimal("3.99"), "buy_rate": Decimal("3.96"), "sell_rate": Decimal("4.02")},
    {"from": "AED", "to": "EUR", "rate": Decimal("0.251"), "buy_rate": Decimal("0.249"), "sell_rate": Decimal("0.253")},

    # GBP to other currencies - ADDING MISSING RATES
    {"from": "GBP", "to": "TRY", "rate": Decimal("41.14"), "buy_rate": Decimal("41.00"), "sell_rate": Decimal("41.30")},
    {"from": "TRY", "to": "GBP", "rate": Decimal("0.0243"), "buy_rate": Decimal("0.0242"), "sell_rate": Decimal("0.0244")},
    {"from": "GBP", "to": "SAR", "rate": Decimal("4.75"), "buy_rate": Decimal("4.72"), "sell_rate": Decimal("4.78")},
    {"from": "SAR", "to": "GBP", "rate": Decimal("0.211"), "buy_rate": Decimal("0.209"), "sell_rate": Decimal("0.212")},
    {"from": "GBP", "to": "AED", "rate": Decimal("4.65"), "buy_rate": Decimal("4.62"), "sell_rate": Decimal("4.68")},
    {"from": "AED", "to": "GBP", "rate": Decimal("0.215"), "buy_rate": Decimal("0.214"), "sell_rate": Decimal("0.217")},
    {"from": "GBP", "to": "JPY", "rate": Decimal("189.20"), "buy_rate": Decimal("188.00"), "sell_rate": Decimal("190.00")},
    {"from": "JPY", "to": "GBP", "rate": Decimal("0.0053"), "buy_rate": Decimal("0.0053"), "sell_rate": Decimal("0.0053")},

    # TRY to other currencies (additional pairs)
    {"from": "TRY", "to": "SAR", "rate": Decimal("0.115"), "buy_rate": Decimal("0.115"), "sell_rate": Decimal("0.116")},
    {"from": "SAR", "to": "TRY", "rate": Decimal("8.67"), "buy_rate": Decimal("8.62"), "sell_rate": Decimal("8.72")},
    {"from": "TRY", "to": "AED", "rate": Decimal("0.113"), "buy_rate": Decimal("0.112"), "sell_rate": Decimal("0.114")},
    {"from": "AED", "to": "TRY", "rate": Decimal("8.86"), "buy_rate": Decimal("8.77"), "sell_rate": Decimal("8.93")},
    {"from": "TRY", "to": "JPY", "rate": Decimal("4.60"), "buy_rate": Decimal("4.58"), "sell_rate": Decimal("4.62")},
    {"from": "JPY", "to": "TRY", "rate": Decimal("0.217"), "buy_rate": Decimal("0.216"), "sell_rate": Decimal("0.219")},

    # SAR to AED and JPY
    {"from": "SAR", "to": "AED", "rate": Decimal("0.978"), "buy_rate": Decimal("0.975"), "sell_rate": Decimal("0.980")},
    {"from": "AED", "to": "SAR", "rate": Decimal("1.023"), "buy_rate": Decimal("1.020"), "sell_rate": Decimal("1.026")},
    {"from": "SAR", "to": "JPY", "rate": Decimal("39.87"), "buy_rate": Decimal("39.50"), "sell_rate": Decimal("40.00")},
    {"from": "JPY", "to": "SAR", "rate": Decimal("0.025"), "buy_rate": Decimal("0.025"), "sell_rate": Decimal("0.025")},

    # AED to JPY
    {"from": "AED", "to": "JPY", "rate": Decimal("40.74"), "buy_rate": Decimal("40.50"), "sell_rate": Decimal("41.00")},
    {"from": "JPY", "to": "AED", "rate": Decimal("0.025"), "buy_rate": Decimal("0.024"), "sell_rate": Decimal("0.025")},
]


async def create_currencies(db: AsyncSession) -> dict:
    """
    Create default currencies
    Returns dict of currency_code: currency_object
    """
    print("Creating default currencies...")
    currencies_map = {}
    
    for currency_data in DEFAULT_CURRENCIES:
        # Check if currency already exists
        result = await db.execute(
            select(Currency).where(Currency.code == currency_data["code"])
        )
        existing_currency = result.scalar_one_or_none()
        
        if existing_currency:
            print(f"  ✓ Currency '{currency_data['code']}' already exists")
            currencies_map[currency_data["code"]] = existing_currency
        else:
            # Create new currency
            new_currency = Currency(**currency_data)
            db.add(new_currency)
            await db.flush()
            currencies_map[currency_data["code"]] = new_currency
            print(f"  ✓ Created currency '{currency_data['code']}' - {currency_data['name_en']}")
    
    await db.commit()
    print(f"✓ Successfully created {len(currencies_map)} currencies\n")
    return currencies_map


async def create_exchange_rates(
    db: AsyncSession,
    currencies_map: dict,
    admin_user: User
) -> None:
    """Create sample exchange rates"""
    print("Creating sample exchange rates...")
    
    rates_created = 0
    
    for rate_data in SAMPLE_EXCHANGE_RATES:
        from_currency = currencies_map.get(rate_data["from"])
        to_currency = currencies_map.get(rate_data["to"])
        
        if not from_currency or not to_currency:
            print(f"  ⚠ Skipping {rate_data['from']}/{rate_data['to']} - currency not found")
            continue
        
        # Check if exchange rate already exists
        result = await db.execute(
            select(ExchangeRate).where(
                ExchangeRate.from_currency_id == from_currency.id,
                ExchangeRate.to_currency_id == to_currency.id,
                ExchangeRate.effective_to.is_(None)
            )
        )
        existing_rate = result.scalar_one_or_none()
        
        if existing_rate:
            print(f"  ✓ Exchange rate {rate_data['from']}/{rate_data['to']} already exists")
        else:
            # Create new exchange rate
            new_rate = ExchangeRate(
                from_currency_id=from_currency.id,
                to_currency_id=to_currency.id,
                rate=rate_data["rate"],
                buy_rate=rate_data.get("buy_rate"),
                sell_rate=rate_data.get("sell_rate"),
                set_by=admin_user.id,
                effective_from=datetime.utcnow(),
                notes="Initial seed data"
            )
            db.add(new_rate)
            rates_created += 1
            print(f"  ✓ Created exchange rate {rate_data['from']}/{rate_data['to']}: {rate_data['rate']}")
    
    await db.commit()
    print(f"✓ Successfully created {rates_created} exchange rates\n")


async def get_admin_user(db: AsyncSession) -> User:
    """Get admin user for setting exchange rates"""
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        print("❌ Admin user not found. Please run seed_data.py first.")
        raise Exception("Admin user required for seeding currencies")
    
    return admin_user


async def seed_currencies():
    """Main seeding function"""
    print("=" * 60)
    print("CEMS Currency Seeding")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Get admin user
            admin_user = await get_admin_user(db)
            print(f"✓ Using admin user: {admin_user.username}\n")
            
            # Create currencies
            currencies_map = await create_currencies(db)
            
            # Create exchange rates
            await create_exchange_rates(db, currencies_map, admin_user)
            
            print("=" * 60)
            print("✓ Currency seeding completed successfully!")
            print("=" * 60)
            print()
            print("📊 Summary:")
            print(f"   • Currencies: {len(currencies_map)}")
            print(f"   • Base Currency: USD")
            print(f"   • Exchange Rates: {len(SAMPLE_EXCHANGE_RATES)}")
            print()
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            await db.rollback()
            raise


async def show_currencies():
    """Display all currencies and their rates"""
    print("=" * 60)
    print("Current Currencies and Exchange Rates")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as db:
        # Get all currencies
        result = await db.execute(
            select(Currency).where(Currency.is_active == True)
        )
        currencies = result.scalars().all()
        
        print("Currencies:")
        print("-" * 60)
        for currency in currencies:
            base_marker = " (BASE)" if currency.is_base_currency else ""
            print(f"  {currency.code} - {currency.name_en} ({currency.name_ar}){base_marker}")
        
        print()
        print("Exchange Rates:")
        print("-" * 60)
        
        # Get all active exchange rates
        result = await db.execute(
            select(ExchangeRate).where(
                ExchangeRate.effective_to.is_(None)
            )
        )
        rates = result.scalars().all()
        
        for rate in rates:
            print(f"  {rate.from_currency.code}/{rate.to_currency.code}: {rate.rate}")
            if rate.buy_rate:
                print(f"    Buy: {rate.buy_rate}, Sell: {rate.sell_rate}")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        asyncio.run(show_currencies())
    else:
        asyncio.run(seed_currencies())