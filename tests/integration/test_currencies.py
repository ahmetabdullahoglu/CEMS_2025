"""
Currency Integration Tests
Complete test suite for currency operations
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models.currency import Currency, ExchangeRate
from app.schemas.currency import CurrencyCreate, ExchangeRateCreate


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Get admin authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "Admin@123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def manager_token(client):
    """Get manager authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "manager",
            "password": "manager123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def user_token(client):
    """Get regular user authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "user",
            "password": "user123"
        }
    )
    return response.json()["access_token"]


# ==================== Currency Tests ====================

class TestCurrencyCreation:
    """Test currency creation operations"""
    
    def test_create_currency_success(self, client, admin_token):
        """Test successful currency creation"""
        response = client.post(
            "/api/v1/currencies",
            json={
                "code": "USD",
                "name_en": "US Dollar",
                "name_ar": "الدولار الأمريكي",
                "symbol": "$",
                "is_base_currency": True,
                "decimal_places": 2,
                "is_active": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "USD"
        assert data["name_en"] == "US Dollar"
        assert data["is_base_currency"] is True
        assert data["is_active"] is True
    
    def test_create_currency_duplicate_code(self, client, admin_token):
        """Test creating currency with duplicate code"""
        # Create first currency
        client.post(
            "/api/v1/currencies",
            json={
                "code": "EUR",
                "name_en": "Euro",
                "name_ar": "يورو",
                "symbol": "€",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/v1/currencies",
            json={
                "code": "EUR",
                "name_en": "Euro 2",
                "name_ar": "يورو 2",
                "symbol": "€",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_currency_invalid_code(self, client, admin_token):
        """Test creating currency with invalid code format"""
        response = client.post(
            "/api/v1/currencies",
            json={
                "code": "US",  # Only 2 letters instead of 3
                "name_en": "Test Currency",
                "name_ar": "عملة تجريبية",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_currency_unauthorized(self, client, user_token):
        """Test currency creation without admin role"""
        response = client.post(
            "/api/v1/currencies",
            json={
                "code": "GBP",
                "name_en": "British Pound",
                "name_ar": "الجنيه الإسترليني",
                "symbol": "£",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403  # Forbidden
    
    def test_create_multiple_base_currencies(self, client, admin_token):
        """Test that only one base currency is allowed"""
        # Create first base currency
        client.post(
            "/api/v1/currencies",
            json={
                "code": "USD",
                "name_en": "US Dollar",
                "name_ar": "الدولار الأمريكي",
                "symbol": "$",
                "is_base_currency": True,
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Try to create second base currency
        response = client.post(
            "/api/v1/currencies",
            json={
                "code": "EUR",
                "name_en": "Euro",
                "name_ar": "يورو",
                "symbol": "€",
                "is_base_currency": True,
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "Base currency already exists" in response.json()["detail"]


class TestCurrencyRetrieval:
    """Test currency retrieval operations"""
    
    def test_list_currencies(self, client, admin_token, user_token):
        """Test listing all currencies"""
        # Create test currencies
        currencies = ["USD", "EUR", "TRY"]
        for code in currencies:
            client.post(
                "/api/v1/currencies",
                json={
                    "code": code,
                    "name_en": f"{code} Name",
                    "name_ar": f"اسم {code}",
                    "decimal_places": 2
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        # List currencies as user
        response = client.get(
            "/api/v1/currencies",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] >= 3
        assert len(data["data"]) >= 3
    
    def test_get_currency_by_id(self, client, admin_token, user_token):
        """Test getting currency by ID"""
        # Create currency
        create_response = client.post(
            "/api/v1/currencies",
            json={
                "code": "JPY",
                "name_en": "Japanese Yen",
                "name_ar": "الين الياباني",
                "symbol": "¥",
                "decimal_places": 0
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        currency_id = create_response.json()["id"]
        
        # Get currency by ID
        response = client.get(
            f"/api/v1/currencies/{currency_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "JPY"
        assert data["decimal_places"] == 0
    
    def test_get_currency_by_code(self, client, admin_token, user_token):
        """Test getting currency by code"""
        # Create currency
        client.post(
            "/api/v1/currencies",
            json={
                "code": "CHF",
                "name_en": "Swiss Franc",
                "name_ar": "الفرنك السويسري",
                "symbol": "CHF",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Get by code
        response = client.get(
            "/api/v1/currencies/code/CHF",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["code"] == "CHF"
    
    def test_get_nonexistent_currency(self, client, user_token):
        """Test getting non-existent currency"""
        response = client.get(
            "/api/v1/currencies/code/XXX",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 404


class TestCurrencyUpdate:
    """Test currency update operations"""
    
    def test_update_currency_success(self, client, admin_token):
        """Test successful currency update"""
        # Create currency
        create_response = client.post(
            "/api/v1/currencies",
            json={
                "code": "AUD",
                "name_en": "Australian Dollar",
                "name_ar": "الدولار الأسترالي",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        currency_id = create_response.json()["id"]
        
        # Update currency
        response = client.put(
            f"/api/v1/currencies/{currency_id}",
            json={
                "name_en": "Australian Dollar Updated",
                "symbol": "A$"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name_en"] == "Australian Dollar Updated"
        assert data["symbol"] == "A$"
    
    def test_activate_deactivate_currency(self, client, admin_token):
        """Test currency activation and deactivation"""
        # Create currency
        create_response = client.post(
            "/api/v1/currencies",
            json={
                "code": "CAD",
                "name_en": "Canadian Dollar",
                "name_ar": "الدولار الكندي",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        currency_id = create_response.json()["id"]
        
        # Deactivate
        response = client.patch(
            f"/api/v1/currencies/{currency_id}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False
        
        # Activate
        response = client.patch(
            f"/api/v1/currencies/{currency_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True


# ==================== Exchange Rate Tests ====================

class TestExchangeRates:
    """Test exchange rate operations"""
    
    @pytest.fixture
    def setup_currencies(self, client, admin_token):
        """Setup test currencies"""
        currencies = {}
        for code in ["USD", "EUR", "TRY"]:
            response = client.post(
                "/api/v1/currencies",
                json={
                    "code": code,
                    "name_en": f"{code} Name",
                    "name_ar": f"اسم {code}",
                    "decimal_places": 2,
                    "is_base_currency": (code == "USD")
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            currencies[code] = response.json()["id"]
        return currencies
    
    def test_set_exchange_rate(self, client, admin_token, setup_currencies):
        """Test setting exchange rate"""
        response = client.post(
            "/api/v1/currencies/rates",
            json={
                "from_currency_id": setup_currencies["USD"],
                "to_currency_id": setup_currencies["EUR"],
                "rate": 0.85,
                "buy_rate": 0.84,
                "sell_rate": 0.86,
                "notes": "Test rate"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert float(data["rate"]) == 0.85
        assert float(data["buy_rate"]) == 0.84
        assert float(data["sell_rate"]) == 0.86
    
    def test_get_exchange_rate(self, client, admin_token, user_token, setup_currencies):
        """Test getting current exchange rate"""
        # Set rate
        client.post(
            "/api/v1/currencies/rates",
            json={
                "from_currency_id": setup_currencies["USD"],
                "to_currency_id": setup_currencies["TRY"],
                "rate": 32.5
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Get rate
        response = client.get(
            "/api/v1/currencies/rates/USD/TRY",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        assert float(response.json()["rate"]) == 32.5
    
    def test_calculate_exchange(self, client, admin_token, user_token, setup_currencies):
        """Test exchange calculation"""
        # Set rate
        client.post(
            "/api/v1/currencies/rates",
            json={
                "from_currency_id": setup_currencies["USD"],
                "to_currency_id": setup_currencies["EUR"],
                "rate": 0.85
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Calculate exchange
        response = client.get(
            "/api/v1/currencies/calculate",
            params={
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "EUR"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert float(data["amount"]) == 100
        assert float(data["rate"]) == 0.85
        assert float(data["result"]) == 85.0
    
    def test_rate_history(self, client, admin_token, user_token, setup_currencies):
        """Test exchange rate history"""
        # Set multiple rates
        rates = [0.85, 0.86, 0.84]
        for rate in rates:
            client.post(
                "/api/v1/currencies/rates",
                json={
                    "from_currency_id": setup_currencies["USD"],
                    "to_currency_id": setup_currencies["EUR"],
                    "rate": rate
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        # Get history
        response = client.get(
            "/api/v1/currencies/rates/history/USD/EUR",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["data"]) >= 3
    
    def test_inverse_rate_calculation(self, client, admin_token, user_token, setup_currencies):
        """Test inverse rate calculation"""
        # Set USD -> EUR rate
        client.post(
            "/api/v1/currencies/rates",
            json={
                "from_currency_id": setup_currencies["USD"],
                "to_currency_id": setup_currencies["EUR"],
                "rate": 0.85
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Get EUR -> USD rate (should calculate inverse)
        response = client.get(
            "/api/v1/currencies/rates/EUR/USD",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        # Rate should be approximately 1/0.85 = 1.176
        rate = float(response.json()["rate"])
        assert 1.17 < rate < 1.18


# ==================== Permission Tests ====================

class TestPermissions:
    """Test role-based access control"""
    
    def test_user_cannot_create_currency(self, client, user_token):
        """Regular users cannot create currencies"""
        response = client.post(
            "/api/v1/currencies",
            json={
                "code": "TEST",
                "name_en": "Test",
                "name_ar": "تجربة",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_manager_can_set_rates(self, client, admin_token, manager_token):
        """Managers can set exchange rates"""
        # Create currencies as admin
        usd_response = client.post(
            "/api/v1/currencies",
            json={
                "code": "USD",
                "name_en": "US Dollar",
                "name_ar": "دولار",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        eur_response = client.post(
            "/api/v1/currencies",
            json={
                "code": "EUR",
                "name_en": "Euro",
                "name_ar": "يورو",
                "decimal_places": 2
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Set rate as manager
        response = client.post(
            "/api/v1/currencies/rates",
            json={
                "from_currency_id": usd_response.json()["id"],
                "to_currency_id": eur_response.json()["id"],
                "rate": 0.85
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 201
    
    def test_user_can_view_currencies(self, client, user_token):
        """Regular users can view currencies"""
        response = client.get(
            "/api/v1/currencies",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])