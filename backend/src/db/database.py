"""Database connection and session lifecycle management."""

from pathlib import Path
from typing import Generator, Optional
import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.config import get_settings
from src.db.models import Base, TransactionAuditRecord

logger = logging.getLogger(__name__)

_engine = None
_SessionFactory = None


def get_engine():
    """Returns singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        # Default to SQLite in data directory
        db_url = getattr(settings, "DATABASE_URL", "sqlite:///./data/fraud_audit.db")

        # Ensure directory exists if SQLite
        if db_url.startswith("sqlite:///"):
            raw_path = db_url.replace("sqlite:///", "")
            Path(raw_path).parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        _engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
        logger.info("Initialized database engine with URL: %s", db_url)
    return _engine


def get_session_factory():
    """Returns singleton sessionmaker."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionFactory


def init_db() -> None:
    """Creates database schema tables if they do not exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def save_audit_record(
    transaction_id: str,
    amount: float,
    time_delta: float,
    fraud_probability: float,
    is_fraud: bool,
    risk_level: str,
    decision: str,
    latency_ms: float,
    top_factors: Optional[list] = None,
    session: Optional[Session] = None,
) -> TransactionAuditRecord:
    """Helper saving a transaction audit record synchronously."""
    should_close = False
    if session is None:
        factory = get_session_factory()
        session = factory()
        should_close = True

    try:
        record = TransactionAuditRecord(
            transaction_id=transaction_id,
            amount=amount,
            time_delta=time_delta,
            fraud_probability=fraud_probability,
            is_fraud=is_fraud,
            risk_level=risk_level,
            decision=decision,
            latency_ms=latency_ms,
            top_factors_json=json.dumps(top_factors or []),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    except Exception as exc:
        session.rollback()
        logger.error("Failed to commit audit record for %s: %s", transaction_id, exc)
        raise
    finally:
        if should_close:
            session.close()
