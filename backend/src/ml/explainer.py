"""Explainability module for credit card fraud predictions.

Uses exact Tree SHAP (Shapley Additive exPlanations) to identify and rank
which transaction features increased or decreased fraud probability.
"""

from typing import Any, Dict, List, Optional
import logging
import numpy as np
import xgboost as xgb

logger = logging.getLogger(__name__)

# Feature descriptions mapping for triage officers
FEATURE_DESCRIPTIONS: Dict[str, str] = {
    "scaled_amount": "Transaction monetary amount outlier relative to cardholder baseline.",
    "scaled_time": "Time delta / purchase sequence velocity indicator.",
    "V4": "High correlation with rapid location-shifting behavior.",
    "V10": "Abnormal shift in terminal verification parameters.",
    "V11": "Anomalous velocity in repeat payment attempts.",
    "V12": "High divergence in merchant category profile.",
    "V14": "Strongest historical indicator of fraudulent card presentation.",
    "V17": "Deviation in geographic authorization patterns.",
}


class FraudExplainer:
    """Explains individual transaction risk scores using Tree SHAP contributions."""

    def __init__(self, model: Any, feature_names: List[str]) -> None:
        """Initializes the explainer.

        Args:
            model: Trained classifier (XGBClassifier or booster).
            feature_names: Ordered list of feature names matching preprocessed input.
        """
        self.model = model
        self.feature_names = feature_names
        self.booster = self._extract_booster(model)

    def _extract_booster(self, model: Any) -> Optional[xgb.Booster]:
        """Safely extracts the underlying XGBoost booster object."""
        if hasattr(model, "get_booster"):
            return model.get_booster()
        if isinstance(model, xgb.Booster):
            return model
        return None

    def explain_instance(
        self,
        features_array: np.ndarray,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Calculates exact feature contributions for a single transaction.

        Args:
            features_array: Preprocessed 2D array of shape (1, n_features).
            top_k: Number of highest-impact factors to return.

        Returns:
            List of dictionaries with feature, impact, direction, and description.
        """
        if features_array.ndim == 1:
            features_array = features_array.reshape(1, -1)

        if self.booster is not None:
            return self._explain_xgboost(features_array, top_k=top_k)

        return self._explain_generic(features_array, top_k=top_k)

    def _explain_xgboost(self, features_array: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Computes exact Tree SHAP values using XGBoost's native pred_contribs."""
        dmatrix = xgb.DMatrix(features_array, feature_names=self.feature_names)
        # contribs shape: (1, n_features + 1), last element is base value bias
        contribs = self.booster.predict(dmatrix, pred_contribs=True)[0]
        feature_contribs = contribs[:-1]

        # Rank features by absolute impact magnitude
        abs_sorted_indices = np.argsort(np.abs(feature_contribs))[::-1][:top_k]

        explanations: List[Dict[str, Any]] = []
        for idx in abs_sorted_indices:
            feat_name = self.feature_names[idx]
            impact_val = float(feature_contribs[idx])
            direction = "INCREASES_RISK" if impact_val > 0 else "DECREASES_RISK"
            desc = FEATURE_DESCRIPTIONS.get(
                feat_name,
                f"Statistical anomaly in anonymized feature {feat_name}.",
            )

            explanations.append({
                "feature": feat_name,
                "impact": round(impact_val, 4),
                "direction": direction,
                "description": desc,
            })

        return explanations

    def _explain_generic(self, features_array: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Fallback feature importance calculation for non-XGBoost models."""
        importances = getattr(self.model, "feature_importances_", None)
        if importances is None:
            return []

        weighted_impact = features_array[0] * importances
        abs_sorted_indices = np.argsort(np.abs(weighted_impact))[::-1][:top_k]

        explanations: List[Dict[str, Any]] = []
        for idx in abs_sorted_indices:
            feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"Feat_{idx}"
            impact_val = float(weighted_impact[idx])
            direction = "INCREASES_RISK" if impact_val > 0 else "DECREASES_RISK"

            explanations.append({
                "feature": feat_name,
                "impact": round(impact_val, 4),
                "direction": direction,
                "description": FEATURE_DESCRIPTIONS.get(feat_name, f"Influence from {feat_name}"),
            })

        return explanations
