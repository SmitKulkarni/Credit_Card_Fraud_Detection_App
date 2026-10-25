"""Pydantic schemas for fraud detection API request and response validation."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, model_validator


class TransactionInput(BaseModel):
    """Schema for incoming transaction payload to evaluate."""

    transactionId: Optional[str] = Field(
        default=None,
        description="Unique external identifier for the transaction (auto-generated if omitted).",
        examples=["tx_88129014"],
    )
    amount: float = Field(
        ...,
        ge=0.0,
        description="Transaction monetary amount.",
        examples=[149.62],
    )
    time: float = Field(
        default=0.0,
        ge=0.0,
        description="Seconds elapsed since the initial reference timestamp.",
        examples=[406.0],
    )
    features: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional dictionary containing PCA features V1 through V28.",
        examples=[{
            "V1": -2.31, "V2": 1.95, "V3": -1.60, "V4": 3.99, "V5": -0.52,
            "V10": -4.21, "V11": 3.12, "V12": -5.60, "V14": -6.10, "V17": -4.50,
        }],
    )

    # Optional flat fields V1 to V28 directly on root level for flexibility
    v1: Optional[float] = None
    v2: Optional[float] = None
    v3: Optional[float] = None
    v4: Optional[float] = None
    v5: Optional[float] = None
    v6: Optional[float] = None
    v7: Optional[float] = None
    v8: Optional[float] = None
    v9: Optional[float] = None
    v10: Optional[float] = None
    v11: Optional[float] = None
    v12: Optional[float] = None
    v13: Optional[float] = None
    v14: Optional[float] = None
    v15: Optional[float] = None
    v16: Optional[float] = None
    v17: Optional[float] = None
    v18: Optional[float] = None
    v19: Optional[float] = None
    v20: Optional[float] = None
    v21: Optional[float] = None
    v22: Optional[float] = None
    v23: Optional[float] = None
    v24: Optional[float] = None
    v25: Optional[float] = None
    v26: Optional[float] = None
    v27: Optional[float] = None
    v28: Optional[float] = None

    @model_validator(mode="after")
    def populate_defaults(self) -> "TransactionInput":
        """Ensures transactionId is generated if not provided."""
        if not self.transactionId:
            self.transactionId = f"tx_{uuid.uuid4().hex[:10]}"
        return self

    def to_feature_dict(self) -> Dict[str, float]:
        """Flattens input into a standardized dictionary with Amount, Time, and V1-V28."""
        result: Dict[str, float] = {
            "Amount": float(self.amount),
            "Time": float(self.time),
        }

        # First check nested features dict
        nested = self.features or {}
        for i in range(1, 29):
            col_v = f"V{i}"
            val = nested.get(col_v, nested.get(col_v.lower()))
            if val is None:
                # Check root-level field
                val = getattr(self, f"v{i}", 0.0)
            result[col_v] = float(val if val is not None else 0.0)

        return result


class FactorExplanation(BaseModel):
    """Schema for individual feature contribution factor."""

    feature: str = Field(..., description="Feature name (e.g. V14, Amount)")
    impact: float = Field(..., description="Shapley impact magnitude")
    direction: str = Field(..., description="INCREASES_RISK or DECREASES_RISK")
    description: str = Field(..., description="Contextual analyst explanation")


class PredictionResponse(BaseModel):
    """Schema returned for a scored transaction."""

    transactionId: str = Field(..., description="Transaction identifier")
    fraudProbability: float = Field(..., description="Calibrated risk score between 0.0 and 1.0")
    isFraud: bool = Field(..., description="True if probability exceeds the fraud decision threshold")
    riskLevel: str = Field(..., description="Risk tier: LOW, MEDIUM, or HIGH")
    decision: str = Field(..., description="Actionable decision: APPROVE, MANUAL_REVIEW, or BLOCK_TRANSACTION")
    latencyMs: float = Field(..., description="Inference processing latency in milliseconds")
    thresholdUsed: float = Field(..., description="Decision cutoff threshold applied")
    topFactors: List[FactorExplanation] = Field(
        default_factory=list,
        description="Ranked list of key features influencing the prediction",
    )
    evaluatedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 evaluation timestamp",
    )


class BatchTransactionRequest(BaseModel):
    """Schema for multi-transaction batch scoring requests."""

    transactions: List[TransactionInput] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Array of transactions to evaluate in parallel (max 1,000 items).",
    )
    includeExplanation: bool = Field(
        default=False,
        description="Whether to attach SHAP factor breakdowns to each transaction in the batch.",
    )


class BatchPredictionResponse(BaseModel):
    """Summary response for batch evaluation."""

    totalProcessed: int = Field(..., description="Total transactions scored")
    fraudDetected: int = Field(..., description="Number of transactions flagged as fraud")
    manualReviewCount: int = Field(..., description="Number of transactions flagged for manual review")
    approvedCount: int = Field(..., description="Number of transactions approved")
    averageLatencyMs: float = Field(..., description="Average inference latency per item in ms")
    results: List[PredictionResponse] = Field(..., description="Individual item prediction results")


class PresetScenario(BaseModel):
    """Pre-configured transaction scenario for demonstration."""

    presetId: str
    title: str
    riskCategory: str
    description: str
    payload: TransactionInput
