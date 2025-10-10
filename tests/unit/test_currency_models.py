"""
Unit Tests for Currency Models
Tests currency creation, exchange rates, and history tracking
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.currency import Currency, ExchangeRate, ExchangeRateHistory
from app.db.models.user import User


# ==================== Currency Model Tests ====================

@pytest.mark.unit
async def test_create_currency(db_session: AsyncSession):
    """Test creating a currency"""
    currency = Currency(
        code="USD",
        name_en="US Dollar",
        name_ar="دولار أمريكي",
        symbol="$",
        is_base_currency=True,
        decimal_places=2
    )
    
    db_session.add(currency)
    await db_session.commit()
    await db_session.refresh(currency)
    
    assert currency.id is not None
    assert currency.code == "USD"
    assert currency.name_en == "US Dollar"
    assert currency.name_ar == "دولار أمريكي"
    assert currency.symbol == "$"
    assert currency.is_base_currency is True
    assert currency.decimal_places == 2
    assert currency.is_active is True


@pytest.mark.unit
async def test_currency_unique_code(db_session: AsyncSession):
    """Test that currency code must be unique"""
    currency1 = Currency(
        code="EUR",
        name_en="Euro",
        name_ar="يورو",
        symbol="€"
    )
    db_session.add(currency1)
    await db_session.commit()
    
    # Try to create another currency with same code
    currency2 = Currency(
        code="EUR",
        name_en="European Euro",
        name_ar="يورو أوروبي",
        symbol="€"
    )
    db_session.add(currency2)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.unit
async def test_currency_code_length_constraint(db_session: AsyncSession):
    """Test that currency code must be exactly 3 characters"""
    # This will be caught by PostgreSQL constraint
    currency = Currency(
        code="US",  # Only 2 characters
        name_en="Invalid",
        name_ar="غير صالح"
    )
    db_session.add(currency)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.unit
async def test_single_base_currency(db_session: AsyncSession):
    """Test that only one base currency can be active"""
    # Create first base currency
    currency1 = Currency(
        code="USD",
        name_en="US Dollar",
        name_ar="دولار أمريكي",
        is_base_currency=True
    )
    db_session.add(currency1)
    await db_session.commit()
    
    # Try to create second base currency
    currency2 = Currency(
        code="EUR",
        name_en="Euro",
        name_ar="يورو",
        is_base_currency=True
    )
    db_session.add(currency2)
    
    # Should raise error from trigger
    with pytest.raises(Exception):  # Will raise from PostgreSQL trigger
        await db_session.commit()


@pytest.mark.unit
async def test_decimal_places_constraint(db_session: AsyncSession):
    """Test that decimal_places must be non-negative"""
    currency = Currency(
        code="XXX",
        name_en="Invalid Currency",
        name_ar="عملة غير صالحة",
        decimal_places=-1  # Invalid
    )
    db_session.add(currency)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ==================== Exchange Rate Model Tests ====================

@pytest.mark.unit
async def test_create_exchange_rate(db_session: AsyncSession, test_user: User):
    """Test creating an exchange rate"""
    # Create currencies
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    # Create exchange rate
    rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        buy_rate=Decimal("0.91"),
        sell_rate=Decimal("0.93"),
        set_by=test_user.id,
        effective_from=datetime.utcnow()
    )
    
    db_session.add(rate)
    await db_session.commit()
    await db_session.refresh(rate)
    
    assert rate.id is not None
    assert rate.rate == Decimal("0.92")
    assert rate.buy_rate == Decimal("0.91")
    assert rate.sell_rate == Decimal("0.93")
    assert rate.from_currency.code == "USD"
    assert rate.to_currency.code == "EUR"


@pytest.mark.unit
async def test_exchange_rate_positive_constraint(db_session: AsyncSession, test_user: User):
    """Test that exchange rate must be positive"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    # Try to create rate with negative value
    rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("-0.92"),  # Negative
        set_by=test_user.id
    )
    db_session.add(rate)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.unit
