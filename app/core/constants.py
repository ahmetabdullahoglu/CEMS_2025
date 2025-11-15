"""
CEMS Constants and Enumerations
Defines all constant values and enums used throughout the application
"""

from enum import Enum


# ==================== User & Authentication ====================

class UserRole(str, Enum):
    """User role types with hierarchical permissions"""
    ADMIN = "admin"
    MANAGER = "manager"
    TELLER = "teller"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"


# ==================== Branch Management ====================

class BranchRegion(str, Enum):
    """Geographic regions for branches"""
    ISTANBUL_EUROPEAN = "istanbul_european"
    ISTANBUL_ASIAN = "istanbul_asian"
    ANKARA = "ankara"
    IZMIR = "izmir"
    ANTALYA = "antalya"
    OTHER = "other"


class BranchStatus(str, Enum):
    """Branch operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"


# ==================== Transactions ====================

class TransactionType(str, Enum):
    """Types of financial transactions"""
    INCOME = "income"
    EXPENSE = "expense"
    EXCHANGE = "exchange"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    """Transaction lifecycle states"""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REVERSED = "reversed"


class IncomeCategory(str, Enum):
    """Income source categories shared across API, DB and scripts"""

    SERVICE_FEE = "service_fee"
    EXCHANGE_COMMISSION = "exchange_commission"
    TRANSFER_FEE = "transfer_fee"
    COMMISSION = "commission"  # Legacy generic commission bucket
    INTEREST = "interest"
    OTHER = "other"


class ExpenseCategory(str, Enum):
    """Expense type categories shared across API, DB and scripts"""

    RENT = "rent"
    SALARY = "salary"          # Legacy value kept for existing data
    SALARIES = "salaries"      # Preferred payroll category going forward
    UTILITIES = "utilities"
    MAINTENANCE = "maintenance"
    SUPPLIES = "supplies"
    MARKETING = "marketing"
    OTHER = "other"


# ==================== Currency Management ====================

class CurrencyStatus(str, Enum):
    """Currency availability status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


# ==================== Customer Management ====================

class CustomerType(str, Enum):
    """Customer classification"""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"


class CustomerStatus(str, Enum):
    """Customer account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class RiskLevel(str, Enum):
    """Customer risk assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentType(str, Enum):
    """Customer document types for KYC"""
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    TAX_ID = "tax_id"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


# ==================== Vault Management ====================

class VaultType(str, Enum):
    """Vault classification"""
    MAIN = "main"
    BRANCH = "branch"


class VaultTransferType(str, Enum):
    """Types of vault/branch transfers"""
    VAULT_TO_BRANCH = "vault_to_branch"
    BRANCH_TO_VAULT = "branch_to_vault"
    BRANCH_TO_BRANCH = "branch_to_branch"
    VAULT_TO_VAULT = "vault_to_vault"


class VaultTransferStatus(str, Enum):
    """Transfer workflow states"""
    PENDING = "pending"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# ==================== Alerts & Notifications ====================

class AlertType(str, Enum):
    """System alert categories"""
    LOW_BALANCE = "low_balance"
    HIGH_BALANCE = "high_balance"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    LARGE_TRANSACTION = "large_transaction"
    FAILED_LOGIN = "failed_login"
    SYSTEM_ERROR = "system_error"


class AlertSeverity(str, Enum):
    """Alert importance levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery methods"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"


# ==================== Audit & Logging ====================

class AuditAction(str, Enum):
    """Auditable user actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"
    TRANSFER = "transfer"


class EntityType(str, Enum):
    """Entity types for audit trail"""
    USER = "user"
    BRANCH = "branch"
    CUSTOMER = "customer"
    TRANSACTION = "transaction"
    CURRENCY = "currency"
    VAULT = "vault"
    DOCUMENT = "document"


# ==================== Report Types ====================

class ReportType(str, Enum):
    """Available report types"""
    DAILY_SUMMARY = "daily_summary"
    MONTHLY_REVENUE = "monthly_revenue"
    BRANCH_PERFORMANCE = "branch_performance"
    EXCHANGE_TRENDS = "exchange_trends"
    CUSTOMER_ANALYSIS = "customer_analysis"
    BALANCE_SNAPSHOT = "balance_snapshot"
    USER_ACTIVITY = "user_activity"
    AUDIT_TRAIL = "audit_trail"


class ReportFormat(str, Enum):
    """Export format options"""
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"
    CSV = "csv"


# ==================== Permissions ====================

