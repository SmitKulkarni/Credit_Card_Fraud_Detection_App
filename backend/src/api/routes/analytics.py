"""Analytics, session statistics, audit trails, and drift monitoring routes."""

from typing import List, Optional
import numpy as np
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.schemas.transaction import BatchTransactionRequest
from src.db.database import get_db
from src.db.models import TransactionAuditRecord

router = APIRouter(tags=["Analytics & Monitoring"])


class SessionStatsTracker:
    """In-memory rolling statistics collector for live session scoring."""

    def __init__(self, max_history: int = 5000) -> None:
        self.total_scored: int = 0
        self.fraud_blocked: int = 0
        self.manual_reviews: int = 0
        self.approved: int = 0
        self.latencies: List[float] = []
        self.max_history = max_history

    def record_prediction(self, risk_level: str, latency_ms: float) -> None:
        """Records a single prediction event."""
        self.total_scored += 1
        if risk_level == "HIGH":
            self.fraud_blocked += 1
        elif risk_level == "MEDIUM":
            self.manual_reviews += 1
        else:
            self.approved += 1

        self.latencies.append(latency_ms)
        if len(self.latencies) > self.max_history:
            self.latencies.pop(0)

    def summary(self) -> dict:
        """Returns consolidated session analytics."""
        avg_lat = round(float(np.mean(self.latencies)), 2) if self.latencies else 0.0
        p95_lat = round(float(np.percentile(self.latencies, 95)), 2) if self.latencies else 0.0

        total = max(1, self.total_scored)
        return {
            "totalTransactionsScored": self.total_scored,
            "fraudBlocked": self.fraud_blocked,
            "fraudBlockedRate": round((self.fraud_blocked / total) * 100, 2),
            "manualReviewsTriggered": self.manual_reviews,
            "manualReviewRate": round((self.manual_reviews / total) * 100, 2),
            "approvedTransactions": self.approved,
            "approvalRate": round((self.approved / total) * 100, 2),
            "latencyStats": {
                "averageMs": avg_lat,
                "p95Ms": p95_lat,
                "sampleCount": len(self.latencies),
            },
        }


@router.get("/analytics/stats", summary="Get Live Session Scoring Metrics")
async def get_analytics_stats(request: Request):
    """Returns rolling counters of processed transactions, fraud rate, and latency percentiles."""
    stats: SessionStatsTracker = getattr(request.app.state, "stats", None)
    if stats is None:
        return {"message": "Session stats tracker not initialized."}
    return stats.summary()


@router.get("/analytics/history", summary="Query Persistent Audit Trail")
async def get_audit_history(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    riskLevel: Optional[str] = Query(default=None, description="Filter by risk tier: LOW, MEDIUM, or HIGH"),
    db: Session = Depends(get_db),
):
    """Returns paginated historical transactions saved in the compliance audit database."""
    query = db.query(TransactionAuditRecord)
    if riskLevel:
        query = query.filter(TransactionAuditRecord.risk_level == riskLevel.upper())

    total = query.count()
    records = query.order_by(TransactionAuditRecord.evaluated_at.desc()).offset(offset).limit(limit).all()

    return {
        "totalRecords": total,
        "limit": limit,
        "offset": offset,
        "records": [r.to_dict() for r in records],
    }


@router.get("/analytics/supabase-history", summary="Query Cloud Audit Trail from Supabase")
async def get_supabase_audit_history(limit: int = Query(default=25, ge=1, le=100)):
    """Fetches real-time transaction audit records stored in Supabase Postgres."""
    from src.db.database import fetch_supabase_audit_records
    records = fetch_supabase_audit_records(limit=limit)
    return {
        "source": "supabase_postgres",
        "count": len(records),
        "records": records,
    }


@router.post("/analytics/drift-check", summary="Evaluate Data Drift (PSI)")
async def check_data_drift(
    payload: BatchTransactionRequest,
    request: Request,
):
    """Calculates Population Stability Index (PSI) on a batch of incoming transactions."""
    drift_detector = getattr(request.app.state, "drift_detector", None)
    if drift_detector is None:
        return {
            "driftStatus": "UNINITIALIZED",
            "message": "Drift detector baseline not initialized in application state.",
        }

    raw_dicts = [tx.to_feature_dict() for tx in payload.transactions]
    drift_report = drift_detector.evaluate_batch_drift(raw_dicts)
    return drift_report
