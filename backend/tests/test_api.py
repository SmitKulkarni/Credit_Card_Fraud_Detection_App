"""Integration and end-to-end test suite for FastAPI fraud detection endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing an initialized FastAPI TestClient with lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


class TestSystemRoutes:
    """Tests for root, health, and model metadata endpoints."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Verifies root endpoint returns active API descriptor."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "docsUrl" in data

    def test_health_check(self, client: TestClient) -> None:
        """Verifies /api/v1/health reports healthy with model loaded."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["modelLoaded"] is True
        assert data["uptimeSeconds"] >= 0.0

    def test_model_metadata(self, client: TestClient) -> None:
        """Verifies /api/v1/model/metadata returns active model metrics and PR-AUC."""
        response = client.get("/api/v1/model/metadata")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert data["metrics"]["pr_auc"] >= 0.85
        assert "activeThresholds" in data


class TestPredictionRoutes:
    """Tests for single and batch prediction endpoints."""

    def test_get_preset_scenarios(self, client: TestClient) -> None:
        """Verifies /api/v1/predict/presets returns the 3 pre-configured scenarios."""
        response = client.get("/api/v1/predict/presets")
        assert response.status_code == 200
        presets = response.json()
        assert len(presets) == 3
        preset_ids = [p["presetId"] for p in presets]
        assert "legitimate_grocery" in preset_ids
        assert "suspicious_velocity" in preset_ids
        assert "confirmed_fraud" in preset_ids

    def test_predict_single_normal_transaction(self, client: TestClient) -> None:
        """Scores a normal transaction and asserts LOW risk / APPROVE."""
        payload = {
            "transactionId": "tx_test_normal_01",
            "amount": 25.50,
            "time": 300.0,
            "features": {f"V{i}": 0.02 for i in range(1, 29)},
        }
        response = client.post("/api/v1/predict?includeExplanation=true", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["transactionId"] == "tx_test_normal_01"
        assert data["isFraud"] is False
        assert data["riskLevel"] == "LOW"
        assert data["decision"] == "APPROVE"
        assert 0.0 <= data["fraudProbability"] < 0.20
        assert data["latencyMs"] >= 0.0
        assert len(data["topFactors"]) > 0

    def test_predict_single_fraud_transaction(self, client: TestClient) -> None:
        """Scores an anomalous transaction and asserts HIGH risk / BLOCK."""
        payload = {
            "transactionId": "tx_test_fraud_01",
            "amount": 1650.00,
            "time": 850.0,
            "features": {
                **{f"V{i}": -0.2 for i in range(1, 29)},
                "V4": 4.5,
                "V10": -5.2,
                "V11": 3.8,
                "V12": -6.5,
                "V14": -7.2,
                "V17": -5.0,
            },
        }
        response = client.post("/api/v1/predict?includeExplanation=true", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["transactionId"] == "tx_test_fraud_01"
        assert data["isFraud"] is True
        assert data["riskLevel"] == "HIGH"
        assert data["decision"] == "BLOCK_TRANSACTION"
        assert data["fraudProbability"] >= 0.35
        assert len(data["topFactors"]) > 0

    def test_predict_batch_transactions(self, client: TestClient) -> None:
        """Verifies vectorized batch scoring with multiple items."""
        batch_payload = {
            "transactions": [
                {
                    "transactionId": "tx_batch_01",
                    "amount": 12.00,
                    "time": 100.0,
                    "features": {f"V{i}": 0.01 for i in range(1, 29)},
                },
                {
                    "transactionId": "tx_batch_02",
                    "amount": 1850.00,
                    "time": 200.0,
                    "features": {
                        **{f"V{i}": 0.0 for i in range(1, 29)},
                        "V14": -6.8,
                        "V12": -5.5,
                    },
                },
            ],
            "includeExplanation": False,
        }
        response = client.post("/api/v1/predict/batch", json=batch_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["totalProcessed"] == 2
        assert len(data["results"]) == 2
        assert data["averageLatencyMs"] >= 0.0

    def test_validation_error_negative_amount(self, client: TestClient) -> None:
        """Verifies that negative amount triggers 422 Unprocessable Entity."""
        invalid_payload = {
            "transactionId": "tx_invalid",
            "amount": -50.0,
            "time": 100.0,
        }
        response = client.post("/api/v1/predict", json=invalid_payload)
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"


class TestAnalyticsRoutes:
    """Tests for session statistics tracking."""

    def test_analytics_stats_recording(self, client: TestClient) -> None:
        """Verifies analytics endpoint returns rolling transaction counters."""
        response = client.get("/api/v1/analytics/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "totalTransactionsScored" in stats
        assert stats["totalTransactionsScored"] >= 1
        assert "latencyStats" in stats


class TestDashboardMount:
    """Tests for Phase 3 UI dashboard mounting."""

    def test_dashboard_mount_serves_html(self, client: TestClient) -> None:
        """Verifies that /dashboard returns the HTML analyst workstation."""
        response = client.get("/dashboard")
        assert response.status_code in [200, 307]  # 307 redirect to /dashboard/ or 200
        if response.status_code == 307:
            response = client.get("/dashboard/")
            assert response.status_code == 200
        assert "Sentinel Triage Studio" in response.text

