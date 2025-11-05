# app/api/v1/endpoints/__init__.py
"""
API v1 Endpoints Package
All endpoint modules for the API
"""

# Import all endpoint routers
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import currencies
from app.api.v1.endpoints import branches
#from app.api.v1.endpoints import customers


# Export for easy imports
__all__ = [
    "auth",
    "currencies", 
    "branches",
    "customers"
]