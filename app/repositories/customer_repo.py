# app/repositories/customer_repo.py
"""
Customer Repository
Data access layer for customer operations

Phase 5.2: Customer Service & API
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload

from app.db.models.customer import Customer, CustomerDocument, CustomerNote, CustomerType, RiskLevel, DocumentType
from app.core.exceptions import NotFoundError, ValidationError


class CustomerRepository:
    """Repository for customer data operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== Basic CRUD ====================
    
    async def get_by_id(
        self,
        customer_id: UUID,
        include_documents: bool = False,
        include_notes: bool = False
    ) -> Optional[Customer]:
        """Get customer by ID with optional eager loading"""
        query = select(Customer).where(Customer.id == customer_id)
        
        # Eager load relationships if requested
        if include_documents:
            query = query.options(selectinload(Customer.documents))
        if include_notes:
            query = query.options(selectinload(Customer.notes))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_customer_number(self, customer_number: str) -> Optional[Customer]:
        """Get customer by unique customer number"""
        result = await self.db.execute(
            select(Customer).where(Customer.customer_number == customer_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_national_id(self, national_id: str) -> Optional[Customer]:
        """Get customer by national ID"""
        result = await self.db.execute(
            select(Customer).where(Customer.national_id == national_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_passport(self, passport_number: str) -> Optional[Customer]:
        """Get customer by passport number"""
        result = await self.db.execute(
            select(Customer).where(Customer.passport_number == passport_number)
        )
        return result.scalar_one_or_none()
    
    async def create(self, customer: Customer) -> Customer:
        """Create new customer"""
        self.db.add(customer)
        await self.db.flush()
        await self.db.refresh(customer)
        return customer
    
    async def update(self, customer: Customer) -> Customer:
        """Update existing customer"""
        await self.db.flush()
        await self.db.refresh(customer)
        return customer
    
    async def delete(self, customer: Customer) -> None:
        """Soft delete customer (set is_active = False)"""
        customer.is_active = False
        await self.db.flush()
    
    # ==================== Search & Filtering ====================
    
    async def search_customers(
        self,
        query: Optional[str] = None,
        branch_id: Optional[UUID] = None,
        customer_type: Optional[CustomerType] = None,
        risk_level: Optional[RiskLevel] = None,
        is_verified: Optional[bool] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Customer]:
        """
        Advanced customer search with multiple filters
        
        Args:
            query: Search text (name, phone, email, national_id, passport)
            branch_id: Filter by branch
            customer_type: Filter by type (individual/corporate)
            risk_level: Filter by risk level
            is_verified: Filter by verification status
            is_active: Filter by active status
            skip: Pagination offset
            limit: Pagination limit
        """
        stmt = select(Customer)
        
        # Build filters
        filters = []
        
        if is_active is not None:
            filters.append(Customer.is_active == is_active)
        
        if branch_id:
            filters.append(Customer.branch_id == branch_id)
        
        if customer_type:
            filters.append(Customer.customer_type == customer_type)
        
        if risk_level:
            filters.append(Customer.risk_level == risk_level)
        
        if is_verified is not None:
            filters.append(Customer.is_verified == is_verified)
        
        # Text search across multiple fields
        if query:
            search_term = f"%{query}%"
            filters.append(
                or_(
                    Customer.first_name.ilike(search_term),
                    Customer.last_name.ilike(search_term),
                    Customer.name_ar.ilike(search_term),
                    Customer.phone_number.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.national_id.ilike(search_term),
                    Customer.passport_number.ilike(search_term),
                    Customer.customer_number.ilike(search_term)
                )
            )
        
        # Apply all filters
        if filters:
            stmt = stmt.where(and_(*filters))
        
        # Ordering and pagination
        stmt = stmt.order_by(desc(Customer.registered_at))
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def count_customers(
        self,
        query: Optional[str] = None,
        branch_id: Optional[UUID] = None,
        customer_type: Optional[CustomerType] = None,
        risk_level: Optional[RiskLevel] = None,
        is_verified: Optional[bool] = None,
        is_active: bool = True
    ) -> int:
        """Count customers matching search criteria"""
        stmt = select(func.count(Customer.id))
        
        filters = []
        
        if is_active is not None:
            filters.append(Customer.is_active == is_active)
        if branch_id:
            filters.append(Customer.branch_id == branch_id)
        if customer_type:
            filters.append(Customer.customer_type == customer_type)
        if risk_level:
            filters.append(Customer.risk_level == risk_level)
        if is_verified is not None:
            filters.append(Customer.is_verified == is_verified)
        
        if query:
            search_term = f"%{query}%"
            filters.append(
                or_(
                    Customer.first_name.ilike(search_term),
                    Customer.last_name.ilike(search_term),
                    Customer.name_ar.ilike(search_term),
                    Customer.phone_number.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.national_id.ilike(search_term),
                    Customer.passport_number.ilike(search_term)
                )
            )
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    # ==================== Customer Statistics ====================
    
    async def get_customer_transaction_count(self, customer_id: UUID) -> int:
        """Get total number of transactions for customer"""
        # This will be implemented when Transaction model is ready
        # For now, return 0
        return 0
    
    async def get_customer_total_volume(self, customer_id: UUID) -> Decimal:
        """Get total transaction volume for customer"""
        # This will be implemented when Transaction model is ready
        return Decimal("0.00")
    
    async def get_recent_customers(
        self,
        branch_id: Optional[UUID] = None,
        days: int = 30,
        limit: int = 10
    ) -> List[Customer]:
        """Get recently registered customers"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(Customer).where(
            and_(
                Customer.registered_at >= since_date,
                Customer.is_active == True
            )
        )
        
        if branch_id:
            stmt = stmt.where(Customer.branch_id == branch_id)
        
        stmt = stmt.order_by(desc(Customer.registered_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # ==================== Documents ====================
    
    async def get_customer_documents(
        self,
        customer_id: UUID,
        document_type: Optional[DocumentType] = None,
        is_verified: Optional[bool] = None
    ) -> List[CustomerDocument]:
        """Get customer documents with optional filters"""
        stmt = select(CustomerDocument).where(
            CustomerDocument.customer_id == customer_id
        )
        
        if document_type:
            stmt = stmt.where(CustomerDocument.document_type == document_type)
        if is_verified is not None:
            stmt = stmt.where(CustomerDocument.is_verified == is_verified)

        stmt = stmt.order_by(desc(CustomerDocument.created_at))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_document_by_id(self, document_id: UUID) -> Optional[CustomerDocument]:
        """Get document by ID"""
        result = await self.db.execute(
            select(CustomerDocument).where(CustomerDocument.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def create_document(self, document: CustomerDocument) -> CustomerDocument:
        """Create customer document"""
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document
    
    async def update_document(self, document: CustomerDocument) -> CustomerDocument:
        """Update customer document"""
        await self.db.flush()
        await self.db.refresh(document)
        return document
    
    async def get_expired_documents(
        self,
        branch_id: Optional[UUID] = None,
        days_before_expiry: int = 30
    ) -> List[CustomerDocument]:
        """Get documents expiring soon or already expired"""
        expiry_date = date.today() + timedelta(days=days_before_expiry)
        
        stmt = select(CustomerDocument).join(Customer).where(
            and_(
                CustomerDocument.expiry_date <= expiry_date,
                CustomerDocument.is_verified == True,
                Customer.is_active == True
            )
        )
        
        if branch_id:
            stmt = stmt.where(Customer.branch_id == branch_id)
        
        stmt = stmt.order_by(CustomerDocument.expiry_date)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # ==================== Notes ====================
    
    async def get_customer_notes(
        self,
        customer_id: UUID,
        is_alert: Optional[bool] = None,
        limit: int = 50
    ) -> List[CustomerNote]:
        """Get customer notes"""
        stmt = select(CustomerNote).where(
            CustomerNote.customer_id == customer_id
        )
        
        if is_alert is not None:
            stmt = stmt.where(CustomerNote.is_alert == is_alert)
        
        stmt = stmt.order_by(desc(CustomerNote.created_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_note(self, note: CustomerNote) -> CustomerNote:
        """Create customer note"""
        self.db.add(note)
        await self.db.flush()
        await self.db.refresh(note)
        return note
    
    async def get_note_by_id(self, note_id: UUID) -> Optional[CustomerNote]:
        """Get note by ID"""
        result = await self.db.execute(
            select(CustomerNote).where(CustomerNote.id == note_id)
        )
        return result.scalar_one_or_none()
    
    async def update_note(self, note: CustomerNote) -> CustomerNote:
        """Update customer note"""
        await self.db.flush()
        await self.db.refresh(note)
        return note
    
    async def delete_note(self, note: CustomerNote) -> None:
        """Delete customer note"""
        await self.db.delete(note)
        await self.db.flush()
    
    # ==================== Branch Statistics ====================
    
    async def get_branch_customer_stats(self, branch_id: UUID) -> Dict[str, Any]:
        """Get customer statistics for a branch"""
        # Total customers
        total_result = await self.db.execute(
            select(func.count(Customer.id)).where(
                and_(
                    Customer.branch_id == branch_id,
                    Customer.is_active == True
                )
            )
        )
        total_customers = total_result.scalar_one()
        
        # Verified customers
        verified_result = await self.db.execute(
            select(func.count(Customer.id)).where(
                and_(
                    Customer.branch_id == branch_id,
                    Customer.is_active == True,
                    Customer.is_verified == True
                )
            )
        )
        verified_customers = verified_result.scalar_one()
        
        # By type
        type_result = await self.db.execute(
            select(
                Customer.customer_type,
                func.count(Customer.id)
            ).where(
                and_(
                    Customer.branch_id == branch_id,
                    Customer.is_active == True
                )
            ).group_by(Customer.customer_type)
        )
        by_type = {row[0].value: row[1] for row in type_result.all()}
        
        # By risk level
        risk_result = await self.db.execute(
            select(
                Customer.risk_level,
                func.count(Customer.id)
            ).where(
                and_(
                    Customer.branch_id == branch_id,
                    Customer.is_active == True
                )
            ).group_by(Customer.risk_level)
        )
        by_risk = {row[0].value if row[0] else "unassessed": row[1] for row in risk_result.all()}
        
        return {
            "total_customers": total_customers,
            "verified_customers": verified_customers,
            "unverified_customers": total_customers - verified_customers,
            "by_type": by_type,
            "by_risk_level": by_risk
        }