async def test_exchange_rate_same_currency_constraint(db_session: AsyncSession, test_user: User):
    """Test that from and to currencies must be different"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    db_session.add(usd)
    await db_session.commit()
    
    # Try to create rate with same currency
    rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=usd.id,  # Same currency
        rate=Decimal("1.0"),
        set_by=test_user.id
    )
    db_session.add(rate)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.unit
async def test_exchange_rate_is_current(db_session: AsyncSession, test_user: User):
    """Test is_current property"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    # Create current rate
    current_rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        set_by=test_user.id,
        effective_from=datetime.utcnow() - timedelta(days=1),
        effective_to=None  # Current rate
    )
    db_session.add(current_rate)
    await db_session.commit()
    await db_session.refresh(current_rate)
    
    assert current_rate.is_current is True
    
    # Create expired rate
    expired_rate = ExchangeRate(
        from_currency_id=eur.id,
        to_currency_id=usd.id,
        rate=Decimal("1.09"),
        set_by=test_user.id,
        effective_from=datetime.utcnow() - timedelta(days=2),
        effective_to=datetime.utcnow() - timedelta(days=1)  # Expired
    )
    db_session.add(expired_rate)
    await db_session.commit()
    await db_session.refresh(expired_rate)
    
    assert expired_rate.is_current is False


@pytest.mark.unit
async def test_calculate_exchange(db_session: AsyncSession, test_user: User):
    """Test exchange calculation"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        buy_rate=Decimal("0.91"),
        sell_rate=Decimal("0.93"),
        set_by=test_user.id
    )
    db_session.add(rate)
    await db_session.commit()
    
    # Test standard rate
    result = rate.calculate_exchange(Decimal("100"))
    assert result == Decimal("92")
    
    # Test buy rate
    result_buy = rate.calculate_exchange(Decimal("100"), use_buy=True)
    assert result_buy == Decimal("91")
    
    # Test sell rate
    result_sell = rate.calculate_exchange(Decimal("100"), use_sell=True)
    assert result_sell == Decimal("93")


@pytest.mark.unit
async def test_get_inverse_rate(db_session: AsyncSession, test_user: User):
    """Test inverse rate calculation"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        set_by=test_user.id
    )
    db_session.add(rate)
    await db_session.commit()
    
    inverse = rate.get_inverse_rate()
    # 1/0.92 ≈ 1.087
    assert inverse > Decimal("1.086") and inverse < Decimal("1.088")


# ==================== Exchange Rate History Tests ====================

@pytest.mark.unit
async def test_exchange_rate_history_tracking(db_session: AsyncSession, test_user: User):
    """Test that exchange rate changes are tracked in history"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    # Create initial rate
    rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        set_by=test_user.id
    )
    db_session.add(rate)
    await db_session.commit()
    await db_session.refresh(rate)
    
    # Check history was created (by trigger)
    result = await db_session.execute(
        select(ExchangeRateHistory).where(
            ExchangeRateHistory.exchange_rate_id == rate.id
        )
    )
    history = result.scalars().all()
    
    # Should have one history entry for creation
    assert len(history) >= 1
    assert history[0].change_type == "created"
    assert history[0].new_rate == Decimal("0.92")


@pytest.mark.unit
async def test_rate_change_percentage(db_session: AsyncSession, test_user: User):
    """Test rate change percentage calculation"""
    history = ExchangeRateHistory(
        exchange_rate_id=test_user.id,  # Dummy ID
        from_currency_code="USD",
        to_currency_code="EUR",
        old_rate=Decimal("0.90"),
        new_rate=Decimal("0.95"),
        change_type="updated",
        changed_by=test_user.id
    )
    
    # Calculate percentage change
    # (0.95 - 0.90) / 0.90 * 100 ≈ 5.56%
    percentage = history.rate_change_percentage
    assert percentage > Decimal("5.5") and percentage < Decimal("5.6")


# ==================== Relationship Tests ====================

@pytest.mark.unit
async def test_currency_relationships(db_session: AsyncSession, test_user: User):
    """Test currency-exchange rate relationships"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    gbp = Currency(code="GBP", name_en="British Pound", name_ar="جنيه إسترليني")
    db_session.add_all([usd, eur, gbp])
    await db_session.commit()
    
    # Create multiple rates for USD
    rate1 = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        set_by=test_user.id
    )
    rate2 = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=gbp.id,
        rate=Decimal("0.79"),
        set_by=test_user.id
    )
    db_session.add_all([rate1, rate2])
    await db_session.commit()
    await db_session.refresh(usd)
    
    # USD should have two "from" exchange rates
    assert len(usd.from_exchange_rates) == 2


