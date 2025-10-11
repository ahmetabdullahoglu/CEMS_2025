"""
API v1 Router
Aggregates all API endpoints
"""

from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints import auth, currencies,branches  # Add currencies

# Future imports (will be implemented in next components)
# from app.api.v1.endpoints import (
#     users,
#     currencies,
#     branches,
#     customers,
#     transactions,
#     vault,
#     reports
# )

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Future routers (uncomment as implemented)
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(currencies.router, prefix="/currencies", tags=["Currencies"])
# api_router.include_router(branches.router, prefix="/branches", tags=["Branches"])
# api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
# api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
# api_router.include_router(vault.router, prefix="/vault", tags=["Vault"])
# api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
# Add currency router
api_router.include_router(
    currencies.router, 
    prefix="/currencies", 
    tags=["Currencies"]
)
# Register routers
api_router.include_router(
    branches.router,
    prefix="/branches",
    tags=["branches"]
)
# Placeholder endpoint for testing
@api_router.get("/ping", tags=["Test"])
async def ping():
    """Test endpoint to verify API is working"""
    return {
        "success": True,
        "message": "pong"
    }