"""
Database Models Package
Exports all database models for easy import
"""

# ==================== User & Authentication Models ====================
from app.db.models.user import User, user_branches, user_roles
from app.db.models.role import Role

# ==================== Currency Models ====================
from app.db.models.currency import Currency, ExchangeRate, ExchangeRateHistory
from app.db.models.rate_update_request import RateUpdateRequest, UpdateRequestStatus

# ==================== Future Models (will be added in next phases) ====================
# Phase 4: Branch Management
# from app.db.models.branch import Branch, BranchBalance, BranchBalanceHistory
from app.db.models.branch import (
    Branch, BranchBalance, BranchBalanceHistory, BranchAlert,
    RegionEnum, BalanceAlertType, AlertSeverity, BalanceChangeType
)

# Phase 5: Customer Management
# from app.db.models.customer import Customer, CustomerDocument, CustomerNote
# Phase 6: Transaction Management
# from app.db.models.transaction import (
#     Transaction,
#     IncomeTransaction,
#     ExpenseTransaction,
#     ExchangeTransaction,
#     TransferTransaction
# )
from app.db.models.customer import Customer, CustomerDocument, CustomerNote
# ==================== Transaction Models ====================
from app.db.models.transaction import (
    Transaction,
    IncomeTransaction,
    ExpenseTransaction,
    ExchangeTransaction,
    TransferTransaction,
    TransactionType,
    TransactionStatus,
    IncomeCategory,
    ExpenseCategory,
    TransferType,
    TransactionNumberGenerator
)
# Phase 7: Vault Management
# from app.db.models.vault import Vault, VaultBalance, VaultTransfer
# ==================== Vault Management ====================
from app.db.models.vault import (
    Vault,
    VaultBalance,
    VaultTransfer,
    VaultType,
    VaultTransferType,
    VaultTransferStatus,
    VaultTransferNumberGenerator
)
# Phase 8: Document Management
# from app.db.models.document import Document

# Phase 9: Audit & Logging
from app.db.models.audit import AuditLog

# ==================== Export All Models ====================
__all__ = [
    # User & Authentication
    "User",
    "Role",
    "user_branches",
    "user_roles",
    
    # Currency
    "Currency",
    "ExchangeRate",
    "ExchangeRateHistory",
    "RateUpdateRequest",
    "UpdateRequestStatus",
    
    # Future exports (uncomment as models are added):
    # Branch Management
    # "Branch",
    # "BranchBalance",
    # "BranchBalanceHistory",
    "Branch",
    "BranchBalance", 
    "BranchBalanceHistory",
    "BranchAlert",
    "RegionEnum",
    "BalanceAlertType",
    "AlertSeverity",
    "BalanceChangeType",
    # Customer Management
    # "Customer",
    # "CustomerDocument",
    # "CustomerNote",
    "Customer",
    "CustomerDocument", 
    "CustomerNote",
    # Transaction Management
    # "Transaction",
    # "IncomeTransaction",
    # "ExpenseTransaction",
    # "ExchangeTransaction",
    # "TransferTransaction",
     # Transactions
    "Transaction",
    "IncomeTransaction",
    "ExpenseTransaction",
    "ExchangeTransaction",
    "TransferTransaction",
    "TransactionType",
    "TransactionStatus",
    "IncomeCategory",
    "ExpenseCategory",
    "TransferType",
    "TransactionNumberGenerator",
    # Vault Management
    # "Vault",
    # "VaultBalance",
    # "VaultTransfer",
    "Vault",
    "VaultBalance",
    "VaultTransfer",
    "VaultType",
    "VaultTransferType",
    "VaultTransferStatus",
    "VaultTransferNumberGenerator",
    # Document Management
    # "Document",
    
    # Audit & Logging
    "AuditLog",
]


# ==================== Model Import Helper ====================
def get_all_models():
    """
    Get all registered models
    Useful for migrations and testing
    
    Returns:
        list: List of all model classes
    """
    return [
        User,
        Role,
        Currency,
        ExchangeRate,
        ExchangeRateHistory,
        # Add new models here as they are created
    ]


def get_model_names():
    """
    Get names of all registered models
    
    Returns:
        list: List of model names as strings
    """
    return [model.__name__ for model in get_all_models()]


# ==================== Model Metadata ====================
MODEL_METADATA = {
    # User & Authentication
    "User": {
        "table": "users",
        "description": "System users with authentication",
        "phase": 2,
    },
    "Role": {
        "table": "roles",
        "description": "User roles with permissions",
        "phase": 2,
    },
    
    # Currency
    "Currency": {
        "table": "currencies",
        "description": "Currency definitions",
        "phase": 3,
    },
    "ExchangeRate": {
        "table": "exchange_rates",
        "description": "Exchange rates between currencies",
        "phase": 3,
    },
    "ExchangeRateHistory": {
        "table": "exchange_rate_history",
        "description": "History of exchange rate changes",
        "phase": 3,
    },
    "RateUpdateRequest": {
        "table": "rate_update_requests",
        "description": "Pending exchange rate update requests for approval",
        "phase": 3,
    },
}


def get_model_info(model_name: str) -> dict:
    """
    Get metadata information about a model
    
    Args:
        model_name: Name of the model class
        
    Returns:
        dict: Model metadata or None if not found
    """
    return MODEL_METADATA.get(model_name)


# ==================== Import Verification ====================
def verify_imports():
    """
    Verify all model imports are working
    Useful for debugging import issues
    
    Returns:
        bool: True if all imports successful
    """
    try:
        models = get_all_models()
        print(f"✅ Successfully imported {len(models)} models:")
        for model in models:
            print(f"   - {model.__name__} (table: {model.__tablename__})")
        return True
    except Exception as e:
        print(f"❌ Error importing models: {str(e)}")
        return False


# ==================== Development Utilities ====================
if __name__ == "__main__":
    # Run verification when module is executed directly
    print("=" * 60)
    print("CEMS Database Models Verification")
    print("=" * 60)
    print()
    
    verify_imports()
    
    print()
    print("Model Metadata:")
    print("-" * 60)
    for model_name, info in MODEL_METADATA.items():
        print(f"{model_name}:")
        print(f"  Table: {info['table']}")
        print(f"  Description: {info['description']}")
        print(f"  Phase: {info['phase']}")
        print()