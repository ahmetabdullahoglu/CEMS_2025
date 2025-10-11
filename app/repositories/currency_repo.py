"""
Currency Repository - Async Version
Data access layer for currency operations
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.db.models.currency import Currency, ExchangeRate, ExchangeRateHistory
from app.core.exceptions import DatabaseError, ValidationError


class CurrencyRepository:
    """Repository for Currency database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== Currency Operations ====================
    
    async def get_all_currencies(
        self,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Currency]:
        """Get all currencies with pagination"""
        query = select(Currency)
        
        if not include_inactive:
            query = query.where(Currency.is_active == True)
        
        query = query.order_by(Currency.code).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_currency_by_id(self, currency_id: UUID) -> Optional[Currency]:
        """Get currency by ID"""
        query = select(Currency).where(Currency.id == currency_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_currency_by_code(self, code: str) -> Optional[Currency]:
        """Get currency by code"""
        query = select(Currency).where(Currency.code == code.upper())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_base_currency(self) -> Optional[Currency]:
        """Get the system's base currency"""
        query = select(Currency).where(
            and_(
                Currency.is_base_currency == True,
                Currency.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_currency(self, currency_data: dict) -> Currency:
        """Create new currency"""
        try:
            # Check if code already exists
            existing = await self.get_currency_by_code(currency_data['code'])
            if existing:
                raise ValidationError(
                    f"Currency with code {currency_data['code']} already exists"
                )
            
            # If this is base currency, ensure no other base exists
            if currency_data.get('is_base_currency'):
                base = await self.get_base_currency()
                if base:
                    raise ValidationError(
                        f"Base currency already exists: {base.code}"
                    )
            
            currency = Currency(**currency_data)
            self.db.add(currency)
            await self.db.commit()
            await self.db.refresh(currency)
            return currency
            
        except IntegrityError as e:
            await self.db.rollback()
            raise DatabaseError(f"Failed to create currency: {str(e)}")
    
    async def update_currency(self, currency_id: UUID, update_data: dict) -> Currency:
        """Update currency"""
        try:
            currency = await self.get_currency_by_id(currency_id)
            if not currency:
                raise ValidationError(f"Currency {currency_id} not found")
            
            # If setting as base currency, check existing base
            if update_data.get('is_base_currency') and not currency.is_base_currency:
                base = await self.get_base_currency()
                if base and base.id != currency_id:
                    raise ValidationError(
                        f"Base currency already exists: {base.code}. "
                        "Deactivate it first."
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(currency, key) and value is not None:
                    setattr(currency, key, value)
            
            await self.db.commit()
            await self.db.refresh(currency)
            return currency
            
        except IntegrityError as e:
            await self.db.rollback()
            raise DatabaseError(f"Failed to update currency: {str(e)}")
    
    async def activate_currency(self, currency_id: UUID) -> Currency:
        """Activate currency"""
        return await self.update_currency(currency_id, {'is_active': True})
    
    async def deactivate_currency(self, currency_id: UUID) -> Currency:
        """Deactivate currency"""
        currency = await self.get_currency_by_id(currency_id)
        if currency and currency.is_base_currency:
            raise ValidationError("Cannot deactivate base currency")
        return await self.update_currency(currency_id, {'is_active': False})
    
    async def count_currencies(self, include_inactive: bool = False) -> int:
        """Count total currencies"""
        query = select(func.count(Currency.id))
        if not include_inactive:
            query = query.where(Currency.is_active == True)
        result = await self.db.execute(query)
        return result.scalar()
    
    # ==================== Exchange Rate Operations ====================
    
    async def get_exchange_rate(
        self,
        from_currency_id: UUID,
        to_currency_id: UUID,
        at_date: Optional[datetime] = None
    ) -> Optional[ExchangeRate]:
        """Get exchange rate between two currencies"""
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
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_all_rates_for_currency(
        self,
        currency_id: UUID,
        include_historical: bool = False
    ) -> List[ExchangeRate]:
        """Get all exchange rates for a currency"""
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
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_exchange_rate(self, rate_data: dict) -> ExchangeRate:
        """Create new exchange rate"""
        try:
            # Validate currencies exist
            from_curr = await self.get_currency_by_id(rate_data['from_currency_id'])
            to_curr = await self.get_currency_by_id(rate_data['to_currency_id'])
            
            if not from_curr or not to_curr:
                raise ValidationError("Invalid currency IDs")
            
            if rate_data['from_currency_id'] == rate_data['to_currency_id']:
                raise ValidationError("Cannot create rate for same currency")
            
            # Deactivate previous rate if exists
            existing = await self.get_exchange_rate(
                rate_data['from_currency_id'],
                rate_data['to_currency_id']
            )
            
            if existing:
                existing.effective_to = datetime.utcnow()
                self.db.add(existing)
            
            # Create new rate
            rate = ExchangeRate(**rate_data)
            self.db.add(rate)
            await self.db.commit()
            await self.db.refresh(rate)
            
            # Reload with relationships
            query = select(ExchangeRate).where(
                ExchangeRate.id == rate.id
            ).options(
                selectinload(ExchangeRate.from_currency),
                selectinload(ExchangeRate.to_currency)
            )
            result = await self.db.execute(query)
            return result.scalar_one()
            
        except IntegrityError as e:
            await self.db.rollback()
            raise DatabaseError(f"Failed to create exchange rate: {str(e)}")
    
    async def update_exchange_rate(
        self,
        rate_id: UUID,
        update_data: dict
    ) -> ExchangeRate:
        """Update exchange rate"""
        try:
            query = select(ExchangeRate).where(ExchangeRate.id == rate_id)
            result = await self.db.execute(query)
            rate = result.scalar_one_or_none()
            
            if not rate:
                raise ValidationError(f"Exchange rate {rate_id} not found")
            
            for key, value in update_data.items():
                if hasattr(rate, key) and value is not None:
                    setattr(rate, key, value)
            
            await self.db.commit()
            await self.db.refresh(rate)
            return rate
            
        except IntegrityError as e:
            await self.db.rollback()
            raise DatabaseError(f"Failed to update exchange rate: {str(e)}")
    
    async def get_rate_history(
        self,
        from_currency_id: UUID,
        to_currency_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ExchangeRate]:
        """Get historical exchange rates"""
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
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ==================== Audit Operations ====================
    
    async def create_rate_history(self, history_data: dict) -> ExchangeRateHistory:
        """Create exchange rate history entry"""
        try:
            history = ExchangeRateHistory(**history_data)
            self.db.add(history)
            await self.db.commit()
            await self.db.refresh(history)
            return history
        except IntegrityError as e:
            await self.db.rollback()
            raise DatabaseError(f"Failed to create rate history: {str(e)}")