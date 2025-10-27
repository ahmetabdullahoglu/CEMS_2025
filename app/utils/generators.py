# app/utils/generators.py
"""
ID and Number Generators
Utility functions for generating unique identifiers and numbers
"""
import random
import string
import secrets
from datetime import datetime
from typing import Optional


def generate_customer_number() -> str:
    """
    Generate unique customer number
    Format: CUS-YYMMDD-XXXX
    Example: CUS-250110-1234
    
    Returns:
        str: Generated customer number
    """
    today = datetime.now()
    date_part = today.strftime("%y%m%d")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"CUS-{date_part}-{random_part}"


def generate_transaction_reference() -> str:
    """
    Generate unique transaction reference
    Format: TXN-YYMMDDHHMMSS-XXXX
    Example: TXN-250110123045-7891
    
    Returns:
        str: Generated transaction reference
    """
    now = datetime.now()
    timestamp = now.strftime("%y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"TXN-{timestamp}-{random_part}"


def generate_branch_code(
    region: str,
    sequence: int
) -> str:
    """
    Generate branch code
    Format: [REGION_PREFIX][SEQUENCE]
    Example: IST001, ANK002
    
    Args:
        region: Region name
        sequence: Branch sequence number
        
    Returns:
        str: Generated branch code
    """
    # Extract first 3 letters of region
    region_prefix = region[:3].upper()
    return f"{region_prefix}{sequence:03d}"


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token
    
    Args:
        length: Token length in bytes
        
    Returns:
        str: Hex-encoded token
    """
    return secrets.token_hex(length)


def generate_verification_code(length: int = 6) -> str:
    """
    Generate numeric verification code
    
    Args:
        length: Code length
        
    Returns:
        str: Numeric code
    """
    return ''.join(random.choices(string.digits, k=length))


def generate_document_filename(
    customer_number: str,
    document_type: str,
    extension: str
) -> str:
    """
    Generate standardized document filename
    Format: [CUSTOMER_NUMBER]_[DOCUMENT_TYPE]_[TIMESTAMP].[EXT]
    Example: CUS-250110-1234_national_id_20250110123045.pdf
    
    Args:
        customer_number: Customer number
        document_type: Type of document
        extension: File extension (without dot)
        
    Returns:
        str: Generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_doc_type = document_type.lower().replace(" ", "_")
    return f"{customer_number}_{safe_doc_type}_{timestamp}.{extension}"
