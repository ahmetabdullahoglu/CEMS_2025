"""
Schemas Package
Exports all Pydantic schemas for request/response validation
"""

# ==================== User & Authentication Schemas ====================
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    UserListResponse,
    PasswordChange,
    UserBranchAssignment,
    UserRoleAssignment,
    UserStats,
)

from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithUsers,
    RoleListResponse,
    PermissionInfo,
    PermissionsListResponse,
    DEFAULT_ROLES,
)

# ==================== Currency Schemas ====================
from app.schemas.currency import (
    # Base Currency Schemas
    CurrencyBase,
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyResponse,
    CurrencyWithRates,
    CurrencyListResponse,
    
    # Exchange Rate Schemas
    ExchangeRateBase,
    ExchangeRateCreate,
    ExchangeRateUpdate,
    ExchangeRateResponse,
    ExchangeRateWithDetails,
    ExchangeRateListResponse,
    
    # Exchange Rate History Schemas
    ExchangeRateHistoryResponse,
    ExchangeRateHistoryListResponse,
    
    # Utility Schemas
    CurrencyPairRequest,
    ExchangeCalculationRequest,
    ExchangeCalculationResponse,
    CurrentRateRequest,
    CurrentRateResponse,
    RateHistoryRequest,
    SetRateRequest,
    CurrencyStatsResponse,
    MessageResponse,
)

# ==================== Future Schemas (will be added in next phases) ====================
# Phase 4: Branch Management
# from app.schemas.branch import (
#     BranchBase,
#     BranchCreate,
#     BranchUpdate,
#     BranchResponse,
#     BranchWithBalances,
#     BranchBalanceResponse,
#     BranchListResponse,
# )
from app.schemas.branch import (
    BranchCreate, BranchUpdate, BranchResponse,
    BranchWithBalances, BranchListResponse,
    BranchBalanceResponse, SetThresholdsRequest,
    ReconcileBalanceRequest, BranchStatistics
)
# Phase 5: Customer Management
# from app.schemas.customer import (
#     CustomerBase,
#     CustomerCreate,
#     CustomerUpdate,
#     CustomerResponse,
#     CustomerWithDocuments,
#     CustomerListResponse,
# )

# Phase 6: Transaction Management
# from app.schemas.transaction import (
#     TransactionBase,
#     IncomeTransactionCreate,
#     ExpenseTransactionCreate,
#     ExchangeTransactionCreate,
#     TransferTransactionCreate,
#     TransactionResponse,
#     TransactionListResponse,
# )
# ==================== Transaction Schemas ====================
from app.schemas.transaction import (
    # Enums
    TransactionTypeEnum,
    TransactionStatusEnum,
    IncomeCategoryEnum,
    ExpenseCategoryEnum,
    TransferTypeEnum,
    
    # Income
    IncomeTransactionCreate,
    IncomeTransactionResponse,
    
    # Expense
    ExpenseTransactionCreate,
    ExpenseTransactionResponse,
    ExpenseApprovalRequest,
    
    # Exchange
    ExchangeTransactionCreate,
    ExchangeTransactionResponse,
    ExchangeCalculationRequest,
    ExchangeCalculationResponse,
    
    # Transfer
    TransferTransactionCreate,
    TransferTransactionResponse,
    TransferReceiptRequest,
    
    # Common
    TransactionCancelRequest,
    TransactionFilter,
    TransactionListResponse,
    TransactionSummary,
)
# Phase 7: Vault Management
# from app.schemas.vault import (
#     VaultBase,
#     VaultResponse,
#     VaultTransferCreate,
#     VaultTransferResponse,
# )

# ==================== Common/Shared Schemas ====================
from app.schemas.common import (
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
)


