# app/api/v1/endpoints/customers.py
"""
Customer API Endpoints
RESTful API for customer management, KYC, and document handling

Phase 5.2: Customer Service & API
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_db as get_db
from app.db.models.user import User
from app.db.models.customer import CustomerType, RiskLevel, DocumentType
from app.api.deps import get_current_active_user, get_current_superuser
from app.services.customer_service import CustomerService
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerDetailResponse,  # ⬅️ حذفنا CustomerListResponse
    CustomerDocumentCreate, CustomerDocumentResponse,
    CustomerNoteCreate, CustomerNoteResponse,
    CustomerKYCVerification
)
from app.schemas.common import PaginatedResponse, paginated, BulkOperationResponse
from app.core.exceptions import NotFoundError, ValidationError, DuplicateError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Customers"])


# ==================== Customer CRUD ====================

@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Customer"
)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Register a new customer
    
    **Required Fields:**
    - first_name, last_name
    - phone_number
    - Either national_id or passport_number
    - branch_id (customer's primary branch)
    
    **Optional Fields:**
    - name_ar (Arabic name)
    - email
    - date_of_birth
    - nationality
    - address, city, country
    - customer_type (default: individual)
    
    **Permissions:** Authenticated user with customer:create permission
    """
    try:
        logger.info(f"Creating customer by user {current_user.id}")
        
        service = CustomerService(db)
        customer = await service.create_customer(
            customer_data=customer_data.dict(exclude_unset=True),
            current_user=current_user,
            branch_id=customer_data.branch_id
        )
        
        logger.info(f"Customer created: {customer.customer_number}")
        return customer
        
    except DuplicateError as e:
        logger.warning(f"Duplicate customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )


@router.post(
    "/bulk",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Create Customers"
)
async def bulk_create_customers(
    customers: List[CustomerCreate],
    branch_id: UUID = Query(..., description="Branch ID where all customers will be registered"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create multiple customers in a single request

    **Required Fields for each customer:**
    - first_name, last_name
    - phone_number
    - Either national_id or passport_number

    **Note:** All customers will be registered to the same branch specified in branch_id query parameter

    **Response:**
    Returns summary of successful and failed creations with error details

    **Permissions:** Authenticated user with customer:create permission

    **Example Request:**
    ```json
    [
      {
        "first_name": "Ahmed",
        "last_name": "Ali",
        "phone_number": "+966501234567",
        "national_id": "1234567890",
        "email": "ahmed@example.com",
        "customer_type": "individual"
      },
      {
        "first_name": "Sarah",
        "last_name": "Mohammed",
        "phone_number": "+966501234568",
        "passport_number": "P12345678",
        "email": "sarah@example.com",
        "customer_type": "individual"
      }
    ]
    ```
    """
    try:
        if not customers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customers list cannot be empty"
            )

        if len(customers) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create more than 100 customers at once"
            )

        logger.info(f"Bulk creating {len(customers)} customers at branch {branch_id} by user {current_user.id}")

        service = CustomerService(db)
        customers_data = [customer.dict(exclude_unset=True) for customer in customers]
        results = await service.bulk_create_customers(customers_data, current_user, branch_id)

        logger.info(
            f"Bulk customer creation completed: "
            f"{results['successful']} successful, {results['failed']} failed"
        )

        return BulkOperationResponse(
            total=results["total"],
            successful=results["successful"],
            failed=results["failed"],
            errors=results["errors"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk customer creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create customers"
        )


@router.get(
    "",
    response_model=PaginatedResponse[CustomerResponse],  # ⬅️ هنا
    summary="Search/List Customers"
)
async def search_customers(
    query: Optional[str] = Query(None, description="Search text (name, phone, ID)"),
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    customer_type: Optional[CustomerType] = Query(None, description="Filter by type"),
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk level"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    is_active: bool = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=100, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search and list customers with advanced filtering
    
    **Search Capabilities:**
    - Full-text search across: name, phone, email, national_id, passport, customer_number
    - Filter by branch, type, risk level, verification status
    - Pagination support
    
    **Query Parameters:**
    - query: Search text (searches multiple fields)
    - branch_id: Filter customers by branch
    - customer_type: individual or corporate
    - risk_level: low, medium, high
    - is_verified: KYC verification status
    - is_active: Show only active customers
    - skip, limit: Pagination
    
    **Returns:**
    - customers: List of customer records
    - total: Total count matching filters
    - skip, limit: Pagination parameters
    
    **Permissions:** Any authenticated user
    """
    try:
        logger.info(f"Searching customers: query='{query}', branch={branch_id}")
        
        service = CustomerService(db)
        customers, total = await service.search_customers(
            query=query,
            branch_id=branch_id,
            customer_type=customer_type,
            risk_level=risk_level,
            is_verified=is_verified,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        return paginated(customers, total, skip, limit)
        
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search customers"
        )


@router.get(
    "/{customer_id}",
    response_model=CustomerDetailResponse,
    summary="Get Customer Details"
)
async def get_customer(
    customer_id: UUID,
    include_documents: bool = Query(False, description="Include documents"),
    include_notes: bool = Query(False, description="Include notes"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed customer information
    
    **Path Parameters:**
    - customer_id: UUID of the customer
    
    **Query Parameters:**
    - include_documents: Include customer documents in response
    - include_notes: Include customer notes in response
    
    **Returns:**
    - Complete customer information
    - Optional: documents and notes if requested
    
    **Permissions:** Authenticated user
    """
    try:
        service = CustomerService(db)
        customer = await service.get_customer_by_id(
            customer_id=customer_id,
            include_documents=include_documents,
            include_notes=include_notes
        )

        # Convert to dict to avoid lazy loading issues
        customer_dict = {
            "id": customer.id,
            "customer_number": customer.customer_number,
            "customer_type": customer.customer_type,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "name_ar": customer.name_ar if hasattr(customer, 'name_ar') else None,
            "date_of_birth": customer.date_of_birth,
            "nationality": customer.nationality,
            "national_id": customer.national_id,
            "passport_number": customer.passport_number,
            "phone_number": customer.phone_number,
            "email": customer.email,
            "address": customer.address,
            "city": customer.city,
            "country": customer.country,
            "is_verified": customer.is_verified,
            "verified_at": customer.verified_at,
            "risk_level": customer.risk_level,
            "is_active": customer.is_active,
            "branch_id": customer.branch_id,
            "registered_by_id": customer.registered_by_id,
            "verified_by_id": customer.verified_by_id if hasattr(customer, 'verified_by_id') else None,
            "registered_at": customer.registered_at,
            "last_transaction_date": customer.last_transaction_date if hasattr(customer, 'last_transaction_date') else None,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at,
            "additional_info": customer.additional_info if hasattr(customer, 'additional_info') else None,
            # Include documents only if explicitly requested (and eagerly loaded)
            "documents": [
                {
                    "id": doc.id,
                    "customer_id": doc.customer_id,
                    "document_type": doc.document_type,
                    "document_number": doc.document_number,
                    "document_url": doc.document_url,
                    "issue_date": doc.issue_date,
                    "expiry_date": doc.expiry_date,
                    "is_verified": doc.is_verified,
                    "verified_by_id": doc.verified_by_id,
                    "verified_at": doc.verified_at,
                    "verification_notes": doc.verification_notes,
                    "uploaded_by_id": doc.uploaded_by_id,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at
                }
                for doc in customer.documents
            ] if include_documents else [],
            # Include notes only if explicitly requested (and eagerly loaded)
            "notes": [
                {
                    "id": note.id,
                    "customer_id": note.customer_id,
                    "note_text": note.note_text,
                    "is_alert": note.is_alert,
                    "created_by_id": note.created_by_id,
                    "created_at": note.created_at,
                    "updated_at": note.updated_at
                }
                for note in customer.notes
            ] if include_notes else [],
            "total_transactions": 0  # TODO: Calculate from transactions
        }

        return customer_dict

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer"
        )


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update Customer"
)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update customer information
    
    **Updatable Fields:**
    - Basic info: first_name, last_name, name_ar
    - Contact: phone_number, email
    - Address: address, city, country
    - Type: customer_type
    - Additional info: additional_info (JSONB)
    
    **Non-Updatable Fields:**
    - customer_number
    - national_id, passport_number
    - branch_id (requires separate transfer)
    - Verification fields (use verification endpoint)
    
    **Permissions:** Authenticated user with customer:update permission
    """
    try:
        service = CustomerService(db)
        customer = await service.update_customer(
            customer_id=customer_id,
            update_data=customer_data.dict(exclude_unset=True),
            current_user=current_user
        )
        
        logger.info(f"Customer {customer_id} updated by user {current_user.id}")
        return customer
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer"
        )


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate Customer"
)
async def deactivate_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Deactivate customer account (soft delete)
    
    **Note:** This does not permanently delete the customer.
    It sets is_active = False, preserving all historical data.
    
    **Permissions:** Admin only
    """
    try:
        service = CustomerService(db)
        await service.deactivate_customer(
            customer_id=customer_id,
            current_user=current_user
        )
        
        logger.info(f"Customer {customer_id} deactivated by admin {current_user.id}")
        return None
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deactivating customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate customer"
        )


# ==================== KYC & Verification ====================

@router.post(
    "/{customer_id}/verify",
    response_model=CustomerResponse,
    summary="Verify Customer KYC"
)
async def verify_customer_kyc(
    customer_id: UUID,
    verification_data: CustomerKYCVerification,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify customer KYC status
    
    **Required:**
    - risk_level: Assessed risk level (low, medium, high)
    
    **Optional:**
    - verification_notes: Notes about the verification process
    
    **Prerequisites:**
    - Customer must have uploaded documents
    - Documents should be verified
    
    **Permissions:** User with customer:verify permission (manager or admin)
    """
    try:
        service = CustomerService(db)
        customer = await service.verify_customer_kyc(
            customer_id=customer_id,
            risk_level=verification_data.risk_level,
            verification_notes=verification_data.verification_notes,
            current_user=current_user
        )
        
        logger.info(f"Customer {customer_id} KYC verified by user {current_user.id}")
        return customer
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying KYC for customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify KYC"
        )


# ==================== Customer Statistics ====================

@router.get(
    "/{customer_id}/stats",
    summary="Get Customer Statistics"
)
async def get_customer_stats(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get customer statistics and analytics
    
    **Returns:**
    - Account age
    - Transaction count and volume
    - Document statistics
    - Verification status
    - Risk level
    
    **Permissions:** Authenticated user
    """
    try:
        service = CustomerService(db)
        stats = await service.calculate_customer_stats(customer_id)
        
        return stats
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting stats for customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get(
    "/{customer_id}/transactions",
    summary="Get Customer Transactions"
)
async def get_customer_transactions(
    customer_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get customer transaction history

    Returns paginated list of all transactions for the specified customer.

    **Permissions:** Authenticated user
    """
    try:
        service = CustomerService(db)
        result = await service.get_customer_transactions(
            customer_id=customer_id,
            skip=skip,
            limit=limit
        )

        return {
            "customer_id": str(customer_id),
            "transactions": result["transactions"],
            "total": result["total"]
        }

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting transactions for customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions"
        )


# ==================== Document Management ====================

@router.post(
    "/{customer_id}/documents",
    response_model=CustomerDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Customer Document"
)
async def upload_customer_document(
    customer_id: UUID,
    document_data: CustomerDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload document for customer
    
    **Required Fields:**
    - document_type: Type of document (national_id, passport, etc.)
    - document_url: File path or S3 key
    
    **Optional Fields:**
    - document_number
    - issue_date
    - expiry_date
    
    **Document Types:**
    - national_id: National ID card
    - passport: Passport
    - driving_license: Driver's license
    - utility_bill: Utility bill (proof of address)
    - bank_statement: Bank statement
    - commercial_registration: Commercial registration (for corporate)
    - tax_certificate: Tax certificate
    - other: Other documents
    
    **Note:** Actual file upload handling should be implemented separately
    This endpoint records document metadata after file is uploaded to storage
    
    **Permissions:** Authenticated user with document:upload permission
    """
    try:
        service = CustomerService(db)
        document = await service.add_customer_document(
            customer_id=customer_id,
            document_type=document_data.document_type,
            document_url=document_data.document_url,
            document_number=document_data.document_number,
            issue_date=document_data.issue_date,
            expiry_date=document_data.expiry_date,
            current_user=current_user
        )
        
        logger.info(f"Document uploaded for customer {customer_id}")
        return document
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading document for customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get(
    "/{customer_id}/documents",
    response_model=List[CustomerDocumentResponse],
    summary="Get Customer Documents"
)
async def get_customer_documents(
    customer_id: UUID,
    document_type: Optional[DocumentType] = Query(None, description="Filter by type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all documents for a customer
    
    **Query Parameters:**
    - document_type: Filter documents by type
    
    **Permissions:** Authenticated user
    """
    try:
        service = CustomerService(db)
        documents = await service.get_customer_documents(
            customer_id=customer_id,
            document_type=document_type
        )
        
        return documents
        
    except Exception as e:
        logger.error(f"Error getting documents for customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.put(
    "/documents/{document_id}/verify",
    response_model=CustomerDocumentResponse,
    summary="Verify Document"
)
async def verify_document(
    document_id: UUID,
    is_verified: bool,
    verification_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify customer document
    
    **Parameters:**
    - is_verified: Verification status (true/false)
    - verification_notes: Optional notes about verification
    
    **Permissions:** User with document:verify permission (manager or admin)
    """
    try:
        service = CustomerService(db)
        document = await service.verify_document(
            document_id=document_id,
            is_verified=is_verified,
            verification_notes=verification_notes,
            current_user=current_user
        )
        
        logger.info(f"Document {document_id} verified by user {current_user.id}")
        return document
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify document"
        )


# ==================== Notes Management ====================

@router.post(
    "/{customer_id}/notes",
    response_model=CustomerNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Customer Note"
)
async def add_customer_note(
    customer_id: UUID,
    note_data: CustomerNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add note to customer record
    
    **Fields:**
    - note_text: Note content
    - is_alert: Whether this is an important alert (default: false)
    
    **Use Cases:**
    - Record important information about customer
    - Flag suspicious activity
    - Document KYC decisions
    - Communication history
    
    **Permissions:** Authenticated user
    """
    try:
        service = CustomerService(db)
        note = await service.add_customer_note(
            customer_id=customer_id,
            note_text=note_data.note_text,
            is_alert=note_data.is_alert,
            current_user=current_user
        )
        
        logger.info(f"Note added to customer {customer_id}")
        return note
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding note to customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add note"
        )


@router.get(
    "/{customer_id}/notes",
    response_model=List[CustomerNoteResponse],
    summary="Get Customer Notes"
)
async def get_customer_notes(
    customer_id: UUID,
    is_alert: Optional[bool] = Query(None, description="Filter by alert status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all notes for a customer
    
    **Query Parameters:**
    - is_alert: Filter to show only alerts (true) or only regular notes (false)
    
    **Permissions:** Authenticated user
    """
    try:
        service = CustomerService(db)
        notes = await service.get_customer_notes(
            customer_id=customer_id,
            is_alert=is_alert
        )
        
        return notes
        
    except Exception as e:
        logger.error(f"Error getting notes for customer {customer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notes"
        )
