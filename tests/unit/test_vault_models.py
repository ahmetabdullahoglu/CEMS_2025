# tests/unit/test_vault_models.py
"""
Unit Tests for Vault Models
============================
Tests for vault models, relationships, and constraints
"""

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.vault import (
    Vault, VaultBalance, VaultTransfer,
    VaultType, TransferType, TransferStatus,
    VaultTransferNumberGenerator
)
from app.db.models.branch import Branch
from app.db.models.currency import Currency
from app.db.models.user import User


# ==================== FIXTURES ====================

@pytest.fixture
def db_session():
    """Create a test database session"""
    # This would be properly configured in conftest.py
    # For now, this is a placeholder
    pass


@pytest.fixture
def test_currency(db_session):
    """Create a test currency"""
    currency = Currency(
        code="USD",
        name_en="US Dollar",
        name_ar="الدولار الأمريكي",
        symbol="$",
        is_base=True,
        is_active=True
    )
    db_session.add(currency)
    db_session.commit()
    return currency


@pytest.fixture
def test_branch(db_session):
    """Create a test branch"""
    branch = Branch(
        code="BR001",
        name_en="Test Branch",
        name_ar="فرع تجريبي",
        is_active=True
    )
    db_session.add(branch)
    db_session.commit()
    return branch


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


# ==================== VAULT MODEL TESTS ====================

class TestVaultModel:
    """Tests for Vault model"""
    
    def test_create_main_vault(self, db_session):
        """Test creating a main vault"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            branch_id=None,
            is_active=True,
            description="Central main vault",
            location="Main Office - Vault Room"
        )
        
        db_session.add(vault)
        db_session.commit()
        
        assert vault.id is not None
        assert vault.vault_code == "VLT-MAIN"
        assert vault.vault_type == VaultType.MAIN
        assert vault.branch_id is None
        assert vault.is_active is True
    
    def test_create_branch_vault(self, db_session, test_branch):
        """Test creating a branch vault"""
        vault = Vault(
            vault_code=f"VLT-{test_branch.code}",
            name=f"{test_branch.name_en} Vault",
            vault_type=VaultType.BRANCH,
            branch_id=test_branch.id,
            is_active=True
        )
        
        db_session.add(vault)
        db_session.commit()
        
        assert vault.id is not None
        assert vault.vault_type == VaultType.BRANCH
        assert vault.branch_id == test_branch.id
        assert vault.branch == test_branch
    
    def test_main_vault_without_branch_id(self, db_session):
        """Test that main vault cannot have branch_id"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            branch_id=uuid4(),  # Should be NULL
            is_active=True
        )
        
        db_session.add(vault)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_branch_vault_requires_branch_id(self, db_session):
        """Test that branch vault requires branch_id"""
        vault = Vault(
            vault_code="VLT-BR001",
            name="Branch Vault",
            vault_type=VaultType.BRANCH,
            branch_id=None,  # Should not be NULL
            is_active=True
        )
        
        db_session.add(vault)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_unique_vault_code(self, db_session):
        """Test that vault_code must be unique"""
        vault1 = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault 1",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        vault2 = Vault(
            vault_code="VLT-MAIN",  # Duplicate
            name="Main Vault 2",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        
        db_session.add(vault1)
        db_session.commit()
        
        db_session.add(vault2)
        with pytest.raises(IntegrityError):
            db_session.commit()


# ==================== VAULT BALANCE MODEL TESTS ====================

