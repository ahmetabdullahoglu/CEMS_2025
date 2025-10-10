"""
Currency Repository
Data access layer for currency operations
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.db.models.currency import Currency, ExchangeRate, ExchangeRateHistory
from app.core.exceptions import DatabaseError, ValidationError


class CurrencyRepository:
    """Repository for Currency database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Currency Operations ====================
    
    def get_all_currencies(
        self,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Currency]:
        """
        Get all currencies with pagination
        
        Args:
            include_inactive: Include inactive currencies
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of Currency objects
        """
        query = select(Currency)
        
        if not include_inactive:
            query = query.where(Currency.is_active == True)
        
        query = query.order_by(Currency.code).offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def get_currency_by_id(self, currency_id: UUID) -> Optional[Currency]:
        """Get currency by ID"""
        query = select(Currency).where(Currency.id == currency_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_currency_by_code(self, code: str) -> Optional[Currency]:
        """
        Get currency by code
        
        Args:
            code: ISO 4217 currency code (e.g., 'USD')
            
        Returns:
            Currency object or None
        """
        query = select(Currency).where(Currency.code == code.upper())
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_base_currency(self) -> Optional[Currency]:
        """
        Get the system's base currency
        
        Returns:
            Base Currency object or None
        """
        query = select(Currency).where(
            and_(
                Currency.is_base_currency == True,
                Currency.is_active == True
            )
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def create_currency(self, currency_data: dict) -> Currency:
        """
        Create new currency
        
        Args:
            currency_data: Dictionary with currency data
            
        Returns:
            Created Currency object
            
        Raises:
            DatabaseException: If creation fails
            ValidationException: If validation fails
        """
        try:
            # Check if code already exists
            existing = self.get_currency_by_code(currency_data['code'])
            if existing:
                raise ValidationException(
                    f"Currency with code {currency_data['code']} already exists"
                )
            
            # If this is base currency, ensure no other base exists
            if currency_data.get('is_base_currency'):
                base = self.get_base_currency()
                if base:
                    raise ValidationException(
                        f"Base currency already exists: {base.code}"
                    )
            
            currency = Currency(**currency_data)
            self.db.add(currency)
            self.db.commit()
            self.db.refresh(currency)
            return currency
            
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create currency: {str(e)}")
    
    def update_currency(self, currency_id: UUID, update_data: dict) -> Currency:
        """
        Update currency
        
        Args:
            currency_id: Currency UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated Currency object
            
        Raises:
            DatabaseException: If update fails
            ValidationException: If validation fails
        """
        try:
            currency = self.get_currency_by_id(currency_id)
            if not currency:
                raise ValidationError(f"Currency {currency_id} not found")
            
            # If setting as base currency, check existing base
            if update_data.get('is_base_currency') and not currency.is_base_currency:
                base = self.get_base_currency()
                if base and base.id != currency_id:
                    raise ValidationException(
                        f"Base currency already exists: {base.code}. "
                        "Deactivate it first."
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(currency, key) and value is not None:
                    setattr(currency, key, value)
            
            self.db.commit()
            self.db.refresh(currency)
            return currency
            
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update currency: {str(e)}")
    
    def activate_currency(self, currency_id: UUID) -> Currency:
        """Activate currency"""
        return self.update_currency(currency_id, {'is_active': True})
    
    def deactivate_currency(self, currency_id: UUID) -> Currency:
        """Deactivate currency"""
        currency = self.get_currency_by_id(currency_id)
        if currency and currency.is_base_currency:
            raise ValidationError("Cannot deactivate base currency")
        return self.update_currency(currency_id, {'is_active': False})
    
    def count_currencies(self, include_inactive: bool = False) -> int:
        """Count total currencies"""
        query = select(func.count(Currency.id))
        if not include_inactive:
            query = query.where(Currency.is_active == True)
        result = self.db.execute(query)
        return result.scalar()
    
    # ==================== Exchange Rate Operations ====================
    
    def get_exchange_rate(
        self,
        from_currency_id: UUID,
        to_currency_id: UUID,
        at_date: Optional[datetime] = None
    ) -> Optional[ExchangeRate]:
        """
        Get exchange rate between two currencies
        
        Args:
            from_currency_id: Source currency UUID
            to_currency_id: Target currency UUID
            at_date: Get rate at specific date (default: current)
            
        Returns:
            ExchangeRate object or None
        """
        query = select(ExchangeRate).where(
            and_(
                ExchangeRate.from_currency_id == from_currency_id,
                ExchangeRate.to_currency_id == to_currency_id
            )
        )
        
        if at_date:
            query = query.where(
                and_(
                    ExchangeRate.effective_from <= at_date,
                    or_(
                        ExchangeRate.effective_to.is_(None),
                        ExchangeRate.effective_to > at_date
                    )
                )
            )
        else:
            # Current rate
            now = datetime.utcnow()
            query = query.where(
                and_(
                    ExchangeRate.effective_from <= now,
                    or_(
                        ExchangeRate.effective_to.is_(None),
                        ExchangeRate.effective_to > now
                    )
                )
            )
        
        query = query.options(
            selectinload(ExchangeRate.from_currency),
            selectinload(ExchangeRate.to_currency)
        ).order_by(ExchangeRate.effective_from.desc())
        
        result = self.db.execute(query)
        return result.scalars().first()
    
    def get_all_rates_for_currency(
        self,
        currency_id: UUID,
        include_historical: bool = False
    ) -> List[ExchangeRate]:
        """
        Get all exchange rates for a currency
        
        Args:
            currency_id: Currency UUID
            include_historical: Include historical rates
            
        Returns:
            List of ExchangeRate objects
        """
        query = select(ExchangeRate).where(
            or_(
                ExchangeRate.from_currency_id == currency_id,
                ExchangeRate.to_currency_id == currency_id
            )
        )
        
        if not include_historical:
            now = datetime.utcnow()
            query = query.where(
                and_(
                    ExchangeRate.effective_from <= now,
                    or_(
                        ExchangeRate.effective_to.is_(None),
                        ExchangeRate.effective_to > now
                    )
                )
            )
        
        query = query.options(
            selectinload(ExchangeRate.from_currency),
            selectinload(ExchangeRate.to_currency)
        ).order_by(ExchangeRate.effective_from.desc())
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def create_exchange_rate(self, rate_data: dict) -> ExchangeRate:
        """
        Create new exchange rate
        
        Args:
            rate_data: Dictionary with rate data
            
        Returns:
            Created ExchangeRate object
            
        Raises:
            DatabaseException: If creation fails
            ValidationException: If validation fails
        """
        try:
            # Validate currencies exist
            from_curr = self.get_currency_by_id(rate_data['from_currency_id'])
            to_curr = self.get_currency_by_id(rate_data['to_currency_id'])
            
            if not from_curr or not to_curr:
                raise ValidationError("Invalid currency IDs")
            
            if rate_data['from_currency_id'] == rate_data['to_currency_id']:
                raise ValidationError("Cannot create rate for same currency")
            
            # Deactivate previous rate if exists
            existing = self.get_exchange_rate(
                rate_data['from_currency_id'],
                rate_data['to_currency_id']
            )
            
            if existing:
                existing.effective_to = datetime.utcnow()
                self.db.add(existing)
            
            # Create new rate
            rate = ExchangeRate(**rate_data)
            self.db.add(rate)
            self.db.commit()
            self.db.refresh(rate)
            
            # Reload with relationships
            query = select(ExchangeRate).where(
                ExchangeRate.id == rate.id
            ).options(
                selectinload(ExchangeRate.from_currency),
                selectinload(ExchangeRate.to_currency)
            )
            result = self.db.execute(query)
            return result.scalar_one()
            
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create exchange rate: {str(e)}")
    
    def update_exchange_rate(
        self,
        rate_id: UUID,
        update_data: dict
    ) -> ExchangeRate:
        """
        Update exchange rate
        
        Args:
            rate_id: Rate UUID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated ExchangeRate object
        """
        try:
            query = select(ExchangeRate).where(ExchangeRate.id == rate_id)
            result = self.db.execute(query)
            rate = result.scalar_one_or_none()
            
            if not rate:
                raise ValidationError(f"Exchange rate {rate_id} not found")
            
            for key, value in update_data.items():
                if hasattr(rate, key) and value is not None:
                    setattr(rate, key, value)
            
            self.db.commit()
            self.db.refresh(rate)
            return rate
            
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update exchange rate: {str(e)}")
    
    def get_rate_history(
        self,
        from_currency_id: UUID,
        to_currency_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ExchangeRate]:
        """
        Get historical exchange rates
        
        Args:
            from_currency_id: Source currency UUID
            to_currency_id: Target currency UUID
            start_date: Start date for history
            end_date: End date for history
            
        Returns:
            List of historical ExchangeRate objects
        """
        query = select(ExchangeRate).where(
            and_(
                ExchangeRate.from_currency_id == from_currency_id,
                ExchangeRate.to_currency_id == to_currency_id
            )
        )
        
        if start_date:
            query = query.where(ExchangeRate.effective_from >= start_date)
        if end_date:
            query = query.where(ExchangeRate.effective_from <= end_date)
        
        query = query.options(
            selectinload(ExchangeRate.from_currency),
            selectinload(ExchangeRate.to_currency)
        ).order_by(ExchangeRate.effective_from.desc())
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    # ==================== Audit Operations ====================
    
    def create_rate_history(self, history_data: dict) -> ExchangeRateHistory:
        """Create exchange rate history entry"""
        try:
            history = ExchangeRateHistory(**history_data)
            self.db.add(history)
            self.db.commit()
            self.db.refresh(history)
            return history
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create rate history: {str(e)}")