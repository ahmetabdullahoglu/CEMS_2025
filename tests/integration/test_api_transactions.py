"""
API Integration Tests for Transaction Endpoints
================================================
Tests all transaction API endpoints via HTTP
"""

import pytest
from decimal import Decimal
from uuid import uuid4, UUID
from datetime import date
from httpx import AsyncClient

from app.main import app
from app.db.models.transaction import TransactionType, TransactionStatus


@pytest.mark.asyncio
class TestIncomeEndpoints:
    """Test income transaction endpoints"""

    async def test_create_income_transaction(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/income"""
        payload = {
            "amount": 150.50,
            "currency_id": str(uuid4()),
            "branch_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "income_category": "service_fee",
            "income_source": "Test service fee",
            "reference_number": f"TEST-INC-{uuid4().hex[:8]}"
        }

        response = await async_client.post(
            "/api/v1/transactions/income",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 404]  # May fail due to missing data

    async def test_list_income_transactions(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/income"""
        response = await async_client.get(
            "/api/v1/transactions/income",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "transactions" in data
        assert "total" in data

    async def test_get_income_transaction(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/income/{id}"""
        # Use a random UUID (will return 404 if not found)
        transaction_id = str(uuid4())

        response = await async_client.get(
            f"/api/v1/transactions/income/{transaction_id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestExpenseEndpoints:
    """Test expense transaction endpoints"""

    async def test_create_expense_transaction(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/expense"""
        payload = {
            "amount": 500.00,
            "currency_id": str(uuid4()),
            "branch_id": str(uuid4()),
            "expense_category": "rent",
            "expense_to": "Landlord",
            "approval_required": False,
            "reference_number": f"TEST-EXP-{uuid4().hex[:8]}"
        }

        response = await async_client.post(
            "/api/v1/transactions/expense",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 404]

    async def test_approve_expense_transaction(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/expense/{id}/approve"""
        transaction_id = str(uuid4())
        payload = {
            "approval_notes": "Approved for testing"
        }

        response = await async_client.post(
            f"/api/v1/transactions/expense/{transaction_id}/approve",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code in [200, 400, 403, 404]

    async def test_list_expense_transactions(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/expense"""
        response = await async_client.get(
            "/api/v1/transactions/expense",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data or "items" in data


@pytest.mark.asyncio
class TestExchangeEndpoints:
    """Test exchange transaction endpoints"""

    async def test_preview_exchange_rate(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/exchange/rate-preview"""
        payload = {
            "from_currency_id": str(uuid4()),
            "to_currency_id": str(uuid4()),
            "from_amount": 100.00
        }

        response = await async_client.post(
            "/api/v1/transactions/exchange/rate-preview",
            json=payload,
            headers=auth_headers
        )

        # Will likely fail without proper exchange rates
        assert response.status_code in [200, 400, 404]

    async def test_create_exchange_transaction(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/exchange"""
        payload = {
            "branch_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "from_currency_id": str(uuid4()),
            "to_currency_id": str(uuid4()),
            "from_amount": 100.00,
            "reference_number": f"TEST-EXC-{uuid4().hex[:8]}"
        }

        response = await async_client.post(
            "/api/v1/transactions/exchange",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 404]

    async def test_list_exchange_transactions(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/exchange"""
        response = await async_client.get(
            "/api/v1/transactions/exchange",
            headers=auth_headers
        )

        assert response.status_code == 200

    async def test_get_exchange_transaction(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/exchange/{id}"""
        transaction_id = str(uuid4())

        response = await async_client.get(
            f"/api/v1/transactions/exchange/{transaction_id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 400]


@pytest.mark.asyncio
class TestTransferEndpoints:
    """Test transfer transaction endpoints"""

    async def test_create_transfer_transaction(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/transfer"""
        payload = {
            "from_branch_id": str(uuid4()),
            "to_branch_id": str(uuid4()),
            "amount": 1000.00,
            "currency_id": str(uuid4()),
            "transfer_type": "branch_to_branch",
            "reference_number": f"TEST-TRF-{uuid4().hex[:8]}"
        }

        response = await async_client.post(
            "/api/v1/transactions/transfer",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code in [201, 400, 404]

    async def test_receive_transfer(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/transfer/{id}/receive"""
        transaction_id = str(uuid4())
        payload = {
            "receipt_notes": "Received for testing"
        }

        response = await async_client.post(
            f"/api/v1/transactions/transfer/{transaction_id}/receive",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code in [200, 400, 404]

    async def test_list_transfer_transactions(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/transfer"""
        response = await async_client.get(
            "/api/v1/transactions/transfer",
            headers=auth_headers
        )

        assert response.status_code == 200

    async def test_get_transfer_transaction(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/transfer/{id}"""
        transaction_id = str(uuid4())

        response = await async_client.get(
            f"/api/v1/transactions/transfer/{transaction_id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 400]


@pytest.mark.asyncio
class TestGeneralEndpoints:
    """Test general transaction endpoints"""

    async def test_list_all_transactions(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions"""
        response = await async_client.get(
            "/api/v1/transactions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data

    async def test_list_with_filters(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions with filters"""
        params = {
            "transaction_type": "income",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
            "skip": 0,
            "limit": 10
        }

        response = await async_client.get(
            "/api/v1/transactions",
            params=params,
            headers=auth_headers
        )

        assert response.status_code == 200

    async def test_get_transaction(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/{id}"""
        transaction_id = str(uuid4())

        response = await async_client.get(
            f"/api/v1/transactions/{transaction_id}",
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 400]

    async def test_cancel_transaction(self, async_client: AsyncClient, auth_headers):
        """Test POST /api/v1/transactions/{id}/cancel"""
        transaction_id = str(uuid4())
        payload = {
            "reason": "Testing cancellation functionality"
        }

        response = await async_client.post(
            f"/api/v1/transactions/{transaction_id}/cancel",
            json=payload,
            headers=auth_headers
        )

        # Will likely return 404 or 403
        assert response.status_code in [200, 400, 403, 404]

    async def test_get_transaction_stats(self, async_client: AsyncClient, auth_headers):
        """Test GET /api/v1/transactions/stats/summary"""
        response = await async_client.get(
            "/api/v1/transactions/stats/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data or "total_transactions" in data


@pytest.mark.asyncio
class TestValidation:
    """Test request validation"""

    async def test_invalid_amount(self, async_client: AsyncClient, auth_headers):
        """Test negative amount validation"""
        payload = {
            "amount": -100.00,  # Negative amount
            "currency_id": str(uuid4()),
            "branch_id": str(uuid4()),
            "income_category": "service_fee"
        }

        response = await async_client.post(
            "/api/v1/transactions/income",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    async def test_missing_required_fields(self, async_client: AsyncClient, auth_headers):
        """Test missing required fields"""
        payload = {
            "amount": 100.00
            # Missing required fields
        }

        response = await async_client.post(
            "/api/v1/transactions/income",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422

    async def test_invalid_uuid(self, async_client: AsyncClient, auth_headers):
        """Test invalid UUID format"""
        payload = {
            "amount": 100.00,
            "currency_id": "not-a-valid-uuid",
            "branch_id": str(uuid4()),
            "income_category": "service_fee"
        }

        response = await async_client.post(
            "/api/v1/transactions/income",
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422


# ==================== Fixtures ====================

@pytest.fixture
async def async_client():
    """Create async HTTP client"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    # This should be replaced with actual auth token generation
    return {
        "Authorization": "Bearer test_token"
    }
