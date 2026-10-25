"""Unit and integration test suite for Phase 1 ML components."""

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb

from src.ml.data_loader import (
    ALL_COLUMNS,
    FEATURE_COLUMNS,
    generate_synthetic_transactions,
    get_train_test_splits,
)
from src.ml.evaluate import evaluate_fraud_model, find_optimal_threshold
from src.ml.explainer import FraudExplainer
from src.ml.predictor import FraudPredictor
from src.ml.preprocessor import TransactionPreprocessor


@pytest.fixture(scope="session")
def sample_dataset() -> pd.DataFrame:
    """Fixture providing a deterministic small dataset for rapid testing."""
    return generate_synthetic_transactions(n_samples=500, fraud_ratio=0.05, random_state=42)


@pytest.fixture(scope="session")
def fitted_preprocessor(sample_dataset: pd.DataFrame) -> TransactionPreprocessor:
    """Fixture providing a fitted preprocessor instance."""
    prep = TransactionPreprocessor()
    prep.fit(sample_dataset)
    return prep


@pytest.fixture(scope="session")
def trained_toy_model(
    sample_dataset: pd.DataFrame,
    fitted_preprocessor: TransactionPreprocessor,
) -> xgb.XGBClassifier:
    """Trains a fast XGBoost model on the fixture data."""
    X = fitted_preprocessor.transform(sample_dataset)
    y = sample_dataset["Class"].to_numpy()
    clf = xgb.XGBClassifier(n_estimators=10, max_depth=3, random_state=42)
    clf.fit(X, y)
    return clf


class TestDataLoader:
    """Tests for dataset loading and synthetic generation."""

    def test_synthetic_data_schema(self, sample_dataset: pd.DataFrame) -> None:
        """Verifies schema, dimensions, and lack of nulls in synthetic dataset."""
        assert len(sample_dataset) == 500
        for col in ALL_COLUMNS:
            assert col in sample_dataset.columns
        assert sample_dataset.isnull().sum().sum() == 0

    def test_class_imbalance(self, sample_dataset: pd.DataFrame) -> None:
        """Verifies fraud ratio matches specification."""
        fraud_count = sample_dataset["Class"].sum()
        assert fraud_count > 0
        assert fraud_count == 25  # 5% of 500

    def test_train_test_splitting(self, sample_dataset: pd.DataFrame) -> None:
        """Verifies stratified splitting maintains minority class representation."""
        X_tr, X_te, y_tr, y_te = get_train_test_splits(sample_dataset, test_size=0.2, random_state=42)
        assert len(X_tr) == 400
        assert len(X_te) == 100
        assert y_tr.sum() == 20
        assert y_te.sum() == 5


class TestPreprocessor:
    """Tests for TransactionPreprocessor."""

    def test_transformation_shape(
        self,
        sample_dataset: pd.DataFrame,
        fitted_preprocessor: TransactionPreprocessor,
    ) -> None:
        """Transformed array must have shape (n_samples, 30)."""
        transformed = fitted_preprocessor.transform(sample_dataset)
        assert transformed.shape == (500, 30)
        assert len(fitted_preprocessor.feature_names) == 30

    def test_transform_single_dict(self, fitted_preprocessor: TransactionPreprocessor) -> None:
        """Verifies single dictionary transformation."""
        payload = {"Amount": 99.95, "Time": 1200.0}
        for feat in FEATURE_COLUMNS:
            payload[feat] = 0.5

        single_arr = fitted_preprocessor.transform_single(payload)
        assert single_arr.shape == (1, 30)
        assert isinstance(single_arr, np.ndarray)

    def test_save_and_load(
        self,
        fitted_preprocessor: TransactionPreprocessor,
        tmp_path,
    ) -> None:
        """Verifies serialization roundtrip fidelity."""
        save_file = tmp_path / "preprocessor.joblib"
        fitted_preprocessor.save(save_file)

        loaded = TransactionPreprocessor.load(save_file)
        assert loaded.is_fitted is True
        assert loaded.feature_names == fitted_preprocessor.feature_names


class TestEvaluation:
    """Tests for model diagnostics and metrics."""

    def test_evaluation_metrics_computation(self) -> None:
        """Verifies calculation of PR-AUC, ROC-AUC, and confusion matrix."""
        y_true = np.array([0, 0, 0, 0, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.3, 0.4, 0.8, 0.9])

        metrics = evaluate_fraud_model(y_true, y_proba, threshold=0.5)

        assert "pr_auc" in metrics
        assert "roc_auc" in metrics
        assert "financial_cost_score" in metrics
        assert metrics["confusion_matrix"]["true_positives"] == 2
        assert metrics["confusion_matrix"]["false_negatives"] == 0

    def test_find_optimal_threshold(self) -> None:
        """Verifies threshold calibration output."""
        y_true = np.array([0, 0, 0, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.3, 0.7, 0.85])

        thresh, score = find_optimal_threshold(y_true, y_proba, target_metric="f1")
        assert 0.0 < thresh < 1.0
        assert score > 0.0


class TestExplainer:
    """Tests for Tree SHAP explainability."""

    def test_tree_shap_factors(
        self,
        trained_toy_model: xgb.XGBClassifier,
        fitted_preprocessor: TransactionPreprocessor,
    ) -> None:
        """Verifies SHAP factor extraction."""
        explainer = FraudExplainer(trained_toy_model, fitted_preprocessor.feature_names)
        sample_input = np.random.randn(1, 30).astype(np.float32)

        factors = explainer.explain_instance(sample_input, top_k=4)

        assert len(factors) == 4
        for item in factors:
            assert "feature" in item
            assert "impact" in item
            assert item["direction"] in ["INCREASES_RISK", "DECREASES_RISK"]
            assert "description" in item


class TestPredictor:
    """Tests for end-to-end FraudPredictor."""

    def test_predict_single_flow(
        self,
        trained_toy_model: xgb.XGBClassifier,
        fitted_preprocessor: TransactionPreprocessor,
    ) -> None:
        """Verifies predict_single outputs all required response fields."""
        predictor = FraudPredictor(
            model=trained_toy_model,
            preprocessor=fitted_preprocessor,
            fraud_threshold=0.50,
            review_threshold=0.20,
        )

        test_payload = {"Amount": 250.0, "Time": 3600.0}
        for col in FEATURE_COLUMNS:
            test_payload[col] = -1.2

        result = predictor.predict_single(test_payload, include_explanation=True)

        assert "fraudProbability" in result
        assert 0.0 <= result["fraudProbability"] <= 1.0
        assert result["riskLevel"] in ["LOW", "MEDIUM", "HIGH"]
        assert result["decision"] in ["APPROVE", "MANUAL_REVIEW", "BLOCK_TRANSACTION"]
        assert result["latencyMs"] >= 0.0
        assert len(result["topFactors"]) > 0

    def test_predict_batch_flow(
        self,
        trained_toy_model: xgb.XGBClassifier,
        fitted_preprocessor: TransactionPreprocessor,
    ) -> None:
        """Verifies vectorized batch prediction."""
        predictor = FraudPredictor(
            model=trained_toy_model,
            preprocessor=fitted_preprocessor,
        )

        batch_items = [
            {"Amount": 15.0, "Time": 100.0, **{f"V{i}": 0.1 for i in range(1, 29)}},
            {"Amount": 1200.0, "Time": 200.0, **{f"V{i}": -3.5 for i in range(1, 29)}},
        ]

        results = predictor.predict_batch(batch_items, include_explanation=False)
        assert len(results) == 2
        assert results[0]["transactionIndex"] == 0
        assert results[1]["transactionIndex"] == 1
