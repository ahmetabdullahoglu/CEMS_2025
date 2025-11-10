#!/usr/bin/env python3
"""
Test script for new currency service features:
1. Cross-rate conversion via USD intermediary
2. Balance aggregation in target currency

Usage:
    python scripts/test_currency_features.py
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import AsyncSessionLocal
from app.services.currency_service import CurrencyService


async def test_cross_rate_conversion():
    """Test cross-rate conversion via USD intermediary"""
    print("=" * 70)
    print("Testing Cross-Rate Conversion via USD Intermediary")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        service = CurrencyService(db)

        # Test cases for cross-rate conversion
        test_cases = [
            # Direct rates (should work normally)
            {"from": "USD", "to": "TRY", "amount": Decimal("100.00")},
            {"from": "EUR", "to": "TRY", "amount": Decimal("100.00")},

            # These might need cross-rate via USD
            {"from": "AED", "to": "EGP", "amount": Decimal("1000.00")},
            {"from": "SAR", "to": "TRY", "amount": Decimal("1000.00")},
            {"from": "JPY", "to": "EGP", "amount": Decimal("10000.00")},
            {"from": "EGP", "to": "AED", "amount": Decimal("5000.00")},
        ]

        for test in test_cases:
            try:
                print(f"Converting {test['amount']} {test['from']} to {test['to']}...")

                result = await service.convert_amount(
                    amount=test["amount"],
                    from_currency_code=test["from"],
                    to_currency_code=test["to"],
                    use_intermediary=True
                )

                print(f"  ✅ Success!")
                print(f"     From: {result['from_amount']} {result['from_currency']}")
                print(f"     To: {result['to_amount']} {result['to_currency']}")
                print(f"     Rate: {result['rate']}")
                print(f"     Rate Type: {result['rate_type']}")

                if result.get('via_intermediary'):
                    print(f"     ⚡ Via Intermediary: Yes (used USD)")
                    if result.get('notes'):
                        print(f"     Notes: {result['notes']}")
                else:
                    print(f"     Direct Rate: Yes")

                print()

            except Exception as e:
                print(f"  ❌ Error: {e}")
                print()


async def test_balance_aggregation():
    """Test balance aggregation in different currencies"""
    print("=" * 70)
    print("Testing Balance Aggregation")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        service = CurrencyService(db)

        # Sample balances from different currencies
        branch_balances = [
            {'currency_code': 'TRY', 'amount': Decimal('500000.00')},
            {'currency_code': 'USD', 'amount': Decimal('50000.00')},
            {'currency_code': 'EUR', 'amount': Decimal('30000.00')},
            {'currency_code': 'EGP', 'amount': Decimal('100000.00')},
            {'currency_code': 'SAR', 'amount': Decimal('25000.00')},
            {'currency_code': 'GBP', 'amount': Decimal('5000.00')},
            {'currency_code': 'AED', 'amount': Decimal('15000.00')},
        ]

        # Test aggregation to different currencies
        target_currencies = ['USD', 'EUR', 'TRY', 'EGP']

        for target in target_currencies:
            try:
                print(f"Aggregating balances to {target}...")
                print("-" * 70)

                result = await service.aggregate_balances(
                    balances=branch_balances,
                    target_currency_code=target,
                    use_buy_rate=False,
                    use_sell_rate=False
                )

                print(f"  Target Currency: {result['target_currency']}")
                print(f"  Total Amount: {result['total_amount']:,.2f} {result['target_currency']}")
                print(f"  Rate Type: {result['rate_type']}")
                print()
                print("  Breakdown:")

                for item in result['breakdown']:
                    if 'error' in item:
                        print(f"    ❌ {item['currency']}: {item['original_amount']:,.2f} - Error: {item['error']}")
                    else:
                        intermediary_marker = " (via USD)" if item.get('via_intermediary') else ""
                        print(
                            f"    ✅ {item['currency']}: {item['original_amount']:,.2f} "
                            f"→ {item['converted_amount']:,.2f} {target} "
                            f"(rate: {item['rate_used']}){intermediary_marker}"
                        )

                print()
                print()

            except Exception as e:
                print(f"  ❌ Error aggregating to {target}: {e}")
                print()


async def test_specific_cross_rates():
    """Test specific cross-rate scenarios"""
    print("=" * 70)
    print("Testing Specific Cross-Rate Scenarios")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        service = CurrencyService(db)

        # Test getting rates that might not exist directly
        scenarios = [
            ("AED", "EGP", "Dirham to Egyptian Pound"),
            ("EGP", "AED", "Egyptian Pound to Dirham"),
            ("SAR", "EGP", "Riyal to Egyptian Pound"),
            ("JPY", "SAR", "Yen to Riyal"),
        ]

        for from_curr, to_curr, description in scenarios:
            try:
                print(f"{description} ({from_curr}/{to_curr})...")

                rate = await service.get_latest_rate(
                    from_currency_code=from_curr,
                    to_currency_code=to_curr,
                    use_intermediary=True
                )

                print(f"  ✅ Rate Found: {rate.rate}")
                if rate.notes and 'via USD' in rate.notes:
                    print(f"  ⚡ Calculated via USD intermediary")
                    print(f"  Notes: {rate.notes}")
                else:
                    print(f"  Direct rate available")

                print()

            except Exception as e:
                print(f"  ❌ Error: {e}")
                print()


async def main():
    """Main test function"""
    print("\n🧪 Testing New Currency Service Features\n")

    try:
        # Test 1: Cross-rate conversion
        await test_cross_rate_conversion()

        # Test 2: Balance aggregation
        await test_balance_aggregation()

        # Test 3: Specific cross-rate scenarios
        await test_specific_cross_rates()

        print("=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
