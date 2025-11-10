"""
Add GBP/TRY exchange rate directly to database
Run this if the rate is missing
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.db.models.currency import Currency, ExchangeRate


async def add_gbp_try_rate():
    """Add GBP/TRY exchange rate"""

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Get GBP and TRY currencies
            result = await session.execute(
                text("SELECT id, code FROM currencies WHERE code IN ('GBP', 'TRY')")
            )
            currencies = {row[1]: row[0] for row in result}

            if 'GBP' not in currencies or 'TRY' not in currencies:
                print("❌ GBP or TRY currency not found in database")
                print("Please run seed_currencies.py first")
                return

            gbp_id = currencies['GBP']
            try_id = currencies['TRY']

            print(f"✅ Found GBP: {gbp_id}")
            print(f"✅ Found TRY: {try_id}")

            # Check if rate already exists
            result = await session.execute(
                text("""
                    SELECT id FROM exchange_rates
                    WHERE from_currency_id = :gbp_id
                    AND to_currency_id = :try_id
                """),
                {"gbp_id": gbp_id, "try_id": try_id}
            )
            existing = result.first()

            if existing:
                print(f"✅ GBP/TRY rate already exists: {existing[0]}")
                return

            # Get admin user (first user)
            result = await session.execute(text("SELECT id FROM users LIMIT 1"))
            user = result.first()
            if not user:
                print("❌ No users found in database")
                return

            user_id = user[0]
            print(f"✅ Using user: {user_id}")

            # Add GBP -> TRY rate
            await session.execute(
                text("""
                    INSERT INTO exchange_rates (
                        from_currency_id, to_currency_id,
                        rate, buy_rate, sell_rate,
                        effective_from, set_by, is_current
                    ) VALUES (
                        :gbp_id, :try_id,
                        41.14, 41.00, 41.30,
                        NOW(), :user_id, true
                    )
                """),
                {"gbp_id": gbp_id, "try_id": try_id, "user_id": user_id}
            )
            print("✅ Added GBP → TRY rate: 41.14")

            # Add TRY -> GBP rate
            await session.execute(
                text("""
                    INSERT INTO exchange_rates (
                        from_currency_id, to_currency_id,
                        rate, buy_rate, sell_rate,
                        effective_from, set_by, is_current
                    ) VALUES (
                        :try_id, :gbp_id,
                        0.0243, 0.0242, 0.0244,
                        NOW(), :user_id, true
                    )
                """),
                {"try_id": try_id, "gbp_id": gbp_id, "user_id": user_id}
            )
            print("✅ Added TRY → GBP rate: 0.0243")

            await session.commit()
            print("\n✅ Successfully added GBP/TRY exchange rates!")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Adding GBP/TRY Exchange Rate")
    print("=" * 60)
    asyncio.run(add_gbp_try_rate())
