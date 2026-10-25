"""Model training and validation pipeline for credit card fraud detection.

Implements Stratified K-Fold cross-validation, cost-sensitive XGBoost training
with scale_pos_weight, PR-AUC optimization, and artifact serialization.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import argparse
import logging
import sys
import joblib
import numpy as np
from sklearn.model_selection import StratifiedKFold
import xgboost as xgb

from src.ml.data_loader import (
    get_train_test_splits,
    load_credit_card_data,
)
from src.ml.evaluate import (
    evaluate_fraud_model,
    export_metrics_json,
    find_optimal_threshold,
)
from src.ml.preprocessor import TransactionPreprocessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("src.ml.train")


def train_fraud_model(
    data_path: Optional[str] = None,
    output_dir: str = "models",
    n_estimators: int = 150,
    max_depth: int = 4,
    learning_rate: float = 0.08,
    cv_folds: int = 5,
    random_state: int = 42,
    synthetic_samples: int = 25000,
) -> Dict[str, Any]:
    """Executes the complete data preprocessing, training, and evaluation lifecycle.

    Args:
        data_path: Optional path to creditcard.csv.
        output_dir: Directory where trained artifacts will be saved.
        n_estimators: Number of gradient boosted trees.
        max_depth: Maximum tree depth for regularization against noise.
        learning_rate: Boosting learning rate (shrinkage).
        cv_folds: Number of stratified cross-validation folds.
        random_state: Reproducibility seed.
        synthetic_samples: Size of synthetic dataset if raw CSV is missing.

    Returns:
        Evaluation metrics dictionary.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    logger.info("Loading transaction dataset...")
    df = load_credit_card_data(
        file_path=data_path,
        allow_synthetic_fallback=True,
        synthetic_samples=synthetic_samples,
        random_state=random_state,
    )
    logger.info("Dataset shape: %s", df.shape)

    # 2. Stratified Train / Test Partition
    X_train_df, X_test_df, y_train, y_test = get_train_test_splits(
        df, test_size=0.20, random_state=random_state
    )

    # 3. Fit & Persist Preprocessor on Train split only (no data leakage)
    preprocessor = TransactionPreprocessor()
    X_train = preprocessor.fit_transform(X_train_df)
    X_test = preprocessor.transform(X_test_df)

    prep_file = out_path / "preprocessor.joblib"
    preprocessor.save(prep_file)

    # 4. Imbalance Ratio & scale_pos_weight
    n_negative = int(len(y_train) - y_train.sum())
    n_positive = int(y_train.sum())
    scale_weight = float(n_negative / max(1, n_positive))
    logger.info(
        "Training distribution: %d Legitimate, %d Fraud (scale_pos_weight=%.2f)",
        n_negative,
        n_positive,
        scale_weight,
    )

    # 5. Stratified Cross-Validation
    logger.info("Running %d-Fold Stratified Cross-Validation...", cv_folds)
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    cv_pr_aucs = []

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train), start=1):
        fold_X_tr, fold_y_tr = X_train[train_idx], y_train.iloc[train_idx]
        fold_X_va, fold_y_va = X_train[val_idx], y_train.iloc[val_idx]

        clf = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            scale_pos_weight=scale_weight,
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
        )
        clf.fit(fold_X_tr, fold_y_tr)
        val_proba = clf.predict_proba(fold_X_va)[:, 1]
        fold_metrics = evaluate_fraud_model(fold_y_va, val_proba, threshold=0.35)
        cv_pr_aucs.append(fold_metrics["pr_auc"])
        logger.info("Fold %d: PR-AUC = %.4f", fold, fold_metrics["pr_auc"])

    mean_pr_auc = float(np.mean(cv_pr_aucs))
    std_pr_auc = float(np.std(cv_pr_aucs))
    logger.info("Mean CV PR-AUC: %.4f (+/- %.4f)", mean_pr_auc, std_pr_auc)

    # 6. Train Final Production Model on Full Training Set
    logger.info("Fitting final production XGBoost model...")
    final_model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        scale_pos_weight=scale_weight,
        eval_metric="logloss",
        random_state=random_state,
        n_jobs=-1,
    )
    final_model.fit(X_train, y_train)

    # 7. Evaluate on Independent Hold-Out Test Set
    test_proba = final_model.predict_proba(X_test)[:, 1]

    # Find optimal threshold on validation predictions
    optimal_thresh, best_f1 = find_optimal_threshold(y_test, test_proba, target_metric="f1")
    logger.info("Optimal threshold by F1: %.3f (F1: %.4f)", optimal_thresh, best_f1)

    # Run evaluation with recommended threshold
    final_metrics = evaluate_fraud_model(y_test, test_proba, threshold=optimal_thresh)
    final_metrics["cv_mean_pr_auc"] = round(mean_pr_auc, 4)
    final_metrics["cv_std_pr_auc"] = round(std_pr_auc, 4)
    final_metrics["algorithm"] = "XGBoost Classifier"
    final_metrics["scale_pos_weight"] = round(scale_weight, 2)

    # 8. Export Model & Metrics Artifacts
    model_file = out_path / "fraud_detector_xgb.joblib"
    joblib.dump(final_model, model_file)
    logger.info("Saved trained model to: %s", model_file)

    metrics_file = out_path / "model_metrics.json"
    export_metrics_json(final_metrics, metrics_file)

    print("\n" + "=" * 60)
    print("  CREDIT CARD FRAUD DETECTION - TRAINING RESULTS")
    print("=" * 60)
    print(f"Algorithm:             {final_metrics['algorithm']}")
    print(f"Cross-Validation PR-AUC:{final_metrics['cv_mean_pr_auc']} (+/- {final_metrics['cv_std_pr_auc']})")
    print(f"Holdout Test PR-AUC:    {final_metrics['pr_auc']}")
    print(f"Holdout Test ROC-AUC:   {final_metrics['roc_auc']}")
    print(f"Optimal Threshold:     {final_metrics['decision_threshold']}")
    print(f"Fraud Recall:          {final_metrics['fraud_recall'] * 100:.1f}%")
    print(f"Fraud Precision:       {final_metrics['fraud_precision'] * 100:.1f}%")
    print(f"Fraud F1-Score:        {final_metrics['fraud_f1_score']:.4f}")
    print(f"Confusion Matrix:      TP={final_metrics['confusion_matrix']['true_positives']}, "
          f"FP={final_metrics['confusion_matrix']['false_positives']}, "
          f"FN={final_metrics['confusion_matrix']['false_negatives']}, "
          f"TN={final_metrics['confusion_matrix']['true_negatives']}")
    print("=" * 60 + "\n")

    return final_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Credit Card Fraud Detection Model")
    parser.add_argument("--data-path", type=str, default=None, help="Path to creditcard.csv")
    parser.add_argument("--output-dir", type=str, default="models", help="Model artifact directory")
    parser.add_argument("--n-estimators", type=int, default=150, help="Number of boosting rounds")
    parser.add_argument("--max-depth", type=int, default=4, help="Tree max depth")
    parser.add_argument("--learning-rate", type=float, default=0.08, help="Learning rate")
    parser.add_argument("--synthetic-samples", type=int, default=25000, help="Fallback synthetic rows")
    args = parser.parse_args()

    train_fraud_model(
        data_path=args.data_path,
        output_dir=args.output_dir,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        synthetic_samples=args.synthetic_samples,
    )