@pytest.mark.unit
async def test_query_current_rates(db_session: AsyncSession, test_user: User):
    """Test querying current exchange rates"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    # Create current rate
    current_rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        set_by=test_user.id,
        effective_from=datetime.utcnow(),
        effective_to=None
    )
    
    # Create expired rate
    expired_rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.90"),
        set_by=test_user.id,
        effective_from=datetime.utcnow() - timedelta(days=2),
        effective_to=datetime.utcnow() - timedelta(days=1)
    )
    
    db_session.add_all([current_rate, expired_rate])
    await db_session.commit()
    
    # Query only current rates
    result = await db_session.execute(
        select(ExchangeRate).where(
            ExchangeRate.from_currency_id == usd.id,
            ExchangeRate.to_currency_id == eur.id,
            ExchangeRate.effective_to.is_(None)
        )
    )
    current_rates = result.scalars().all()
    
    # Should only return current rate
    assert len(current_rates) == 1
    assert current_rates[0].rate == Decimal("0.92")


# ==================== Edge Cases ====================

@pytest.mark.unit
async def test_zero_decimal_places_currency(db_session: AsyncSession):
    """Test currency with zero decimal places (like JPY)"""
    jpy = Currency(
        code="JPY",
        name_en="Japanese Yen",
        name_ar="ين ياباني",
        symbol="¥",
        decimal_places=0
    )
    
    db_session.add(jpy)
    await db_session.commit()
    
    assert jpy.decimal_places == 0


@pytest.mark.unit
async def test_very_precise_exchange_rate(db_session: AsyncSession, test_user: User):
    """Test exchange rate with maximum precision (6 decimal places)"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    jpy = Currency(code="JPY", name_en="Japanese Yen", name_ar="ين ياباني")
    db_session.add_all([usd, jpy])
    await db_session.commit()
    
    # Very precise rate
    rate = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=jpy.id,
        rate=Decimal("149.567890"),  # Will be stored as 149.567890
        set_by=test_user.id
    )
    
    db_session.add(rate)
    await db_session.commit()
    await db_session.refresh(rate)
    
    # Check precision is maintained
    assert str(rate.rate) == "149.567890"


@pytest.mark.unit
async def test_multiple_rates_same_pair_different_times(
    db_session: AsyncSession, 
    test_user: User
):
    """Test multiple rates for same currency pair at different times"""
    usd = Currency(code="USD", name_en="US Dollar", name_ar="دولار أمريكي")
    eur = Currency(code="EUR", name_en="Euro", name_ar="يورو")
    db_session.add_all([usd, eur])
    await db_session.commit()
    
    # Create rate for yesterday
    rate1 = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.90"),
        set_by=test_user.id,
        effective_from=datetime.utcnow() - timedelta(days=1),
        effective_to=datetime.utcnow()
    )
    
    # Create rate for today
    rate2 = ExchangeRate(
        from_currency_id=usd.id,
        to_currency_id=eur.id,
        rate=Decimal("0.92"),
        set_by=test_user.id,
        effective_from=datetime.utcnow(),
        effective_to=None
    )
    
    db_session.add_all([rate1, rate2])
    await db_session.commit()
    
    # Both should exist
    result = await db_session.execute(
        select(ExchangeRate).where(
            ExchangeRate.from_currency_id == usd.id,
            ExchangeRate.to_currency_id == eur.id
        )
    )
    rates = result.scalars().all()
    
    assert len(rates) == 2