"""
Permission System
Centralized permission definitions and management
"""

from typing import List, Dict, Set
from enum import Enum


# ==================== Permission Categories ====================

class PermissionCategory(str, Enum):
    """Permission categories for organization"""
    USERS = "users"
    BRANCHES = "branches"
    CURRENCIES = "currencies"
    TRANSACTIONS = "transactions"
    VAULT = "vault"
    REPORTS = "reports"
    CUSTOMERS = "customers"
    DOCUMENTS = "documents"
    SYSTEM = "system"


# ==================== Permission Actions ====================

class PermissionAction(str, Enum):
    """Common permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    CANCEL = "cancel"
    EXPORT = "export"
    ASSIGN = "assign"
    TRANSFER = "transfer"
    VIEW_ALL = "view_all"
    VIEW_BRANCH = "view_branch"
    SET_RATES = "set_rates"


# ==================== Permission Definitions ====================

# All available permissions in the system
ALL_PERMISSIONS: Dict[str, List[str]] = {
    # User Management
    "users": [
        "create",           # Create new users
        "read",            # View user details
        "update",          # Update user information
        "delete",          # Delete/deactivate users
        "assign_roles",    # Assign roles to users
        "manage_permissions", # Manage user permissions
    ],
    
    # Branch Management
    "branches": [
        "create",           # Create new branches
        "read",            # View branch details
        "update",          # Update branch information
        "delete",          # Delete/close branches
        "assign_users",    # Assign users to branches
        "view_all",        # View all branches
        "view_own",        # View only assigned branches
        "manage_balances", # Manage branch balances
    ],
    
    # Currency Management
    "currencies": [
        "create",           # Add new currencies
        "read",            # View currency information
        "update",          # Update currency details
        "delete",          # Remove currencies
        "set_rates",       # Set exchange rates
        "view_rates",      # View exchange rates
        "manage_rates",    # Manage rate history
    ],
    
    # Transaction Management
    "transactions": [
        "create",           # Create new transactions
        "read",            # View transactions
        "update",          # Update pending transactions
        "delete",          # Delete draft transactions
        "approve",         # Approve transactions
        "cancel",          # Cancel transactions
        "view_all",        # View all transactions
        "view_branch",     # View branch transactions only
        "view_own",        # View own transactions only
    ],
    
    # Vault Management
    "vault": [
        "read",            # View vault information
        "transfer",        # Initiate transfers
        "approve_transfer", # Approve vault transfers
        "view_balances",   # View vault balances
        "reconcile",       # Perform reconciliation
    ],
    
    # Report Management
    "reports": [
        "view_branch",     # View branch reports
        "view_all",        # View all reports
        "export",          # Export reports
        "generate",        # Generate custom reports
        "schedule",        # Schedule automated reports
    ],
    
    # Customer Management
    "customers": [
        "create",           # Register new customers
        "read",            # View customer information
        "update",          # Update customer details
        "delete",          # Delete customers
        "verify",          # Verify customer documents
        "view_all",        # View all customers
        "view_branch",     # View branch customers only
    ],
    
    # Document Management
    "documents": [
        "upload",          # Upload documents
        "read",            # View documents
        "update",          # Update document info
        "delete",          # Delete documents
        "verify",          # Verify documents
        "download",        # Download documents
    ],
    
    # System Management
    "system": [
        "view_logs",       # View system logs
        "manage_settings", # Manage system settings
        "backup",          # Perform backups
        "restore",         # Restore from backup
        "maintenance",     # System maintenance mode
    ],
    "reports": [
        "view_branch",      # View own branch reports
        "view_all",         # View all branch reports
        "export",           # Export reports
        "generate",         # Generate custom reports
    ]
}


# ==================== Role Permission Mappings ====================

# Default permissions for each role
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": [
        # Admin has ALL permissions
        "users:create", "users:read", "users:update", "users:delete", 
        "users:assign_roles", "users:manage_permissions",
        
        "branches:create", "branches:read", "branches:update", "branches:delete",
        "branches:assign_users", "branches:view_all", "branches:manage_balances",
        
        "currencies:create", "currencies:read", "currencies:update", "currencies:delete",
        "currencies:set_rates", "currencies:view_rates", "currencies:manage_rates",
        
        "transactions:create", "transactions:read", "transactions:update",
        "transactions:delete", "transactions:approve", "transactions:cancel",
        "transactions:view_all",
        
        "vault:read", "vault:transfer", "vault:approve_transfer",
        "vault:view_balances", "vault:reconcile",
        
        "reports:view_branch", "reports:view_all", "reports:export",
        "reports:generate", "reports:schedule",
        
        "customers:create", "customers:read", "customers:update", "customers:delete",
        "customers:verify", "customers:view_all",
        
        "documents:upload", "documents:read", "documents:update", "documents:delete",
        "documents:verify", "documents:download",
        
        "system:view_logs", "system:manage_settings", "system:backup",
        "system:restore", "system:maintenance",
        "reports:view_all",
        "reports:export",
        "reports:generate",
        
    ],
    
    "manager": [
        # Manager has branch-level management
        "users:read",
        
        "branches:read", "branches:update", "branches:assign_users",
        "branches:view_own", "branches:manage_balances",
        
        "currencies:read", "currencies:set_rates", "currencies:view_rates",
        
        "transactions:create", "transactions:read", "transactions:update",
        "transactions:approve", "transactions:cancel", "transactions:view_branch",
        
        "vault:read", "vault:transfer", "vault:view_balances",
        
        "reports:view_branch", "reports:export", "reports:generate",
        
        "customers:create", "customers:read", "customers:update",
        "customers:verify", "customers:view_branch",
        
        "documents:upload", "documents:read", "documents:update",
        "documents:verify", "documents:download",
        "reports:view_branch",
        "reports:export",
        "reports:generate",
    ],
    
    "teller": [
        # Teller has basic transaction operations
        "currencies:read", "currencies:view_rates",
        
        "transactions:create", "transactions:read", "transactions:view_own",
        
        "reports:view_branch",
        
        "customers:create", "customers:read", "customers:view_branch",
        
        "documents:upload", "documents:read",
        "reports:view_branch",  # Can view own branch reports only

    ],
}


# ==================== Permission Utility Functions ====================

def format_permission(category: str, action: str) -> str:
    """
    Format permission string
    
    Args:
        category: Permission category (e.g., 'users')
        action: Permission action (e.g., 'create')
        
    Returns:
        str: Formatted permission (e.g., 'users:create')
    """
    return f"{category}:{action}"


def parse_permission(permission: str) -> tuple[str, str]:
    """
    Parse permission string into category and action
    
    Args:
        permission: Permission string (e.g., 'users:create')
        
    Returns:
        tuple: (category, action)
    """
    parts = permission.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid permission format: {permission}")
    return parts[0], parts[1]


def get_all_permissions_list() -> List[str]:
    """
    Get list of all available permissions
    
    Returns:
        List[str]: All permissions in format 'category:action'
    """
    permissions = []
    for category, actions in ALL_PERMISSIONS.items():
        for action in actions:
            permissions.append(format_permission(category, action))
    return permissions


def get_permissions_by_category(category: str) -> List[str]:
    """
    Get all permissions for a specific category
    
    Args:
        category: Permission category
        
    Returns:
        List[str]: Permissions for the category
    """
    if category not in ALL_PERMISSIONS:
        return []
    
    return [
        format_permission(category, action)
        for action in ALL_PERMISSIONS[category]
    ]


def validate_permission(permission: str) -> bool:
    """
    Validate if permission exists in system
    
    Args:
        permission: Permission string to validate
        
    Returns:
        bool: True if permission is valid
    """
    try:
        category, action = parse_permission(permission)
        return category in ALL_PERMISSIONS and action in ALL_PERMISSIONS[category]
    except:
        return False


def get_role_permissions(role_name: str) -> List[str]:
    """
    Get all permissions for a role
    
    Args:
        role_name: Role name (admin, manager, teller)
        
    Returns:
        List[str]: List of permissions
    """
    return ROLE_PERMISSIONS.get(role_name, [])


def check_permission_hierarchy(user_permissions: List[str], required_permission: str) -> bool:
    """
    Check if user has required permission or a higher-level permission
    
    For example:
    - 'users:manage_permissions' includes 'users:read'
    - 'transactions:approve' includes 'transactions:read'
    
    Args:
        user_permissions: List of user's permissions
        required_permission: Required permission
        
    Returns:
        bool: True if user has permission or higher
    """
    # Direct permission check
    if required_permission in user_permissions:
        return True
    
    # Parse required permission
    category, action = parse_permission(required_permission)
    
    # Define permission hierarchies
    hierarchies = {
        "read": [],  # Read is base level
        "create": ["read"],
        "update": ["read"],
        "delete": ["read", "update"],
        "approve": ["read", "update"],
        "manage": ["read", "create", "update", "delete"],
        "view_all": ["read", "view_branch", "view_own"],
    }
    
    # Check if user has higher-level permissions
    for user_permission in user_permissions:
        user_category, user_action = parse_permission(user_permission)
        
        # Same category check
        if user_category == category:
            # Check if user's action implies required action
            if action in hierarchies.get(user_action, []):
                return True
    
    return False


# ==================== Permission Groups ====================

class PermissionGroup:
    """Predefined permission groups for common use cases"""
    
    # Read-only permissions
    READ_ONLY = [
        "users:read",
        "branches:read", "branches:view_own",
        "currencies:read", "currencies:view_rates",
        "transactions:read", "transactions:view_own",
        "vault:read", "vault:view_balances",
        "reports:view_branch",
        "customers:read", "customers:view_branch",
        "documents:read",
    ]
    
    # Transaction operations
    TRANSACTION_OPS = [
        "currencies:read", "currencies:view_rates",
        "transactions:create", "transactions:read", "transactions:view_own",
        "customers:read", "customers:view_branch",
    ]
    
    # Branch management
    BRANCH_MANAGEMENT = [
        "branches:read", "branches:update", "branches:assign_users",
        "branches:view_own", "branches:manage_balances",
        "transactions:view_branch",
        "reports:view_branch", "reports:export",
        "customers:view_branch",
    ]
    
    # Financial reporting
    FINANCIAL_REPORTING = [
        "branches:read", "branches:view_all",
        "transactions:read", "transactions:view_all",
        "vault:read", "vault:view_balances",
        "reports:view_all", "reports:export", "reports:generate",
    ]


# ==================== Permission Constants ====================

# Minimum required permissions for different operations
MIN_PERMISSIONS = {
    "login": [],  # No special permissions needed
    "view_dashboard": ["reports:view_branch"],
    "create_transaction": ["transactions:create"],
    "approve_transaction": ["transactions:approve"],
    "manage_users": ["users:read", "users:update"],
    "system_admin": ["system:manage_settings"],
}


# ==================== Export ====================

__all__ = [
    "PermissionCategory",
    "PermissionAction",
    "ALL_PERMISSIONS",
    "ROLE_PERMISSIONS",
    "format_permission",
    "parse_permission",
    "get_all_permissions_list",
    "get_permissions_by_category",
    "validate_permission",
    "get_role_permissions",
    "check_permission_hierarchy",
    "PermissionGroup",
    "MIN_PERMISSIONS",
]