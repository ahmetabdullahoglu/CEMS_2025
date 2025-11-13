# app/services/customer_service.py
"""
Customer Service
Business logic for customer management, KYC, and document verification

Phase 5.2: Customer Service & API
"""
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.repositories.customer_repo import CustomerRepository
from app.db.models.customer import (
    Customer, CustomerDocument, CustomerNote,
    CustomerType, RiskLevel, DocumentType
)
from app.db.models.user import User
from app.core.exceptions import (
    NotFoundError, ValidationError, DuplicateError,
    PermissionDeniedError
)
from app.utils.logger import get_logger
from app.utils.generators import generate_customer_number
from app.schemas.transaction import TransactionFilter

logger = get_logger(__name__)


class CustomerService:
    """Service for customer operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CustomerRepository(db)
    
    # ==================== Customer Creation & Management ====================
    
    async def create_customer(
        self,
        customer_data: Dict[str, Any],
        current_user: User,
        branch_id: UUID
    ) -> Customer:
        """
        Create new customer with validation
        
        Args:
            customer_data: Customer information
            current_user: User creating the customer
            branch_id: Branch where customer is registered
            
        Returns:
            Created customer
            
        Raises:
            DuplicateError: If national_id or passport already exists
            ValidationError: If data is invalid
        """
        logger.info(f"Creating customer at branch {branch_id} by user {current_user.id}")
        
        # Validate identification
        national_id = customer_data.get("national_id")
        passport_number = customer_data.get("passport_number")
        
        if not national_id and not passport_number:
            raise ValidationError("Customer must have either national_id or passport_number")
        
        # Check for duplicates
        if national_id:
            existing = await self.repo.get_by_national_id(national_id)
            if existing:
                raise DuplicateError(f"Customer with national_id {national_id} already exists")
        
        if passport_number:
            existing = await self.repo.get_by_passport(passport_number)
            if existing:
                raise DuplicateError(f"Customer with passport {passport_number} already exists")
        
        # Validate phone number format
        phone = customer_data.get("phone_number")
        if phone and not self._validate_phone(phone):
            raise ValidationError("Invalid phone number format")
        
        # Validate email if provided
        email = customer_data.get("email")
        if email and not self._validate_email(email):
            raise ValidationError("Invalid email format")
        
        # Generate unique customer number
        customer_number = await self._generate_unique_customer_number()
        
        # Create customer
        customer = Customer(
            customer_number=customer_number,
            first_name=customer_data["first_name"],
            last_name=customer_data["last_name"],
            name_ar=customer_data.get("name_ar"),
            national_id=national_id,
            passport_number=passport_number,
            phone_number=phone,
            email=email,
            date_of_birth=customer_data.get("date_of_birth"),
            nationality=customer_data.get("nationality"),
            address=customer_data.get("address"),
            city=customer_data.get("city"),
            country=customer_data.get("country"),
            customer_type=customer_data.get("customer_type", CustomerType.INDIVIDUAL),
            branch_id=branch_id,
            registered_by_id=current_user.id,
            additional_info=customer_data.get("additional_info")
        )
        
        try:
            customer = await self.repo.create(customer)
            await self.db.commit()
            
            logger.info(f"Customer created: {customer.customer_number}")
            return customer
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating customer: {str(e)}")
            raise DuplicateError("Customer with this information already exists")
    
    async def update_customer(
        self,
        customer_id: UUID,
        update_data: Dict[str, Any],
        current_user: User
    ) -> Customer:
        """
        Update customer information
        
        Args:
            customer_id: Customer to update
            update_data: Fields to update
            current_user: User performing the update
            
        Returns:
            Updated customer
        """
        logger.info(f"Updating customer {customer_id} by user {current_user.id}")
        
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        # Check if user has access to customer's branch
        # This would integrate with branch access control
        
        # Validate updates
        if "phone_number" in update_data:
            if not self._validate_phone(update_data["phone_number"]):
                raise ValidationError("Invalid phone number format")
        
        if "email" in update_data and update_data["email"]:
            if not self._validate_email(update_data["email"]):
                raise ValidationError("Invalid email format")
        
        # Update fields
        allowed_fields = [
            "first_name", "last_name", "name_ar", "phone_number", "email",
            "address", "city", "country", "customer_type", "additional_info"
        ]
        
        for field in allowed_fields:
            if field in update_data:
                setattr(customer, field, update_data[field])
        
        try:
            customer = await self.repo.update(customer)
            await self.db.commit()
            
            logger.info(f"Customer {customer_id} updated successfully")
            return customer
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Error updating customer: {str(e)}")
            raise ValidationError("Failed to update customer")
    
    async def deactivate_customer(
        self,
        customer_id: UUID,
        current_user: User
    ) -> Customer:
        """Deactivate customer (soft delete)"""
        logger.info(f"Deactivating customer {customer_id} by user {current_user.id}")
        
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        await self.repo.delete(customer)
        await self.db.commit()
        
        logger.info(f"Customer {customer_id} deactivated")
        return customer
    
    # ==================== Customer Search & Retrieval ====================
    
    async def get_customer_by_id(
        self,
        customer_id: UUID,
        include_documents: bool = False,
        include_notes: bool = False
    ) -> Customer:
        """Get customer by ID with optional related data"""
        customer = await self.repo.get_by_id(
            customer_id,
            include_documents=include_documents,
            include_notes=include_notes
        )
        
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        return customer
    
    async def get_customer_by_national_id(self, national_id: str) -> Optional[Customer]:
        """Get customer by national ID"""
        return await self.repo.get_by_national_id(national_id)
    
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
    ) -> Tuple[List[Customer], int]:
        """
        Search customers with pagination
        
        Returns:
            Tuple of (customers list, total count)
        """
        customers = await self.repo.search_customers(
            query=query,
            branch_id=branch_id,
            customer_type=customer_type,
            risk_level=risk_level,
            is_verified=is_verified,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        total = await self.repo.count_customers(
            query=query,
            branch_id=branch_id,
            customer_type=customer_type,
            risk_level=risk_level,
            is_verified=is_verified,
            is_active=is_active
        )
        
        return customers, total
    
    # ==================== KYC Verification ====================
    
    async def verify_customer_kyc(
        self,
        customer_id: UUID,
        risk_level: RiskLevel,
        verification_notes: Optional[str],
        current_user: User
    ) -> Customer:
        """
        Verify customer KYC status
        
        Args:
            customer_id: Customer to verify
            risk_level: Assessed risk level
            verification_notes: Notes about verification
            current_user: User performing verification
            
        Returns:
            Updated customer
        """
        logger.info(f"Verifying KYC for customer {customer_id} by user {current_user.id}")
        
        customer = await self.repo.get_by_id(customer_id, include_documents=True)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        # Check if customer has required documents
        if not customer.documents:
            raise ValidationError("Customer must have documents before KYC verification")
        
        # Update verification status
        customer.is_verified = True
        customer.verified_at = datetime.utcnow()
        customer.verified_by_id = current_user.id
        customer.risk_level = risk_level
        
        # Add verification note
        if verification_notes:
            note = CustomerNote(
                customer_id=customer_id,
                note_text=verification_notes,
                is_alert=False,
                created_by_id=current_user.id
            )
            await self.repo.create_note(note)
        
        customer = await self.repo.update(customer)
        await self.db.commit()
        
        logger.info(f"Customer {customer_id} KYC verified with risk level {risk_level.value}")
        return customer
    
    async def update_risk_level(
        self,
        customer_id: UUID,
        risk_level: RiskLevel,
        reason: str,
        current_user: User
    ) -> Customer:
        """Update customer risk level"""
        logger.info(f"Updating risk level for customer {customer_id}")
        
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        old_risk = customer.risk_level
        customer.risk_level = risk_level
        
        # Add note about risk level change
        note = CustomerNote(
            customer_id=customer_id,
            note_text=f"Risk level changed from {old_risk.value if old_risk else 'unassessed'} to {risk_level.value}. Reason: {reason}",
            is_alert=True,
            created_by_id=current_user.id
        )
        await self.repo.create_note(note)
        
        customer = await self.repo.update(customer)
        await self.db.commit()
        
        return customer
    
    # ==================== Document Management ====================
    
    async def add_customer_document(
        self,
        customer_id: UUID,
        document_type: DocumentType,
        document_url: str,
        document_number: Optional[str],
        issue_date: Optional[date],
        expiry_date: Optional[date],
        current_user: User
    ) -> CustomerDocument:
        """Add document to customer"""
        logger.info(f"Adding {document_type.value} document for customer {customer_id}")
        
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        # Validate expiry date
        if expiry_date and expiry_date < date.today():
            raise ValidationError("Document expiry date cannot be in the past")
        
        document = CustomerDocument(
            customer_id=customer_id,
            document_type=document_type,
            document_number=document_number,
            document_url=document_url,
            issue_date=issue_date,
            expiry_date=expiry_date,
            uploaded_by_id=current_user.id
        )
        
        try:
            document = await self.repo.create_document(document)
            await self.db.commit()
            
            logger.info(f"Document {document.id} added for customer {customer_id}")
            return document
            
        except IntegrityError:
            await self.db.rollback()
            raise DuplicateError("This document already exists for the customer")
    
    async def verify_document(
        self,
        document_id: UUID,
        is_verified: bool,
        verification_notes: Optional[str],
        current_user: User
    ) -> CustomerDocument:
        """Verify customer document"""
        logger.info(f"Verifying document {document_id}")
        
        document = await self.repo.get_document_by_id(document_id)
        if not document:
            raise NotFoundError(f"Document {document_id} not found")
        
        document.is_verified = is_verified
        document.verified_at = datetime.utcnow() if is_verified else None
        document.verified_by_id = current_user.id if is_verified else None
        document.verification_notes = verification_notes
        
        document = await self.repo.update_document(document)
        await self.db.commit()
        
        logger.info(f"Document {document_id} verification status: {is_verified}")
        return document
    
    async def get_customer_documents(
        self,
        customer_id: UUID,
        document_type: Optional[DocumentType] = None
    ) -> List[CustomerDocument]:
        """Get customer documents"""
        return await self.repo.get_customer_documents(
            customer_id=customer_id,
            document_type=document_type
        )
    
    async def get_expired_documents(
        self,
        branch_id: Optional[UUID] = None,
        days_before_expiry: int = 30
    ) -> List[CustomerDocument]:
        """Get documents expiring soon"""
        return await self.repo.get_expired_documents(
            branch_id=branch_id,
            days_before_expiry=days_before_expiry
        )
    
    # ==================== Notes Management ====================
    
    async def add_customer_note(
        self,
        customer_id: UUID,
        note_text: str,
        is_alert: bool,
        current_user: User
    ) -> CustomerNote:
        """Add note to customer"""
        logger.info(f"Adding note to customer {customer_id}")
        
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        note = CustomerNote(
            customer_id=customer_id,
            note_text=note_text,
            is_alert=is_alert,
            created_by_id=current_user.id
        )
        
        note = await self.repo.create_note(note)
        await self.db.commit()
        
        return note
    
    async def get_customer_notes(
        self,
        customer_id: UUID,
        is_alert: Optional[bool] = None
    ) -> List[CustomerNote]:
        """Get customer notes"""
        return await self.repo.get_customer_notes(
            customer_id=customer_id,
            is_alert=is_alert
        )
    
    async def update_note(
        self,
        note_id: UUID,
        note_text: Optional[str],
        is_alert: Optional[bool],
        current_user: User
    ) -> CustomerNote:
        """Update customer note"""
        note = await self.repo.get_note_by_id(note_id)
        if not note:
            raise NotFoundError(f"Note {note_id} not found")
        
        if note_text is not None:
            note.note_text = note_text
        if is_alert is not None:
            note.is_alert = is_alert
        
        note = await self.repo.update_note(note)
        await self.db.commit()
        
        return note
    
    async def delete_note(self, note_id: UUID, current_user: User) -> None:
        """Delete customer note"""
        note = await self.repo.get_note_by_id(note_id)
        if not note:
            raise NotFoundError(f"Note {note_id} not found")
        
        await self.repo.delete_note(note)
        await self.db.commit()
    
    # ==================== Statistics & Analytics ====================
    
    async def calculate_customer_stats(self, customer_id: UUID) -> Dict[str, Any]:
        """
        Calculate customer statistics
        
        Returns:
            Dictionary with transaction counts, volumes, etc.
        """
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        
        # Get transaction statistics (will be implemented with Transaction module)
        transaction_count = await self.repo.get_customer_transaction_count(customer_id)
        total_volume = await self.repo.get_customer_total_volume(customer_id)
        
        # Document statistics
        documents = await self.repo.get_customer_documents(customer_id)
        verified_docs = sum(1 for doc in documents if doc.is_verified)
        expired_docs = sum(1 for doc in documents if doc.is_expired)
        
        return {
            "customer_id": str(customer_id),
            "customer_number": customer.customer_number,
            "is_verified": customer.is_verified,
            "risk_level": customer.risk_level.value if customer.risk_level else None,
            "account_age_days": (datetime.utcnow() - customer.registered_at).days,
            "total_transactions": transaction_count,
            "total_volume": float(total_volume),
            "documents": {
                "total": len(documents),
                "verified": verified_docs,
                "expired": expired_docs
            },
            "last_transaction_date": customer.last_transaction_date.isoformat() if customer.last_transaction_date else None
        }
    
    async def get_customer_transactions(
        self,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 50,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get customer transaction history

        Args:
            customer_id: UUID of the customer
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            date_range: Optional tuple of (date_from, date_to)

        Returns:
            Dict with 'transactions' list and 'total' count
        """
        # Import here to avoid circular dependency
        from app.services.transaction_service import TransactionService

        logger.info(f"Getting transactions for customer {customer_id} (skip={skip}, limit={limit})")

        # Verify customer exists
        customer = await self.repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")

        # Build filter for transactions
        filters = TransactionFilter(
            customer_id=customer_id,
            skip=skip,
            limit=limit
        )

        # Add date range if provided
        if date_range:
            filters.date_from = date_range[0]
            filters.date_to = date_range[1]

        # Get transactions using TransactionService
        transaction_service = TransactionService(self.db)
        result = await transaction_service.list_transactions(filters, skip=skip, limit=limit)

        return result
    
    async def get_branch_customer_stats(self, branch_id: UUID) -> Dict[str, Any]:
        """Get customer statistics for a branch"""
        return await self.repo.get_branch_customer_stats(branch_id)

    async def bulk_create_customers(
        self,
        customers_data: List[Dict[str, Any]],
        current_user: User,
        branch_id: UUID
    ) -> Dict[str, Any]:
        """
        Create multiple customers in bulk

        Args:
            customers_data: List of customer creation data
            current_user: User performing the operation
            branch_id: Branch where customers are being registered

        Returns:
            Dictionary with results: total, successful, failed, errors
        """
        logger.info(f"Bulk creating {len(customers_data)} customers at branch {branch_id}")

        results = {
            "total": len(customers_data),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "created_customers": []
        }

        for idx, customer_data in enumerate(customers_data):
            try:
                # Create customer
                customer = await self.create_customer(customer_data, current_user, branch_id)
                results["successful"] += 1
                results["created_customers"].append({
                    "index": idx,
                    "customer_number": customer.customer_number,
                    "name": f"{customer.first_name} {customer.last_name}",
                    "id": str(customer.id)
                })

            except (ValidationError, DuplicateError) as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": idx,
                    "name": f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}",
                    "error": str(e)
                })
                logger.warning(f"Failed to create customer at index {idx}: {str(e)}")
                continue

        logger.info(
            f"Bulk customer creation completed: "
            f"{results['successful']} successful, {results['failed']} failed"
        )

        return results

    # ==================== Validation Helpers ====================
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Basic phone validation (customize for your region)
        pattern = r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{4,10}$'
        return bool(re.match(pattern, phone))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def _generate_unique_customer_number(self) -> str:
        """Generate unique customer number"""
        max_attempts = 10
        for _ in range(max_attempts):
            number = generate_customer_number()
            existing = await self.repo.get_by_customer_number(number)
            if not existing:
                return number
        
        raise ValidationError("Failed to generate unique customer number")