class Permission(str, Enum):
    """Granular permission definitions"""
    # User permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Branch permissions
    BRANCH_CREATE = "branch:create"
    BRANCH_READ = "branch:read"
    BRANCH_UPDATE = "branch:update"
    BRANCH_DELETE = "branch:delete"
    BRANCH_ASSIGN_USERS = "branch:assign_users"
    
    # Currency permissions
    CURRENCY_CREATE = "currency:create"
    CURRENCY_READ = "currency:read"
    CURRENCY_UPDATE = "currency:update"
    CURRENCY_DELETE = "currency:delete"
    CURRENCY_SET_RATES = "currency:set_rates"
    
    # Transaction permissions
    TRANSACTION_CREATE = "transaction:create"
    TRANSACTION_READ = "transaction:read"
    TRANSACTION_APPROVE = "transaction:approve"
    TRANSACTION_CANCEL = "transaction:cancel"
    
    # Vault permissions (NEW - Added for Phase 7.2)
    VAULT_READ = "vault:read"
    VAULT_CREATE = "vault:create"
    VAULT_UPDATE = "vault:update"
    VAULT_TRANSFER = "vault:transfer"
    VAULT_APPROVE = "vault:approve"
    VAULT_RECEIVE = "vault:receive"
    VAULT_RECONCILE = "vault:reconcile"
    VAULT_ADJUST_BALANCE = "vault:adjust_balance"
    VAULT_CANCEL = "vault:cancel"
    
    # Report permissions
    REPORT_VIEW_BRANCH = "report:view_branch"
    REPORT_VIEW_ALL = "report:view_all"
    REPORT_EXPORT = "report:export"


# ==================== BUSINESS RULES ====================

# Currency & Exchange
CURRENCY_DECIMAL_PLACES = 2
EXCHANGE_RATE_DECIMAL_PLACES = 6

# Transaction Limits
MIN_TRANSACTION_AMOUNT = 0.01
MAX_TRANSACTION_AMOUNT = 1_000_000.00

# Branch Balance Thresholds
DEFAULT_MIN_BALANCE_THRESHOLD = 1000.00
DEFAULT_MAX_BALANCE_THRESHOLD = 100000.00

# Vault Settings (NEW - Added for Phase 7.2)
TRANSFER_APPROVAL_THRESHOLD = 50_000  # Transfers above this require approval
MAX_TRANSFER_AMOUNT = 1_000_000  # Maximum single transfer amount
MIN_VAULT_BALANCE = 10_000  # Minimum vault balance per currency (warning threshold)

# Reconciliation Settings (NEW - Added for Phase 7.2)
RECONCILIATION_TOLERANCE = 0.01  # Acceptable discrepancy in reconciliation
RECONCILIATION_FREQUENCY_DAYS = 7  # Recommended reconciliation frequency

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Token Expiration (in minutes)
PASSWORD_RESET_TOKEN_EXPIRE = 30
EMAIL_VERIFICATION_TOKEN_EXPIRE = 1440  # 24 hours
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # NEW - Added for Phase 7.2
REFRESH_TOKEN_EXPIRE_DAYS = 7  # NEW - Added for Phase 7.2

# File Paths
STATIC_DIR = "static"
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp"
LOGS_DIR = "logs"

# Date/Time Formats (NEW - Added for Phase 7.2)
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TRANSFER_NUMBER_DATE_FORMAT = "%Y%m%d"

# ==================== SECURITY SETTINGS (NEW - Added for Phase 7.2) ====================

# Password Requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_NUMBERS = True
REQUIRE_SPECIAL_CHARS = True

# ==================== ROLE PERMISSIONS MAPPING (NEW - Added for Phase 7.2) ====================

ROLE_PERMISSIONS = {
    "ADMIN": [
        # All vault permissions
        Permission.VAULT_READ,
        Permission.VAULT_CREATE,
        Permission.VAULT_UPDATE,
        Permission.VAULT_TRANSFER,
        Permission.VAULT_APPROVE,
        Permission.VAULT_RECEIVE,
        Permission.VAULT_RECONCILE,
        Permission.VAULT_ADJUST_BALANCE,
        Permission.VAULT_CANCEL,
        # All branch permissions
        Permission.BRANCH_CREATE,
        Permission.BRANCH_READ,
        Permission.BRANCH_UPDATE,
        Permission.BRANCH_DELETE,
        Permission.BRANCH_ASSIGN_USERS,
        # All transaction permissions
        Permission.TRANSACTION_CREATE,
        Permission.TRANSACTION_READ,
        Permission.TRANSACTION_APPROVE,
        Permission.TRANSACTION_CANCEL,
        # All user permissions
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        # All currency permissions
        Permission.CURRENCY_CREATE,
        Permission.CURRENCY_READ,
        Permission.CURRENCY_UPDATE,
        Permission.CURRENCY_DELETE,
        Permission.CURRENCY_SET_RATES,
        # All report permissions
        Permission.REPORT_VIEW_BRANCH,
        Permission.REPORT_VIEW_ALL,
        Permission.REPORT_EXPORT,
    ],
    "MANAGER": [
        # Vault permissions (manager level)
        Permission.VAULT_READ,
        Permission.VAULT_TRANSFER,
        Permission.VAULT_APPROVE,
        Permission.VAULT_RECONCILE,
        # Branch permissions
        Permission.BRANCH_READ,
        Permission.BRANCH_UPDATE,
        Permission.BRANCH_ASSIGN_USERS,
        # Transaction permissions
        Permission.TRANSACTION_CREATE,
        Permission.TRANSACTION_READ,
        Permission.TRANSACTION_APPROVE,
        Permission.TRANSACTION_CANCEL,
        # Currency permissions
        Permission.CURRENCY_READ,
        Permission.CURRENCY_SET_RATES,
        # Report permissions
        Permission.REPORT_VIEW_BRANCH,
        Permission.REPORT_VIEW_ALL,
        Permission.REPORT_EXPORT,
    ],
    "TELLER": [
        # Vault permissions (teller level)
        Permission.VAULT_READ,
        Permission.VAULT_RECEIVE,
        # Branch permissions
        Permission.BRANCH_READ,
        # Transaction permissions
        Permission.TRANSACTION_CREATE,
        Permission.TRANSACTION_READ,
        # Currency permissions
        Permission.CURRENCY_READ,
        # Report permissions
        Permission.REPORT_VIEW_BRANCH,
    ]
}

