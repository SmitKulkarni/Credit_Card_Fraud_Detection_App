"""Health and model metadata routes."""

from datetime import datetime, timezone
import json
import logging
import time
from fastapi import APIRouter, HTTPException, Request

from src.api.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health & System"])
START_TIME = time.time()


@router.get("/health", summary="Service Health & Liveness Check")
async def health_check(request: Request):
    """Returns liveness, uptime, and ML model readiness status."""
    settings = get_settings()
    predictor = getattr(request.app.state, "predictor", None)
    model_loaded = predictor is not None

    return {
        "status": "healthy" if model_loaded else "degraded",
        "appName": settings.APP_NAME,
        "appVersion": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "modelLoaded": model_loaded,
        "uptimeSeconds": round(time.time() - START_TIME, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/model/metadata", summary="Active Model Performance & Registry Metadata")
async def model_metadata(request: Request):
    """Returns active model benchmarks (PR-AUC, ROC-AUC, decision thresholds) from the registry."""
    settings = get_settings()
    metrics_path = settings.metrics_path

    if not metrics_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Model metrics metadata not found at {metrics_path}. Has training been run?",
        )

    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
    except Exception as exc:
        logger.error("Failed to parse model metrics JSON: %s", exc)
        raise HTTPException(status_code=500, detail="Could not read model metadata file.")

    return {
        "modelName": settings.MODEL_FILENAME,
        "algorithm": metrics_data.get("algorithm", "XGBoost Classifier"),
        "metrics": metrics_data,
        "activeThresholds": {
            "fraudThreshold": settings.FRAUD_PROBABILITY_THRESHOLD,
            "reviewThreshold": settings.REVIEW_PROBABILITY_THRESHOLD,
        },
        "retrievedAt": datetime.now(timezone.utc).isoformat(),
    }
