"""Unit and integration test suite for Phase 4: Database Auditing & Drift Monitoring."""

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.database import get_db, save_audit_record
from src.db.models import TransactionAuditRecord
from src.ml.drift_detector import DriftDetector, calculate_psi


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing initialized TestClient."""
    with TestClient(app) as test_client:
        yield test_client


class TestDatabaseAuditing:
    """Tests for SQLite audit trail persistence and retrieval."""

    def test_save_and_retrieve_audit_record(self) -> None:
        """Verifies manual save_audit_record writes to database."""
        record = save_audit_record(
            transaction_id="tx_audit_test_99",
            amount=299.50,
            time_delta=500.0,
            fraud_probability=0.88,
            is_fraud=True,
            risk_level="HIGH",
            decision="BLOCK_TRANSACTION",
            latency_ms=11.2,
            top_factors=[{"feature": "V14", "impact": 3.2}],
        )

        assert record.id is not None
        assert record.transaction_id == "tx_audit_test_99"
        assert record.is_fraud is True

        data_dict = record.to_dict()
        assert data_dict["transactionId"] == "tx_audit_test_99"
        assert len(data_dict["topFactors"]) == 1

    def test_audit_history_api_endpoint(self, client: TestClient) -> None:
        """Verifies /api/v1/analytics/history returns saved transactions with pagination."""
        # Trigger prediction to ensure at least one record is saved
        client.post("/api/v1/predict", json={"amount": 45.0, "time": 120.0})

        response = client.get("/api/v1/analytics/history?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()

        assert "totalRecords" in data
        assert data["totalRecords"] >= 1
        assert "records" in data
        assert len(data["records"]) <= 10

    def test_audit_history_filtering_by_risk(self, client: TestClient) -> None:
        """Verifies filtering audit records by risk level."""
        response = client.get("/api/v1/analytics/history?riskLevel=HIGH")
        assert response.status_code == 200
        data = response.json()

        for rec in data["records"]:
            assert rec["riskLevel"] == "HIGH"


class TestDriftMonitoring:
    """Tests for PSI calculation and DriftDetector."""

    def test_psi_identical_distributions(self) -> None:
        """PSI of identical distributions must be near 0.0."""
        rng = np.random.RandomState(42)
        dist = rng.normal(0, 1, 1000)

        psi = calculate_psi(dist, dist)
        assert psi < 0.05

    def test_psi_divergent_distributions(self) -> None:
        """PSI of significantly shifted distributions must indicate critical drift (> 0.2)."""
        rng = np.random.RandomState(42)
        baseline = rng.normal(0, 1, 1000)
        shifted = rng.normal(3.5, 2, 1000)

        psi = calculate_psi(baseline, shifted)
        assert psi > 0.20

    def test_drift_detector_evaluation(self) -> None:
        """Verifies DriftDetector detects stable vs drifted batches."""
        rng = np.random.RandomState(42)
        base_df = pd.DataFrame({
            "Amount": rng.uniform(10, 100, 500),
            "Time": rng.uniform(0, 1000, 500),
            "V4": rng.normal(0, 1, 500),
            "V14": rng.normal(0, 1, 500),
        })

        detector = DriftDetector(baseline_df=base_df)

        # Stable batch
        stable_batch = pd.DataFrame({
            "Amount": rng.uniform(10, 100, 200),
            "Time": rng.uniform(0, 1000, 200),
            "V4": rng.normal(0, 1, 200),
            "V14": rng.normal(0, 1, 200),
        })
        stable_report = detector.evaluate_batch_drift(stable_batch)
        assert stable_report["driftStatus"] in ["NO_DRIFT", "MODERATE_DRIFT"]

        # Heavily drifted batch
        drifted_batch = pd.DataFrame({
            "Amount": rng.uniform(5000, 10000, 200),
            "Time": rng.uniform(50000, 90000, 200),
            "V4": rng.normal(5, 2, 200),
            "V14": rng.normal(-8, 2, 200),
        })
        drift_report = detector.evaluate_batch_drift(drifted_batch)
        assert drift_report["driftStatus"] == "CRITICAL_DRIFT"

    def test_drift_check_api_endpoint(self, client: TestClient) -> None:
        """Verifies /api/v1/analytics/drift-check API endpoint."""
        payload = {
            "transactions": [
                {"amount": 25.0, "time": 100.0, "features": {f"V{i}": 0.0 for i in range(1, 29)}},
                {"amount": 35.0, "time": 150.0, "features": {f"V{i}": 0.1 for i in range(1, 29)}},
            ]
        }
        response = client.post("/api/v1/analytics/drift-check", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "driftStatus" in data
        assert "averagePsi" in data
        assert "recommendation" in data