# ==================== NOTIFICATION SETTINGS (NEW - Added for Phase 7.2) ====================

# Alert Thresholds
LOW_BALANCE_THRESHOLD_PERCENTAGE = 10  # Alert when balance < 10% of max
HIGH_BALANCE_THRESHOLD_PERCENTAGE = 90  # Alert when balance > 90% of max

# Notification Types
NOTIFICATION_TYPES = [
    "transfer_pending",
    "transfer_approved",
    "transfer_rejected",
    "transfer_completed",
    "low_balance_alert",
    "high_balance_alert",
    "reconciliation_discrepancy",
    "large_transaction_alert"
]

# ==================== AUDIT LOG SETTINGS (NEW - Added for Phase 7.2) ====================

# Actions to log
AUDIT_ACTIONS = [
    "user_login",
    "user_logout",
    "vault_transfer_created",
    "vault_transfer_approved",
    "vault_transfer_rejected",
    "vault_transfer_completed",
    "vault_balance_adjusted",
    "branch_balance_adjusted",
    "transaction_created",
    "transaction_approved",
    "transaction_voided",
    "reconciliation_performed"
]

# Retention periods (in days)
AUDIT_LOG_RETENTION_DAYS = 365
TRANSACTION_LOG_RETENTION_DAYS = 2555  # 7 years
SECURITY_LOG_RETENTION_DAYS = 1825  # 5 years

# ==================== VALIDATION RULES (NEW - Added for Phase 7.2) ====================

# Currency Code Format
CURRENCY_CODE_PATTERN = r"^[A-Z]{3}$"  # e.g., USD, EUR, IQD

# Vault Code Format
VAULT_CODE_PATTERN = r"^V-[A-Z0-9]{4,10}$"  # e.g., V-MAIN, V-BR01

# Branch Code Format
BRANCH_CODE_PATTERN = r"^BR-[A-Z0-9]{4,10}$"  # e.g., BR-BGH, BR-001

# Customer ID Format
CUSTOMER_ID_PATTERN = r"^C-\d{8}$"  # e.g., C-00000001

# Transaction Number Formats
INCOME_NUMBER_PREFIX = "INC"
EXPENSE_NUMBER_PREFIX = "EXP"
EXCHANGE_NUMBER_PREFIX = "EXC"
TRANSFER_NUMBER_PREFIX = "TRF"
VAULT_TRANSFER_NUMBER_PREFIX = "VTR"

# ==================== ERROR MESSAGES (NEW - Added for Phase 7.2) ====================

ERROR_MESSAGES = {
    "insufficient_balance": "Insufficient balance for this operation",
    "transfer_approval_required": "Transfer amount requires manager approval",
    "invalid_vault_type": "Invalid vault type specified",
    "vault_not_found": "Vault not found",
    "currency_not_found": "Currency not found",
    "branch_not_found": "Branch not found",
    "transfer_not_found": "Transfer not found",
    "invalid_transfer_status": "Invalid transfer status for this operation",
    "permission_denied": "You don't have permission to perform this action",
    "main_vault_exists": "Main vault already exists",
    "reconciliation_discrepancy": "Reconciliation found discrepancies"
}

# ==================== SUCCESS MESSAGES (NEW - Added for Phase 7.2) ====================

SUCCESS_MESSAGES = {
    "vault_created": "Vault created successfully",
    "vault_updated": "Vault updated successfully",
    "transfer_created": "Transfer created successfully",
    "transfer_approved": "Transfer approved successfully",
    "transfer_rejected": "Transfer rejected",
    "transfer_completed": "Transfer completed successfully",
    "transfer_cancelled": "Transfer cancelled",
    "reconciliation_complete": "Reconciliation completed successfully",
    "balance_adjusted": "Balance adjusted successfully"
}