# ==================== Export All Schemas ====================
__all__ = [
    # ==================== User & Authentication ====================
    # User Schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserListResponse",
    "PasswordChange",
    "UserBranchAssignment",
    "UserRoleAssignment",
    "UserStats",
    
    # Role Schemas
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithUsers",
    "RoleListResponse",
    "PermissionInfo",
    "PermissionsListResponse",
    "DEFAULT_ROLES",
    
    # ==================== Currency ====================
    # Currency Schemas
    "CurrencyBase",
    "CurrencyCreate",
    "CurrencyUpdate",
    "CurrencyResponse",
    "CurrencyWithRates",
    "CurrencyListResponse",
    
    # Exchange Rate Schemas
    "ExchangeRateBase",
    "ExchangeRateCreate",
    "ExchangeRateUpdate",
    "ExchangeRateResponse",
    "ExchangeRateWithDetails",
    "ExchangeRateListResponse",
    
    # Exchange Rate History
    "ExchangeRateHistoryResponse",
    "ExchangeRateHistoryListResponse",
    
    # Utility Schemas
    "CurrencyPairRequest",
    "ExchangeCalculationRequest",
    "ExchangeCalculationResponse",
    "CurrentRateRequest",
    "CurrentRateResponse",
    "RateHistoryRequest",
    "SetRateRequest",
    "CurrencyStatsResponse",
    "MessageResponse",
    
    # ==================== Common/Shared ====================
    "PaginationParams",
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    
    # Future schemas (will be uncommented as they are added)
    # Branch Management
    # "BranchBase",
    # "BranchCreate",
    # "BranchUpdate",
    # "BranchResponse",
    # "BranchWithBalances",
    # "BranchBalanceResponse",
    # "BranchListResponse",
    "BranchCreate",
    "BranchUpdate",
    "BranchResponse",
    "BranchWithBalances",
    "BranchBalanceResponse",
    # Customer Management
    # "CustomerBase",
    # "CustomerCreate",
    # "CustomerUpdate",
    # "CustomerResponse",
    # "CustomerWithDocuments",
    # "CustomerListResponse",
    
    # Transaction Management
    # "TransactionBase",
    # "IncomeTransactionCreate",
    # "ExpenseTransactionCreate",
    # "ExchangeTransactionCreate",
    # "TransferTransactionCreate",
    # "TransactionResponse",
    # "TransactionListResponse",
    # Transaction Schemas
    "TransactionTypeEnum",
    "TransactionStatusEnum",
    "IncomeCategoryEnum",
    "ExpenseCategoryEnum",
    "TransferTypeEnum",
    "IncomeTransactionCreate",
    "IncomeTransactionResponse",
    "ExpenseTransactionCreate",
    "ExpenseTransactionResponse",
    "ExpenseApprovalRequest",
    "ExchangeTransactionCreate",
    "ExchangeTransactionResponse",
    "ExchangeCalculationRequest",
    "ExchangeCalculationResponse",
    "TransferTransactionCreate",
    "TransferTransactionResponse",
    "TransferReceiptRequest",
    "TransactionCancelRequest",
    "TransactionFilter",
    "TransactionListResponse",
    "TransactionSummary",
    # Vault Management
    # "VaultBase",
    # "VaultResponse",
    # "VaultTransferCreate",
    # "VaultTransferResponse",
    "UserAssignmentRequest",
    "BranchUsersResponse",
    "BalanceHistoryRecord",
    "BalanceHistoryResponse",
    "BalanceHistoryFilter",
    "AlertStatistics",
    "ReconciliationHistory",
    "CurrencyBalanceSummary",
    "ReconciliationRequest",
    "ReconciliationResponse"
]


# ==================== Schema Categories ====================
SCHEMA_CATEGORIES = {
    "authentication": [
        "UserCreate", "UserUpdate", "UserResponse", "PasswordChange",
        "RoleCreate", "RoleUpdate", "RoleResponse",
    ],
    "currency": [
        "CurrencyCreate", "CurrencyUpdate", "CurrencyResponse",
        "ExchangeRateCreate", "ExchangeRateUpdate", "ExchangeRateResponse",
    ],
    # Add more categories as schemas are added
}


def get_schemas_by_category(category: str) -> list:
    """
    Get all schema names for a specific category
    
    Args:
        category: Category name (e.g., 'authentication', 'currency')
        
    Returns:
        list: List of schema names in that category
    """
    return SCHEMA_CATEGORIES.get(category, [])


def list_all_schemas():
    """
    List all available schemas
    Useful for documentation and testing
    
    Returns:
        dict: Dictionary of categories and their schemas
    """
    return SCHEMA_CATEGORIES


# ==================== Development Utilities ====================
if __name__ == "__main__":
    # Run when module is executed directly
    print("=" * 60)
    print("CEMS Pydantic Schemas Verification")
    print("=" * 60)
    print()
    
    print(f"Total schemas exported: {len(__all__)}")
    print()
    
    print("Schema Categories:")
    print("-" * 60)
    for category, schemas in SCHEMA_CATEGORIES.items():
        print(f"\n{category.upper()}:")
        for schema in schemas:
            print(f"  - {schema}")
    print()