class TestVaultBalanceModel:
    """Tests for VaultBalance model"""
    
    def test_create_vault_balance(self, db_session, test_currency):
        """Test creating a vault balance"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        balance = VaultBalance(
            vault_id=vault.id,
            currency_id=test_currency.id,
            balance=Decimal('10000.00'),
            last_updated=datetime.utcnow()
        )
        
        db_session.add(balance)
        db_session.commit()
        
        assert balance.id is not None
        assert balance.vault_id == vault.id
        assert balance.currency_id == test_currency.id
        assert balance.balance == Decimal('10000.00')
    
    def test_balance_cannot_be_negative(self, db_session, test_currency):
        """Test that balance cannot be negative"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        balance = VaultBalance(
            vault_id=vault.id,
            currency_id=test_currency.id,
            balance=Decimal('-100.00'),  # Negative balance
            last_updated=datetime.utcnow()
        )
        
        db_session.add(balance)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_unique_vault_currency_combination(self, db_session, test_currency):
        """Test that vault+currency combination must be unique"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        balance1 = VaultBalance(
            vault_id=vault.id,
            currency_id=test_currency.id,
            balance=Decimal('10000.00')
        )
        balance2 = VaultBalance(
            vault_id=vault.id,
            currency_id=test_currency.id,  # Duplicate combination
            balance=Decimal('5000.00')
        )
        
        db_session.add(balance1)
        db_session.commit()
        
        db_session.add(balance2)
        with pytest.raises(IntegrityError):
            db_session.commit()


# ==================== VAULT TRANSFER MODEL TESTS ====================

class TestVaultTransferModel:
    """Tests for VaultTransfer model"""
    
    def test_create_vault_to_vault_transfer(self, db_session, test_currency, test_user):
        """Test creating a vault-to-vault transfer"""
        from_vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        to_vault = Vault(
            vault_code="VLT-BACKUP",
            name="Backup Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add_all([from_vault, to_vault])
        db_session.flush()
        
        transfer = VaultTransfer(
            transfer_number="VTR-20250109-00001",
            from_vault_id=from_vault.id,
            to_vault_id=to_vault.id,
            to_branch_id=None,
            currency_id=test_currency.id,
            amount=Decimal('5000.00'),
            transfer_type=TransferType.VAULT_TO_VAULT,
            status=TransferStatus.PENDING,
            initiated_by=test_user.id,
            initiated_at=datetime.utcnow(),
            notes="Test transfer"
        )
        
        db_session.add(transfer)
        db_session.commit()
        
        assert transfer.id is not None
        assert transfer.transfer_number == "VTR-20250109-00001"
        assert transfer.amount == Decimal('5000.00')
        assert transfer.status == TransferStatus.PENDING
    
    def test_create_vault_to_branch_transfer(self, db_session, test_currency, test_branch, test_user):
        """Test creating a vault-to-branch transfer"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        transfer = VaultTransfer(
            transfer_number="VTR-20250109-00002",
            from_vault_id=vault.id,
            to_vault_id=None,
            to_branch_id=test_branch.id,
            currency_id=test_currency.id,
            amount=Decimal('3000.00'),
            transfer_type=TransferType.VAULT_TO_BRANCH,
            status=TransferStatus.PENDING,
            initiated_by=test_user.id,
            initiated_at=datetime.utcnow()
        )
        
        db_session.add(transfer)
        db_session.commit()
        
        assert transfer.to_vault_id is None
        assert transfer.to_branch_id == test_branch.id
    
    def test_transfer_amount_must_be_positive(self, db_session, test_currency, test_user):
        """Test that transfer amount must be positive"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        transfer = VaultTransfer(
            transfer_number="VTR-20250109-00003",
            from_vault_id=vault.id,
            to_vault_id=vault.id,
            currency_id=test_currency.id,
            amount=Decimal('-100.00'),  # Negative amount
            transfer_type=TransferType.VAULT_TO_VAULT,
            status=TransferStatus.PENDING,
            initiated_by=test_user.id
        )
        
        db_session.add(transfer)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_transfer_destination_check(self, db_session, test_currency, test_user):
        """Test that transfer must have either to_vault_id or to_branch_id, not both"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        # Both NULL - should fail
        transfer1 = VaultTransfer(
            transfer_number="VTR-20250109-00004",
            from_vault_id=vault.id,
            to_vault_id=None,
            to_branch_id=None,
            currency_id=test_currency.id,
            amount=Decimal('1000.00'),
            transfer_type=TransferType.VAULT_TO_BRANCH,
            status=TransferStatus.PENDING,
            initiated_by=test_user.id
        )
        
        db_session.add(transfer1)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_unique_transfer_number(self, db_session, test_currency, test_user):
        """Test that transfer_number must be unique"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        transfer1 = VaultTransfer(
            transfer_number="VTR-20250109-00005",
            from_vault_id=vault.id,
            to_vault_id=vault.id,
            currency_id=test_currency.id,
            amount=Decimal('1000.00'),
            transfer_type=TransferType.VAULT_TO_VAULT,
            status=TransferStatus.PENDING,
            initiated_by=test_user.id
        )
        transfer2 = VaultTransfer(
            transfer_number="VTR-20250109-00005",  # Duplicate
            from_vault_id=vault.id,
            to_vault_id=vault.id,
            currency_id=test_currency.id,
            amount=Decimal('2000.00'),
            transfer_type=TransferType.VAULT_TO_VAULT,
            status=TransferStatus.PENDING,
            initiated_by=test_user.id
        )
        
        db_session.add(transfer1)
        db_session.commit()
        
        db_session.add(transfer2)
        with pytest.raises(IntegrityError):
            db_session.commit()


# ==================== TRANSFER NUMBER GENERATOR TESTS ====================

class TestVaultTransferNumberGenerator:
    """Tests for VaultTransferNumberGenerator"""
    
    def test_generate_first_transfer_number(self, db_session):
        """Test generating the first transfer number for a date"""
        number = VaultTransferNumberGenerator.generate(
            db_session,
            datetime(2025, 1, 9)
        )
        
        assert number == "VTR-20250109-00001"
    
    def test_generate_sequential_transfer_numbers(self, db_session, test_currency, test_user):
        """Test generating sequential transfer numbers"""
        vault = Vault(
            vault_code="VLT-MAIN",
            name="Main Vault",
            vault_type=VaultType.MAIN,
            is_active=True
        )
        db_session.add(vault)
        db_session.flush()
        
        # Create first transfer
        transfer1 = VaultTransfer(
            transfer_number=VaultTransferNumberGenerator.generate(
                db_session,
                datetime(2025, 1, 9)
            ),
            from_vault_id=vault.id,
            to_vault_id=vault.id,
            currency_id=test_currency.id,
            amount=Decimal('1000.00'),
            transfer_type=TransferType.VAULT_TO_VAULT,
            status=TransferStatus.PENDING,
            initiated_by=test_user.id
        )
        db_session.add(transfer1)
        db_session.commit()
        
        # Generate second number
        number2 = VaultTransferNumberGenerator.generate(
            db_session,
            datetime(2025, 1, 9)
        )
        
        assert transfer1.transfer_number == "VTR-20250109-00001"
        assert number2 == "VTR-20250109-00002"
