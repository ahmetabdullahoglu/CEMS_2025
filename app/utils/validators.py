# app/utils/validators.py
"""
Validation Utilities
Common validation functions for business logic
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import date
import re

from app.core.exceptions import ValidationError


def validate_positive_amount(
    amount: Decimal,
    field_name: str = "amount",
    min_value: Optional[Decimal] = None,
    max_value: Optional[Decimal] = None
) -> Decimal:
    """Validate amount is positive and within range"""
    if amount <= 0:
        raise ValidationError(f"{field_name} must be positive (got: {amount})")
    
    if min_value is not None and amount <= min_value:
        raise ValidationError(f"{field_name} must be greater than {min_value}")
    
    if max_value is not None and amount > max_value:
        raise ValidationError(f"{field_name} must not exceed {max_value}")
    
    return amount


def validate_transaction_limits(
    amount: Decimal,
    transaction_type: str,
    max_single: Optional[Decimal] = None,
    max_daily: Optional[Decimal] = None
) -> Dict[str, Any]:
    """Validate transaction amount against limits"""
    if max_single is None:
        max_single = Decimal('1000000.00')
    
    if max_daily is None:
        max_daily = Decimal('5000000.00')
    
    if amount > max_single:
        raise ValidationError(
            f"Transaction amount ({amount}) exceeds maximum "
            f"({max_single}) for {transaction_type}"
        )
    
    return {
        'valid': True,
        'amount': float(amount),
        'max_single': float(max_single),
        'max_daily': float(max_daily)
    }


def validate_phone_number(phone: str, country_code: str = "SA") -> str:
    """Validate phone number format"""
    phone = phone.replace(" ", "").replace("-", "")
    
    if country_code == "SA":
        if phone.startswith("+966"):
            phone = phone[4:]
        elif phone.startswith("00966"):
            phone = phone[5:]
        
        if not (phone.startswith("5") and len(phone) in [9, 10]):
            raise ValidationError(f"Invalid Saudi phone: {phone}")
        
        if not phone.isdigit():
            raise ValidationError(f"Phone must be digits: {phone}")
    
    return phone


def validate_email(email: str) -> str:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email: {email}")
    return email.lower()


def validate_branch_code(code: str) -> str:
    """Validate branch code format (BR001, BR002, etc.)"""
    if not code.startswith('BR'):
        raise ValidationError(f"Branch code must start with 'BR': {code}")
    
    suffix = code[2:]
    if not suffix.isdigit():
        raise ValidationError(f"Branch code must have numeric suffix: {code}")
    
    if len(suffix) < 3:
        raise ValidationError(f"Branch code suffix must be 3+ digits: {code}")
    
    return code.upper()


def validate_national_id(national_id: str, country: str = "SA") -> str:
    """Validate national ID format"""
    if country == "SA":
        if not national_id.isdigit():
            raise ValidationError(f"National ID must be digits: {national_id}")
        
        if len(national_id) != 10:
            raise ValidationError(f"National ID must be 10 digits: {national_id}")
        
        if not national_id.startswith(('1', '2')):
            raise ValidationError(f"National ID must start with 1 or 2: {national_id}")
    
    return national_id


def validate_date_not_future(date_value: date, field_name: str = "date") -> date:
    """Validate date is not in the future"""
    if date_value > date.today():
        raise ValidationError(f"{field_name} cannot be in future: {date_value}")
    return date_value


def validate_exchange_rate(
    rate: Decimal,
    min_rate: Decimal = Decimal('0.0001'),
    max_rate: Decimal = Decimal('1000000')
) -> Decimal:
    """Validate exchange rate is within bounds"""
    if rate <= 0:
        raise ValidationError(f"Exchange rate must be positive: {rate}")
    
    if rate < min_rate:
        raise ValidationError(f"Rate too low: {rate} (min: {min_rate})")
    
    if rate > max_rate:
        raise ValidationError(f"Rate too high: {rate} (max: {max_rate})")
    
    return rate


__all__ = [
    'validate_positive_amount',
    'validate_transaction_limits',
    'validate_phone_number',
    'validate_email',
    'validate_branch_code',
    'validate_national_id',
    'validate_date_not_future',
    'validate_exchange_rate',
]
