"""
Database Models Package
Exports all database models for easy import
"""

from app.db.models.user import User, user_branches, user_roles
from app.db.models.role import Role

# Export all models
__all__ = [
    "User",
    "Role",
    "user_branches",
    "user_roles",
]

# Note: Import and add new models here as they are created
# Examples for future phases:
#
# from app.db.models.currency import Currency
# from app.db.models.branch import Branch
# from app.db.models.customer import Customer
# from app.db.models.transaction import Transaction
# from app.db.models.vault import Vault
# from app.db.models.document import Document
# from app.db.models.audit import AuditLog
#
# Then add to __all__:
# __all__ = [
#     "User",
#     "Role",
#     "Currency",
#     "Branch",
#     "Customer",
#     "Transaction",
#     "Vault",
#     "Document",
#     "AuditLog",
#     "user_branches",
#     "user_roles",
# ]