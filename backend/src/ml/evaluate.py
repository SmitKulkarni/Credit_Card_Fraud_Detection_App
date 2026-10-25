"""Evaluation and diagnostic metrics for imbalanced fraud classification.

Calculates Precision-Recall AUC (PR-AUC), ROC-AUC, confusion matrices,
F1 scores, and financial cost-weighted penalty metrics.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import json
import logging
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)

# Business Cost Weights
DEFAULT_COST_FALSE_NEGATIVE = 500.0  # Missing a fraudulent transaction
DEFAULT_COST_FALSE_POSITIVE = 10.0   # Annoying a legitimate customer with 2FA/decline


def evaluate_fraud_model(
    y_true: Union[np.ndarray, List[int]],
    y_proba: Union[np.ndarray, List[float]],
    threshold: float = 0.35,
    cost_fn: float = DEFAULT_COST_FALSE_NEGATIVE,
    cost_fp: float = DEFAULT_COST_FALSE_POSITIVE,
) -> Dict[str, Any]:
    """Generates a complete diagnostic evaluation dictionary for fraud detection.

    Args:
        y_true: Ground truth binary targets (0=normal, 1=fraud).
        y_proba: Predicted probabilities of fraud (Class 1).
        threshold: Classification decision cutoff.
        cost_fn: Financial penalty weight for missed fraud.
        cost_fp: Financial penalty weight for false alarms.

    Returns:
        Dictionary with PR-AUC, ROC-AUC, confusion matrix, precision, recall, and cost metrics.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_proba = np.asarray(y_proba, dtype=float)
    y_pred = (y_proba >= threshold).astype(int)

    # Standard imbalanced metrics
    pr_auc = float(average_precision_score(y_true, y_proba))
    try:
        roc_auc = float(roc_auc_score(y_true, y_proba))
    except ValueError:
        roc_auc = 0.5

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = (int(val) for val in cm.ravel())

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    total_cost = (fn * cost_fn) + (fp * cost_fp)
    total_samples = len(y_true)
    fraud_count = int(np.sum(y_true))

    metrics: Dict[str, Any] = {
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "decision_threshold": round(threshold, 3),
        "fraud_precision": round(precision, 4),
        "fraud_recall": round(recall, 4),
        "fraud_f1_score": round(f1, 4),
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        },
        "financial_cost_score": round(total_cost, 2),
        "sample_counts": {
            "total": total_samples,
            "fraud_actual": fraud_count,
            "fraud_detected": tp,
            "fraud_missed": fn,
            "false_alarms": fp,
        },
    }

    logger.info(
        "Evaluation summary [Threshold=%.2f]: PR-AUC=%.4f, Recall=%.4f, Precision=%.4f, F1=%.4f",
        threshold,
        pr_auc,
        recall,
        precision,
        f1,
    )
    return metrics


def find_optimal_threshold(
    y_true: Union[np.ndarray, List[int]],
    y_proba: Union[np.ndarray, List[float]],
    target_metric: str = "f1",
) -> Tuple[float, float]:
    """Finds the probability threshold that maximizes F1 or minimizes business cost.

    Args:
        y_true: Ground truth binary targets.
        y_proba: Predicted probabilities of fraud.
        target_metric: Metric to optimize ('f1' or 'cost').

    Returns:
        Tuple of (optimal_threshold, best_metric_value).
    """
    y_true = np.asarray(y_true, dtype=int)
    y_proba = np.asarray(y_proba, dtype=float)

    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)

    if target_metric == "f1":
        # Avoid division by zero in f1 calculation
        f1_scores = np.divide(
            2 * (precisions * recalls),
            (precisions + recalls),
            out=np.zeros_like(precisions),
            where=(precisions + recalls) > 0,
        )
        best_idx = int(np.argmax(f1_scores[:-1])) if len(thresholds) > 0 else 0
        best_thresh = float(thresholds[best_idx]) if len(thresholds) > 0 else 0.5
        best_val = float(f1_scores[best_idx])
        return round(best_thresh, 3), round(best_val, 4)

    # Cost-based search
    candidate_thresholds = np.linspace(0.05, 0.95, 91)
    lowest_cost = float("inf")
    best_thresh = 0.35

    for t in candidate_thresholds:
        preds = (y_proba >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()
        cost = (fn * DEFAULT_COST_FALSE_NEGATIVE) + (fp * DEFAULT_COST_FALSE_POSITIVE)
        if cost < lowest_cost:
            lowest_cost = cost
            best_thresh = float(t)

    return round(best_thresh, 3), round(lowest_cost, 2)


def export_metrics_json(metrics: Dict[str, Any], filepath: Union[str, Path]) -> Path:
    """Exports metrics dictionary to a JSON file.

    Args:
        metrics: Metrics dictionary from evaluate_fraud_model.
        filepath: Destination path (e.g. models/model_metrics.json).

    Returns:
        Path to the saved JSON file.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Saved model metrics to: %s", path)
    return path
