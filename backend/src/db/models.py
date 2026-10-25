"""SQLAlchemy models for persisting transaction evaluations and audit trails."""

from datetime import datetime, timezone
import json
from typing import Any, Dict
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""
    pass


class TransactionAuditRecord(Base):
    """Stores every evaluated transaction for compliance and forensic auditing."""

    __tablename__ = "transaction_audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    time_delta: Mapped[float] = mapped_column(Float, default=0.0)
    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    is_fraud: Mapped[bool] = mapped_column(Boolean, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    top_factors_json: Mapped[str] = mapped_column(Text, default="[]")
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the audit record to a dictionary."""
        try:
            factors = json.loads(self.top_factors_json)
        except Exception:
            factors = []

        return {
            "id": self.id,
            "transactionId": self.transaction_id,
            "amount": self.amount,
            "time": self.time_delta,
            "fraudProbability": self.fraud_probability,
            "isFraud": self.is_fraud,
            "riskLevel": self.risk_level,
            "decision": self.decision,
            "latencyMs": self.latency_ms,
            "topFactors": factors,
            "evaluatedAt": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }
