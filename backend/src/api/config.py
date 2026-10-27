"""Application settings and configuration management via Pydantic Settings."""

from functools import lru_cache
import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Credit Card Fraud Detection API"
    APP_VERSION: str = "0.5.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Safely parses comma-separated strings, JSON arrays, or lists from environment."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            # Split comma-separated values
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Model Artifact Locations
    MODEL_DIR: str = "models"
    MODEL_FILENAME: str = "fraud_detector_xgb.joblib"
    PREPROCESSOR_FILENAME: str = "preprocessor.joblib"
    METRICS_FILENAME: str = "model_metrics.json"

    # Decision Threshold Policies
    FRAUD_PROBABILITY_THRESHOLD: float = 0.35
    REVIEW_PROBABILITY_THRESHOLD: float = 0.20

    # Database
    DATABASE_URL: str = "sqlite:///./data/fraud_audit.db"

    # Supabase Cloud Integration
    SUPABASE_URL: str = "https://eufrawprayanwthhuvaj.supabase.co"
    SUPABASE_KEY: str = "sb_publishable_3YczReP6yNU8WPGQuS8V9A_CFJaeYA1"
    SUPABASE_SYNC_ENABLED: bool = True

    @property
    def model_path(self) -> Path:
        """Returns resolved Path to the trained model artifact."""
        candidate = Path(self.MODEL_DIR) / self.MODEL_FILENAME
        if candidate.is_file():
            return candidate
        # Try relative to backend package root
        backend_root = Path(__file__).resolve().parent.parent.parent
        pkg_candidate = backend_root / self.MODEL_DIR / self.MODEL_FILENAME
        if pkg_candidate.is_file():
            return pkg_candidate
        return candidate

    @property
    def preprocessor_path(self) -> Path:
        """Returns resolved Path to the fitted preprocessor artifact."""
        candidate = Path(self.MODEL_DIR) / self.PREPROCESSOR_FILENAME
        if candidate.is_file():
            return candidate
        backend_root = Path(__file__).resolve().parent.parent.parent
        pkg_candidate = backend_root / self.MODEL_DIR / self.PREPROCESSOR_FILENAME
        if pkg_candidate.is_file():
            return pkg_candidate
        return candidate

    @property
    def metrics_path(self) -> Path:
        """Returns resolved Path to the evaluation metrics JSON."""
        candidate = Path(self.MODEL_DIR) / self.METRICS_FILENAME
        if candidate.is_file():
            return candidate
        backend_root = Path(__file__).resolve().parent.parent.parent
        pkg_candidate = backend_root / self.MODEL_DIR / self.METRICS_FILENAME
        if pkg_candidate.is_file():
            return pkg_candidate
        return candidate


@lru_cache()
def get_settings() -> Settings:
    """Returns cached singleton application settings instance."""
    return Settings()
