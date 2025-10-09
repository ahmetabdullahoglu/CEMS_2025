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
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REVERSED = "reversed"


class IncomeCategory(str, Enum):
    """Income source categories"""
    SERVICE_FEE = "service_fee"
    COMMISSION = "commission"
    INTEREST = "interest"
    OTHER = "other"


class ExpenseCategory(str, Enum):
    """Expense type categories"""
    RENT = "rent"
    SALARY = "salary"
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


class TransferType(str, Enum):
    """Types of vault/branch transfers"""
    VAULT_TO_BRANCH = "vault_to_branch"
    BRANCH_TO_VAULT = "branch_to_vault"
    BRANCH_TO_BRANCH = "branch_to_branch"
    VAULT_TO_VAULT = "vault_to_vault"


class TransferStatus(str, Enum):
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
    
    # Vault permissions
    VAULT_READ = "vault:read"
    VAULT_TRANSFER = "vault:transfer"
    VAULT_APPROVE_TRANSFER = "vault:approve_transfer"
    
    # Report permissions
    REPORT_VIEW_BRANCH = "report:view_branch"
    REPORT_VIEW_ALL = "report:view_all"
    REPORT_EXPORT = "report:export"


# ==================== Business Constants ====================

# Currency decimal places
CURRENCY_DECIMAL_PLACES = 2
EXCHANGE_RATE_DECIMAL_PLACES = 6

# Transaction limits
MIN_TRANSACTION_AMOUNT = 0.01
MAX_TRANSACTION_AMOUNT = 1000000.00

# Balance thresholds
DEFAULT_MIN_BALANCE_THRESHOLD = 1000.00
DEFAULT_MAX_BALANCE_THRESHOLD = 100000.00

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Token expiration (in minutes)
PASSWORD_RESET_TOKEN_EXPIRE = 30
EMAIL_VERIFICATION_TOKEN_EXPIRE = 1440  # 24 hours

# File paths
STATIC_DIR = "static"
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp"
LOGS_DIR = "logs"