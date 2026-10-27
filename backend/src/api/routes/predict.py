"""Prediction endpoints for single and batch credit card transactions."""

from typing import List
import logging
from fastapi import APIRouter, HTTPException, Query, Request

from src.api.schemas.transaction import (
    BatchPredictionResponse,
    BatchTransactionRequest,
    FactorExplanation,
    PredictionResponse,
    PresetScenario,
    TransactionInput,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Fraud Predictions"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Evaluate Single Transaction Risk",
)
async def predict_single_transaction(
    payload: TransactionInput,
    request: Request,
    includeExplanation: bool = Query(
        default=True,
        description="Attach Tree SHAP top-factor risk breakdown.",
    ),
) -> PredictionResponse:
    """Evaluates a single transaction against the production XGBoost classifier.

    Calculates the probability of fraud, risk level, actionable decision,
    latency, and per-feature Tree SHAP contributions.
    """
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Model predictor service not loaded. Check /health status.",
        )

    features_dict = payload.to_feature_dict()
    raw_result = predictor.predict_single(
        transaction=features_dict,
        include_explanation=includeExplanation,
        top_k_factors=5,
    )

    # Format factors
    factors = [
        FactorExplanation(
            feature=f["feature"],
            impact=f["impact"],
            direction=f["direction"],
            description=f["description"],
        )
        for f in raw_result.get("topFactors", [])
    ]

    response = PredictionResponse(
        transactionId=payload.transactionId or "tx_unknown",
        fraudProbability=raw_result["fraudProbability"],
        isFraud=raw_result["isFraud"],
        riskLevel=raw_result["riskLevel"],
        decision=raw_result["decision"],
        latencyMs=raw_result["latencyMs"],
        thresholdUsed=raw_result["thresholdUsed"],
        topFactors=factors,
    )

    # Update in-memory session stats
    stats = getattr(request.app.state, "stats", None)
    if stats is not None:
        stats.record_prediction(response.riskLevel, response.latencyMs)

    # Persist to database audit log
    try:
        from src.db.database import save_audit_record
        save_audit_record(
            transaction_id=response.transactionId,
            amount=payload.amount,
            time_delta=payload.time,
            fraud_probability=response.fraudProbability,
            is_fraud=response.isFraud,
            risk_level=response.riskLevel,
            decision=response.decision,
            latency_ms=response.latencyMs,
            top_factors=[f.model_dump() for f in response.topFactors],
        )
    except Exception as db_exc:
        logger.warning("Audit persistence failed (non-blocking): %s", db_exc)

    return response


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Vectorized Batch Transaction Evaluation",
)
async def predict_batch_transactions(
    payload: BatchTransactionRequest,
    request: Request,
) -> BatchPredictionResponse:
    """Evaluates up to 1,000 transactions in parallel using vectorized transformations."""
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model predictor service not loaded.")

    raw_dicts = [tx.to_feature_dict() for tx in payload.transactions]
    batch_raw = predictor.predict_batch(
        transactions=raw_dicts,
        include_explanation=payload.includeExplanation,
    )

    results: List[PredictionResponse] = []
    fraud_count = 0
    review_count = 0
    approved_count = 0

    for idx, item in enumerate(batch_raw):
        tx_id = payload.transactions[idx].transactionId or f"tx_batch_{idx}"
        factors = [
            FactorExplanation(
                feature=f["feature"],
                impact=f["impact"],
                direction=f["direction"],
                description=f["description"],
            )
            for f in item.get("topFactors", [])
        ]

        if item["riskLevel"] == "HIGH":
            fraud_count += 1
        elif item["riskLevel"] == "MEDIUM":
            review_count += 1
        else:
            approved_count += 1

        pred = PredictionResponse(
            transactionId=tx_id,
            fraudProbability=item["fraudProbability"],
            isFraud=item["isFraud"],
            riskLevel=item["riskLevel"],
            decision=item["decision"],
            latencyMs=item["latencyMs"],
            thresholdUsed=predictor.fraud_threshold,
            topFactors=factors,
        )
        results.append(pred)

    total = len(results)
    avg_latency = (
        round(sum(r.latencyMs for r in results) / total, 2) if total > 0 else 0.0
    )

    # Update stats
    stats = getattr(request.app.state, "stats", None)
    if stats is not None:
        for r in results:
            stats.record_prediction(r.riskLevel, r.latencyMs)

    # Persist batch audit records
    try:
        from src.db.database import save_audit_record
        for idx, r in enumerate(results):
            tx_in = payload.transactions[idx]
            save_audit_record(
                transaction_id=r.transactionId,
                amount=tx_in.amount,
                time_delta=tx_in.time,
                fraud_probability=r.fraudProbability,
                is_fraud=r.isFraud,
                risk_level=r.riskLevel,
                decision=r.decision,
                latency_ms=r.latencyMs,
            )
    except Exception as db_exc:
        logger.warning("Batch audit persistence error: %s", db_exc)

    return BatchPredictionResponse(
        totalProcessed=total,
        fraudDetected=fraud_count,
        manualReviewCount=review_count,
        approvedCount=approved_count,
        averageLatencyMs=avg_latency,
        results=results,
    )


@router.get(
    "/predict/presets",
    response_model=List[PresetScenario],
    summary="Pre-configured Demo Scenarios",
)
async def get_preset_scenarios() -> List[PresetScenario]:
    """Returns curated demo presets (Normal, Suspicious, Fraud) for 1-click verification."""
    return [
        PresetScenario(
            presetId="legitimate_grocery",
            title="Standard Retail Purchase (₹2,050 Rupees)",
            riskCategory="LOW",
            description="Routine low-value retail purchase with standard cardholder behavioral patterns in Rupees.",
            payload=TransactionInput(
                transactionId="TX-892104",
                amount=2050.00,
                time=450.0,
                features={f"V{i}": 0.05 for i in range(1, 29)},
            ),
        ),
        PresetScenario(
            presetId="suspicious_velocity",
            title="Suspicious E-Commerce Velocity (₹56,500 Rupees)",
            riskCategory="MEDIUM",
            description="Elevated transaction amount in Rupees with moderate divergence in device and velocity features.",
            payload=TransactionInput(
                transactionId="TX-492105",
                amount=56500.00,
                time=1200.0,
                features={
                    **{f"V{i}": 0.1 for i in range(1, 29)},
                    "V4": 1.95,
                    "V11": 1.80,
                    "V14": -1.85,
                    "V12": -1.90,
                },
            ),
        ),
        PresetScenario(
            presetId="confirmed_fraud",
            title="Confirmed Fraudulent Anomaly (₹1,24,000 Rupees)",
            riskCategory="HIGH",
            description="Severe anomaly on critical fraud indicators (V14, V12, V17) with high monetary value in Rupees.",
            payload=TransactionInput(
                transactionId="TX-792106",
                amount=124000.00,
                time=800.0,
                features={
                    **{f"V{i}": -0.5 for i in range(1, 29)},
                    "V4": 4.10,
                    "V10": -4.80,
                    "V11": 3.50,
                    "V12": -6.20,
                    "V14": -7.10,
                    "V17": -4.90,
                },
            ),
        ),
    ]
