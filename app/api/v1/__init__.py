# app/api/v1/__init__.py
"""
API v1 Router
Aggregates all API endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, currencies, branches, users, customers, transactions, vault, reports, dashboard, rate_sync


# Create main API router
api_router = APIRouter()

# ==================== Register All Routers ====================

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Currency endpoints
api_router.include_router(
    currencies.router,
    prefix="/currencies",
    tags=["Currencies"]
)

# Branch endpoints
api_router.include_router(
    branches.router,
    prefix="/branches",
    tags=["Branches"]
)

# User endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Customer endpoints
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])

# api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"]
)
# api_router.include_router(vault.router, prefix="/vault", tags=["Vault"])
api_router.include_router(vault.router)
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# Rate synchronization endpoints
api_router.include_router(
    rate_sync.router,
    prefix="/rate-sync",
    tags=["Rate Synchronization"]
)

# ==================== Health Check Endpoints ====================

@api_router.get("/ping", tags=["Health"])
async def ping():
    """
    Simple health check endpoint
    
    Returns:
        dict: Success message
    """
    return {
        "success": True,
        "message": "pong",
        "service": "CEMS API v1"
    }


@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Detailed health check endpoint
    
    Returns:
        dict: System health status
    """
    return {
        "success": True,
        "status": "healthy",
        "service": "CEMS API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "active",
            "currencies": "active",
            "branches": "active",
            "users": "pending",
            "customers": "pending",
            "transactions": "pending",
            "vault": "pending",
            "reports": "pending"
        }
    }