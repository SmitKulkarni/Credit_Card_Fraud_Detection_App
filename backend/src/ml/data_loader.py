"""Data loader and ingestion module for credit card transactions.

Supports ingestion of the European cardholder benchmark dataset (creditcard.csv)
and provides an automated synthetic generator fallback for self-contained execution.
"""

from pathlib import Path
from typing import Optional, Tuple
import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Expected schema constants
FEATURE_COLUMNS = [f"V{i}" for i in range(1, 29)]
NUMERIC_COLUMNS = ["Time"] + FEATURE_COLUMNS + ["Amount"]
TARGET_COLUMN = "Class"
ALL_COLUMNS = NUMERIC_COLUMNS + [TARGET_COLUMN]


def generate_synthetic_transactions(
    n_samples: int = 15000,
    fraud_ratio: float = 0.002,
    random_state: int = 42,
) -> pd.DataFrame:
    """Generates synthetic credit card transactions matching benchmark distributions.

    Mimics the European cardholder dataset statistics (28 PCA components,
    log-normal transaction amounts, 48-hour time progression, and severe class imbalance).

    Args:
        n_samples: Total number of transactions to synthesize.
        fraud_ratio: Fraction of fraudulent transactions (default 0.2%).
        random_state: Seed for reproducibility.

    Returns:
        pd.DataFrame containing Time, V1-V28, Amount, and Class columns.
    """
    rng = np.random.RandomState(random_state)
    n_fraud = max(1, int(n_samples * fraud_ratio))
    n_legit = n_samples - n_fraud

    logger.info(
        "Generating synthetic dataset: %d samples (%d legitimate, %d fraud).",
        n_samples,
        n_legit,
        n_fraud,
    )

    # 1. Legitimate transactions: standard Gaussian PCA features
    v_legit = rng.normal(loc=0.0, scale=1.0, size=(n_legit, 28))
    # Time over simulated 48 hours (172,800 seconds)
    time_legit = np.sort(rng.uniform(low=0.0, high=172800.0, size=n_legit))
    # Amount: log-normal distribution, median ~$25
    amount_legit = np.round(rng.lognormal(mean=3.0, sigma=1.2, size=n_legit), 2)
    amount_legit = np.clip(amount_legit, 0.5, 5000.0)

    # 2. Fraudulent transactions: shifted distributions on key fraud-predictive components
    # Features V4, V11 often higher in fraud; V10, V12, V14, V17 strongly negative
    v_fraud = rng.normal(loc=0.0, scale=1.5, size=(n_fraud, 28))
    v_fraud[:, 3] += rng.uniform(2.5, 5.0, size=n_fraud)    # V4 shift
    v_fraud[:, 9] -= rng.uniform(3.0, 6.0, size=n_fraud)    # V10 shift
    v_fraud[:, 10] += rng.uniform(2.0, 5.0, size=n_fraud)   # V11 shift
    v_fraud[:, 11] -= rng.uniform(3.5, 7.0, size=n_fraud)   # V12 shift
    v_fraud[:, 13] -= rng.uniform(4.0, 8.0, size=n_fraud)   # V14 shift
    v_fraud[:, 16] -= rng.uniform(3.0, 6.0, size=n_fraud)   # V17 shift

    time_fraud = rng.uniform(low=0.0, high=172800.0, size=n_fraud)
    # Fraud amounts often bifurcate: tiny probes (<$5) or larger purchases
    amount_fraud = np.where(
        rng.rand(n_fraud) > 0.4,
        np.round(rng.uniform(100.0, 1800.0, size=n_fraud), 2),
        np.round(rng.uniform(1.0, 15.0, size=n_fraud), 2),
    )

    # Combine legitimate and fraud populations
    v_all = np.vstack([v_legit, v_fraud])
    time_all = np.concatenate([time_legit, time_fraud])
    amount_all = np.concatenate([amount_legit, amount_fraud])
    classes = np.concatenate([np.zeros(n_legit, dtype=int), np.ones(n_fraud, dtype=int)])

    data_dict = {"Time": time_all}
    for idx, col_name in enumerate(FEATURE_COLUMNS):
        data_dict[col_name] = v_all[:, idx]
    data_dict["Amount"] = amount_all
    data_dict[TARGET_COLUMN] = classes

    df = pd.DataFrame(data_dict)
    # Shuffle to interleave timestamps
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df


def load_credit_card_data(
    file_path: Optional[str] = None,
    allow_synthetic_fallback: bool = True,
    synthetic_samples: int = 20000,
    random_state: int = 42,
) -> pd.DataFrame:
    """Loads credit card transactions from disk or falls back to synthetic generation.

    Args:
        file_path: Optional path to a CSV dataset. If None, checks data/raw/creditcard.csv.
        allow_synthetic_fallback: If True, generates a synthetic dataset when file is missing.
        synthetic_samples: Number of synthetic transactions to create if fallback is triggered.
        random_state: Seed for reproducibility.

    Returns:
        pd.DataFrame containing validated transactions.

    Raises:
        FileNotFoundError: If the dataset file does not exist and fallback is disabled.
        ValueError: If the dataset is missing mandatory schema columns.
    """
    path = Path(file_path) if file_path else Path("data/raw/creditcard.csv")

    if path.is_file():
        logger.info("Loading transaction dataset from: %s", path)
        df = pd.read_csv(path)
    else:
        if allow_synthetic_fallback:
            logger.warning(
                "Dataset file not found at '%s'. Generating %d synthetic transactions.",
                path,
                synthetic_samples,
            )
            df = generate_synthetic_transactions(
                n_samples=synthetic_samples,
                random_state=random_state,
            )
        else:
            raise FileNotFoundError(f"Credit card dataset not found at {path.resolve()}")

    validate_dataframe_schema(df)
    return df


def validate_dataframe_schema(df: pd.DataFrame) -> None:
    """Validates that the dataframe contains the required columns and non-null values.

    Args:
        df: Pandas DataFrame to validate.

    Raises:
        ValueError: If required columns are missing or if null values are detected.
    """
    missing_cols = [col for col in ALL_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    null_counts = df[ALL_COLUMNS].isnull().sum().sum()
    if null_counts > 0:
        raise ValueError(f"Dataset contains {null_counts} null values across features.")


def get_train_test_splits(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Splits data into stratified train and test partitions.

    Args:
        df: Input DataFrame containing features and Class column.
        test_size: Proportion of the dataset to include in the test split.
        random_state: Random state for reproducibility.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test).
    """
    features = df[NUMERIC_COLUMNS]
    target = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=test_size,
        stratify=target,
        random_state=random_state,
    )

    logger.info(
        "Stratified split completed: Train=%d (Frauds=%d), Test=%d (Frauds=%d)",
        len(X_train),
        int(y_train.sum()),
        len(X_test),
        int(y_test.sum()),
    )
    return X_train, X_test, y_train, y_test
