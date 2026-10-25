"""Inference wrapper for real-time and batch fraud prediction.

Loads trained models and preprocessors, computes risk scores and classifications,
measures latency, and optionally attaches Tree SHAP factor explanations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import time
import joblib
import numpy as np
import pandas as pd

from src.ml.explainer import FraudExplainer
from src.ml.preprocessor import TransactionPreprocessor

logger = logging.getLogger(__name__)


class FraudPredictor:
    """Unified fraud detection inference service."""

    def __init__(
        self,
        model: Any,
        preprocessor: TransactionPreprocessor,
        fraud_threshold: float = 0.35,
        review_threshold: float = 0.20,
    ) -> None:
        """Initializes the predictor service.

        Args:
            model: Trained classifier supporting predict_proba or predict.
            preprocessor: Fitted TransactionPreprocessor instance.
            fraud_threshold: Cutoff for high risk / automatic block.
            review_threshold: Cutoff for medium risk / manual triage.
        """
        self.model = model
        self.preprocessor = preprocessor
        self.fraud_threshold = fraud_threshold
        self.review_threshold = review_threshold
        self.explainer = FraudExplainer(model, feature_names=preprocessor.feature_names)

    def predict_single(
        self,
        transaction: Dict[str, Any],
        include_explanation: bool = False,
        top_k_factors: int = 5,
    ) -> Dict[str, Any]:
        """Scores a single transaction dictionary.

        Args:
            transaction: Dictionary containing 'amount', 'time', and 'V1'-'V28'.
            include_explanation: If True, calculates Tree SHAP top factors.
            top_k_factors: Number of SHAP factors to return.

        Returns:
            Dictionary with fraudProbability, isFraud, riskLevel, decision, latencyMs.
        """
        start_time = time.perf_counter()

        # Preprocess features
        features_array = self.preprocessor.transform_single(transaction)

        # Compute probability
        proba = self._get_probability(features_array)[0]
        risk_level, decision, is_fraud = self._classify_risk(proba)

        # Optional SHAP calculation
        top_factors: List[Dict[str, Any]] = []
        if include_explanation:
            top_factors = self.explainer.explain_instance(features_array, top_k=top_k_factors)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "fraudProbability": round(float(proba), 4),
            "isFraud": is_fraud,
            "riskLevel": risk_level,
            "decision": decision,
            "latencyMs": latency_ms,
            "thresholdUsed": self.fraud_threshold,
            "topFactors": top_factors,
        }

    def predict_batch(
        self,
        transactions: List[Dict[str, Any]],
        include_explanation: bool = False,
    ) -> List[Dict[str, Any]]:
        """Vectorized scoring of multiple transactions.

        Args:
            transactions: List of transaction dictionaries.
            include_explanation: Whether to compute SHAP for each transaction.

        Returns:
            List of prediction dictionaries.
        """
        if not transactions:
            return []

        start_time = time.perf_counter()
        df = pd.DataFrame(transactions)

        # Standardize column casing
        df.rename(columns={"amount": "Amount", "time": "Time"}, inplace=True)
        for i in range(1, 29):
            col_v = f"V{i}"
            if col_v.lower() in df.columns and col_v not in df.columns:
                df.rename(columns={col_v.lower(): col_v}, inplace=True)

        features_array = self.preprocessor.transform(df)
        probabilities = self._get_probability(features_array)

        results: List[Dict[str, Any]] = []
        total_latency = (time.perf_counter() - start_time) * 1000
        avg_latency = round(total_latency / len(transactions), 3)

        for idx, proba in enumerate(probabilities):
            risk_level, decision, is_fraud = self._classify_risk(proba)
            item: Dict[str, Any] = {
                "transactionIndex": idx,
                "fraudProbability": round(float(proba), 4),
                "isFraud": is_fraud,
                "riskLevel": risk_level,
                "decision": decision,
                "latencyMs": avg_latency,
            }
            if include_explanation:
                item["topFactors"] = self.explainer.explain_instance(
                    features_array[idx : idx + 1], top_k=3
                )
            results.append(item)

        return results

    def _get_probability(self, features_array: np.ndarray) -> np.ndarray:
        """Extracts probability of Class 1 (Fraud) from model."""
        if hasattr(self.model, "predict_proba"):
            proba_matrix = self.model.predict_proba(features_array)
            return proba_matrix[:, 1]

        # Raw prediction fallback
        raw_preds = self.model.predict(features_array)
        return np.asarray(raw_preds, dtype=float)

    def _classify_risk(self, probability: float) -> tuple[str, str, bool]:
        """Categorizes probability into risk level and actionable decision."""
        if probability >= self.fraud_threshold:
            return "HIGH", "BLOCK_TRANSACTION", True
        if probability >= self.review_threshold:
            return "MEDIUM", "MANUAL_REVIEW", False
        return "LOW", "APPROVE", False

    @classmethod
    def load(
        cls,
        model_path: Union[str, Path] = "models/fraud_detector_xgb.joblib",
        preprocessor_path: Union[str, Path] = "models/preprocessor.joblib",
        fraud_threshold: float = 0.35,
        review_threshold: float = 0.20,
    ) -> "FraudPredictor":
        """Loads serialized model and preprocessor artifacts from disk."""
        model_p = Path(model_path)
        prep_p = Path(preprocessor_path)

        if not model_p.is_file():
            raise FileNotFoundError(f"Model artifact missing at {model_p.resolve()}")
        if not prep_p.is_file():
            raise FileNotFoundError(f"Preprocessor artifact missing at {prep_p.resolve()}")

        model = joblib.load(model_p)
        preprocessor = TransactionPreprocessor.load(prep_p)

        logger.info("FraudPredictor successfully loaded from %s and %s", model_p, prep_p)
        return cls(
            model=model,
            preprocessor=preprocessor,
            fraud_threshold=fraud_threshold,
            review_threshold=review_threshold,
        )
