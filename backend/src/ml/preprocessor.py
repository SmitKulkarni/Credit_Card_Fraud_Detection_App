"""Feature preprocessing pipeline for credit card fraud detection.

Handles outlier-resistant scaling for Amount via RobustScaler,
Time normalization, and alignment of PCA components V1 to V28.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)

FEATURE_NAMES = ["scaled_amount", "scaled_time"] + [f"V{i}" for i in range(1, 29)]


class TransactionPreprocessor(BaseEstimator, TransformerMixin):
    """Preprocessing transformer for credit card transaction records.

    Applies RobustScaler to transaction 'Amount' to resist extreme monetary outliers,
    scales transaction 'Time', and outputs an aligned feature matrix ready for
    tree-based or linear classifiers.
    """

    def __init__(self) -> None:
        """Initializes scaler subcomponents."""
        self.amount_scaler = RobustScaler()
        self.time_scaler = RobustScaler()
        self.pca_features: List[str] = [f"V{i}" for i in range(1, 29)]
        self.is_fitted: bool = False

    @property
    def feature_names(self) -> List[str]:
        """Returns the ordered list of transformed feature names."""
        return FEATURE_NAMES

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Any] = None) -> "TransactionPreprocessor":
        """Fits scalers on the training transaction distribution.

        Args:
            X: Input DataFrame containing 'Amount', 'Time', and 'V1'-'V28'.
            y: Ignored (present for scikit-learn API compatibility).

        Returns:
            self: The fitted preprocessor instance.
        """
        df = self._ensure_dataframe(X)
        logger.info("Fitting TransactionPreprocessor on %d records.", len(df))

        self.amount_scaler.fit(df[["Amount"]])
        self.time_scaler.fit(df[["Time"]])
        self.is_fitted = True
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray, Dict[str, Any]]) -> np.ndarray:
        """Transforms input transaction data into scaled numeric feature arrays.

        Args:
            X: DataFrame, array, or single dictionary of transaction features.

        Returns:
            np.ndarray of shape (n_samples, 30) with ordered features:
            [scaled_amount, scaled_time, V1, V2, ..., V28].

        Raises:
            RuntimeError: If called before fit().
        """
        if not self.is_fitted:
            raise RuntimeError("TransactionPreprocessor must be fitted before calling transform().")

        df = self._ensure_dataframe(X)

        scaled_amount = self.amount_scaler.transform(df[["Amount"]])
        scaled_time = self.time_scaler.transform(df[["Time"]])
        pca_matrix = df[self.pca_features].to_numpy(dtype=np.float32)

        # Concatenate into unified 30-feature vector
        processed_matrix = np.hstack([scaled_amount, scaled_time, pca_matrix])
        return processed_matrix.astype(np.float32)

    def fit_transform(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Any] = None) -> np.ndarray:
        """Fits and transforms the input dataset in a single call."""
        return self.fit(X, y).transform(X)

    def transform_single(self, transaction: Dict[str, Any]) -> np.ndarray:
        """Transforms a single transaction dictionary into a 2D array of shape (1, 30).

        Args:
            transaction: Dictionary with 'Amount', 'Time', and 'V1'-'V28' keys.

        Returns:
            np.ndarray of shape (1, 30).
        """
        # Ensure all expected keys are present, defaulting missing V-features to 0.0
        cleaned: Dict[str, float] = {
            "Amount": float(transaction.get("amount", transaction.get("Amount", 0.0))),
            "Time": float(transaction.get("time", transaction.get("Time", 0.0))),
        }
        for feat in self.pca_features:
            cleaned[feat] = float(transaction.get(feat, transaction.get(feat.lower(), 0.0)))

        df = pd.DataFrame([cleaned])
        return self.transform(df)

    def save(self, filepath: Union[str, Path]) -> Path:
        """Serializes the fitted preprocessor using joblib.

        Args:
            filepath: Destination file path (e.g. models/preprocessor.joblib).

        Returns:
            Path object of the saved artifact.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Saved preprocessor artifact to: %s", path)
        return path

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "TransactionPreprocessor":
        """Loads a fitted preprocessor artifact from disk.

        Args:
            filepath: Path to the .joblib file.

        Returns:
            Fitted TransactionPreprocessor instance.
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Preprocessor artifact not found at: {path}")
        instance = joblib.load(path)
        logger.info("Loaded preprocessor artifact from: %s", path)
        return instance

    def _ensure_dataframe(self, X: Union[pd.DataFrame, np.ndarray, Dict[str, Any]]) -> pd.DataFrame:
        """Converts diverse input types into a standardized DataFrame."""
        if isinstance(X, dict):
            return pd.DataFrame([X])
        if isinstance(X, pd.DataFrame):
            return X.copy()
        if isinstance(X, np.ndarray):
            # Assume ordered: [Time, V1..V28, Amount]
            if X.ndim == 1:
                X = X.reshape(1, -1)
            columns = ["Time"] + self.pca_features + ["Amount"]
            if X.shape[1] != len(columns):
                raise ValueError(
                    f"Array shape {X.shape} incompatible. Expected {len(columns)} columns."
                )
            return pd.DataFrame(X, columns=columns)
        raise TypeError(f"Unsupported data type for preprocessor: {type(X)}")
