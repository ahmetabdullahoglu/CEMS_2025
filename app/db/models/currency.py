"""
Currency Database Models
Handles currencies and exchange rates
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid

from app.db.base_class import BaseModel


class Currency(BaseModel):
    """
    Currency model
    Represents different currencies in the system
    """
    
    __tablename__ = "currencies"
    
    # Currency Information
    code = Column(
        String(3),
        unique=True,
        nullable=False,
        index=True,
        comment="ISO 4217 currency code (USD, EUR, TRY, etc.)"
    )
    
    name_en = Column(
        String(100),
        nullable=False,
        comment="English name of the currency"
    )
    
    name_ar = Column(
        String(100),
        nullable=False,
        comment="Arabic name of the currency"
    )
    
    symbol = Column(
        String(10),
        nullable=True,
        comment="Currency symbol ($, €, ₺, etc.)"
    )
    
    # Settings
    is_base_currency = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this is the base currency for the system (only one allowed)"
    )
    
    decimal_places = Column(
        Integer,
        default=2,
        nullable=False,
        comment="Number of decimal places for this currency"
    )
    
    # Relationships
    from_exchange_rates = relationship(
        "ExchangeRate",
        foreign_keys="ExchangeRate.from_currency_id",
        back_populates="from_currency",
        lazy="selectin"
    )
    
    to_exchange_rates = relationship(
        "ExchangeRate",
        foreign_keys="ExchangeRate.to_currency_id",
        back_populates="to_currency",
        lazy="selectin"
    )
    
    # Add these relationships
    transactions = relationship(
        "Transaction",
        back_populates="currency",
        foreign_keys="Transaction.currency_id"
    )
    
    exchange_from = relationship(
        "ExchangeTransaction",
        foreign_keys="ExchangeTransaction.from_currency_id"
    )
    
    exchange_to = relationship(
        "ExchangeTransaction",
        foreign_keys="ExchangeTransaction.to_currency_id"
    )
    # Table constraints
    __table_args__ = (
        CheckConstraint('LENGTH(code) = 3', name='currency_code_length_check'),
        CheckConstraint('decimal_places >= 0', name='currency_decimal_places_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<Currency(code='{self.code}', name='{self.name_en}')>"


class ExchangeRate(BaseModel):
    """
    Exchange Rate model
    Represents exchange rates between currencies
    """
    
    __tablename__ = "exchange_rates"
    
    # Currency Pair
    from_currency_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('currencies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="Source currency"
    )
    
    to_currency_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('currencies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="Target currency"
    )
    
    # Exchange Rates
    rate = Column(
        Numeric(precision=15, scale=6),
        nullable=False,
        comment="Exchange rate (1 from_currency = X to_currency)"
    )
    
    buy_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=True,
        comment="Buy rate (rate when buying from_currency)"
    )
    
    sell_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=True,
        comment="Sell rate (rate when selling from_currency)"
    )
    
    # Effective Period
    effective_from = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Rate becomes effective from this timestamp"
    )
    
    effective_to = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="Rate is effective until this timestamp (NULL = current rate)"
    )
    
    # Metadata
    set_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        comment="User who set this rate"
    )
    
    notes = Column(
        String(500),
        nullable=True,
        comment="Optional notes about this rate"
    )
    
    # Relationships
    from_currency = relationship(
        "Currency",
        foreign_keys=[from_currency_id],
        back_populates="from_exchange_rates"
    )
    
    to_currency = relationship(
        "Currency",
        foreign_keys=[to_currency_id],
        back_populates="to_exchange_rates"
    )
    
    setter = relationship(
        "User",
        foreign_keys=[set_by]
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            'from_currency_id', 
            'to_currency_id', 
            'effective_from',
            name='unique_currency_pair_time'
        ),
        CheckConstraint('rate > 0', name='exchange_rate_positive'),
        CheckConstraint('buy_rate IS NULL OR buy_rate > 0', name='buy_rate_positive'),
        CheckConstraint('sell_rate IS NULL OR sell_rate > 0', name='sell_rate_positive'),
        CheckConstraint('from_currency_id != to_currency_id', name='different_currencies'),
        CheckConstraint(
            'effective_to IS NULL OR effective_to > effective_from',
            name='valid_effective_period'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<ExchangeRate({self.from_currency.code}/{self.to_currency.code}: {self.rate})>"
    
    @property
    def is_current(self) -> bool:
        """Check if this is the current active rate"""
        now = datetime.utcnow()
        return (
            self.effective_from <= now and 
            (self.effective_to is None or self.effective_to > now)
        )
    
    def calculate_exchange(self, amount: Decimal, use_buy: bool = False, use_sell: bool = False) -> Decimal:
        """
        Calculate exchange amount
        
        Args:
            amount: Amount in from_currency
            use_buy: Use buy rate if available
            use_sell: Use sell rate if available
            
        Returns:
            Decimal: Amount in to_currency
        """
        if use_buy and self.buy_rate:
            return amount * self.buy_rate
        elif use_sell and self.sell_rate:
            return amount * self.sell_rate
        else:
            return amount * self.rate
    
    def get_inverse_rate(self) -> Decimal:
        """Get inverse exchange rate (to_currency -> from_currency)"""
        return Decimal('1') / self.rate


class ExchangeRateHistory(BaseModel):
    """
    Exchange Rate History model
    Tracks all changes to exchange rates for audit trail
    """
    
    __tablename__ = "exchange_rate_history"
    
    # Rate Reference
    exchange_rate_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('exchange_rates.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Exchange rate being modified"
    )
    
    # Currency Pair (denormalized for history)
    from_currency_code = Column(
        String(3),
        nullable=False,
        comment="Source currency code at time of change"
    )
    
    to_currency_code = Column(
        String(3),
        nullable=False,
        comment="Target currency code at time of change"
    )
    
    # Old Values
    old_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=True,
        comment="Previous exchange rate"
    )
    
    old_buy_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=True,
        comment="Previous buy rate"
    )
    
    old_sell_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=True,
        comment="Previous sell rate"
    )
    
    # New Values
    new_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=False,
        comment="New exchange rate"
    )
    
    new_buy_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=True,
        comment="New buy rate"
    )
    
    new_sell_rate = Column(
        Numeric(precision=15, scale=6),
        nullable=True,
        comment="New sell rate"
    )
    
    # Change Metadata
    change_type = Column(
        String(20),
        nullable=False,
        comment="Type of change (created, updated, deactivated)"
    )
    
    changed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        comment="User who made the change"
    )
    
    changed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When the change was made"
    )
    
    reason = Column(
        String(500),
        nullable=True,
        comment="Reason for the change"
    )
    
    # Relationships
    exchange_rate = relationship(
        "ExchangeRate",
        foreign_keys=[exchange_rate_id]
    )
    
    changer = relationship(
        "User",
        foreign_keys=[changed_by]
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('created', 'updated', 'deactivated')",
            name='valid_change_type'
        ),
    )
    
    def __repr__(self) -> str:
        return f"<ExchangeRateHistory({self.from_currency_code}/{self.to_currency_code}: {self.old_rate} -> {self.new_rate})>"
    
    @property
    def rate_change_percentage(self) -> Decimal:
        """Calculate percentage change in rate"""
        if self.old_rate and self.old_rate > 0:
            return ((self.new_rate - self.old_rate) / self.old_rate) * 100
        return Decimal('0')