"""Population Stability Index (PSI) and data drift monitoring engine.

Detects statistical distribution shifts in incoming transaction streams
compared against the baseline training distribution to trigger retraining alerts.
"""

from typing import Any, Dict, List, Optional, Union
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Key fraud-predictive features monitored for distribution drift
MONITORED_FEATURES = ["Amount", "Time", "V4", "V10", "V11", "V12", "V14", "V17"]


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_buckets: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """Calculates the Population Stability Index (PSI) between two numeric samples.

    Args:
        expected: Reference/baseline population array.
        actual: Incoming/monitored population array.
        num_buckets: Number of quantile bins to partition the distribution.
        epsilon: Small constant to prevent zero-division in log calculation.

    Returns:
        PSI value as float.
    """
    expected = np.asarray(expected, dtype=float).ravel()
    actual = np.asarray(actual, dtype=float).ravel()

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine quantile bin edges from reference distribution
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bin_edges = np.percentile(expected, percentiles)
    bin_edges = np.unique(bin_edges)

    if len(bin_edges) < 2:
        return 0.0

    # Bin counts
    exp_counts, _ = np.histogram(expected, bins=bin_edges)
    act_counts, _ = np.histogram(actual, bins=bin_edges)

    # Convert to fractions
    exp_pct = exp_counts / max(1, len(expected))
    act_pct = act_counts / max(1, len(actual))

    # Apply epsilon smoothing
    exp_pct = np.clip(exp_pct, epsilon, 1.0)
    act_pct = np.clip(act_pct, epsilon, 1.0)

    # Re-normalize
    exp_pct /= np.sum(exp_pct)
    act_pct /= np.sum(act_pct)

    # PSI calculation: sum((actual - expected) * ln(actual / expected))
    psi_vector = (act_pct - exp_pct) * np.log(act_pct / exp_pct)
    return float(np.sum(psi_vector))


class DriftDetector:
    """Monitors incoming transaction batches for data drift against baseline distributions."""

    def __init__(
        self,
        baseline_df: Optional[pd.DataFrame] = None,
        monitored_features: Optional[List[str]] = None,
    ) -> None:
        """Initializes the drift detector with baseline distributions.

        Args:
            baseline_df: Historical training DataFrame.
            monitored_features: List of feature names to track.
        """
        self.monitored_features = monitored_features or MONITORED_FEATURES
        self.baseline_distributions: Dict[str, np.ndarray] = {}

        if baseline_df is not None:
            self.fit_baseline(baseline_df)

    def fit_baseline(self, df: pd.DataFrame) -> "DriftDetector":
        """Captures reference distributions for all monitored features."""
        for feat in self.monitored_features:
            if feat in df.columns:
                self.baseline_distributions[feat] = df[feat].to_numpy(dtype=float)
            elif feat.lower() in df.columns:
                self.baseline_distributions[feat] = df[feat.lower()].to_numpy(dtype=float)
        logger.info(
            "Fitted DriftDetector baseline on %d features with %d samples.",
            len(self.baseline_distributions),
            len(df),
        )
        return self

    def evaluate_batch_drift(
        self,
        batch_data: Union[pd.DataFrame, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Calculates PSI scores across all monitored features for an incoming batch.

        Args:
            batch_data: DataFrame or list of transaction dictionaries.

        Returns:
            Dictionary containing overall driftStatus, averagePsi, and per-feature breakdown.
        """
        if isinstance(batch_data, list):
            df = pd.DataFrame(batch_data)
        else:
            df = batch_data.copy()

        if len(df) == 0:
            return {
                "driftStatus": "NO_DATA",
                "averagePsi": 0.0,
                "featurePsiScores": {},
                "recommendation": "Batch contains no records to evaluate.",
            }

        feature_scores: Dict[str, Dict[str, Any]] = {}
        psi_values: List[float] = []

        for feat in self.monitored_features:
            if feat not in self.baseline_distributions:
                continue

            target_col = feat if feat in df.columns else (feat.lower() if feat.lower() in df.columns else None)
            if target_col is None:
                continue

            actual_vals = df[target_col].to_numpy(dtype=float)
            psi = calculate_psi(self.baseline_distributions[feat], actual_vals)
            psi_values.append(psi)

            # Categorize individual feature drift
            if psi >= 0.20:
                feat_status = "CRITICAL_DRIFT"
            elif psi >= 0.10:
                feat_status = "MODERATE_DRIFT"
            else:
                feat_status = "STABLE"

            feature_scores[feat] = {
                "psi": round(psi, 4),
                "status": feat_status,
            }

        avg_psi = float(np.mean(psi_values)) if psi_values else 0.0

        if avg_psi >= 0.20:
            status = "CRITICAL_DRIFT"
            recommendation = "Severe distribution divergence detected. Urgent model retraining recommended."
        elif avg_psi >= 0.10:
            status = "MODERATE_DRIFT"
            recommendation = "Moderate drift observed. Schedule model re-calibration."
        else:
            status = "NO_DRIFT"
            recommendation = "Transaction distribution aligns with historical baseline. Model is healthy."

        return {
            "driftStatus": status,
            "averagePsi": round(avg_psi, 4),
            "sampleCount": len(df),
            "recommendation": recommendation,
            "featurePsiScores": feature_scores,
        }
