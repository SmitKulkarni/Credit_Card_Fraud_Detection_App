"""Application settings and configuration management via Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Credit Card Fraud Detection API"
    APP_VERSION: str = "0.2.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # CORS Whitelist
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*",
    ]

    # Model Artifact Locations
    MODEL_DIR: str = "models"
    MODEL_FILENAME: str = "fraud_detector_xgb.joblib"
    PREPROCESSOR_FILENAME: str = "preprocessor.joblib"
    METRICS_FILENAME: str = "model_metrics.json"

    # Decision Threshold Policies
    FRAUD_PROBABILITY_THRESHOLD: float = 0.35
    REVIEW_PROBABILITY_THRESHOLD: float = 0.20

    @property
    def model_path(self) -> Path:
        """Returns resolved Path to the trained model artifact."""
        return Path(self.MODEL_DIR) / self.MODEL_FILENAME

    @property
    def preprocessor_path(self) -> Path:
        """Returns resolved Path to the fitted preprocessor artifact."""
        return Path(self.MODEL_DIR) / self.PREPROCESSOR_FILENAME

    @property
    def metrics_path(self) -> Path:
        """Returns resolved Path to the evaluation metrics JSON."""
        return Path(self.MODEL_DIR) / self.METRICS_FILENAME


@lru_cache()
def get_settings() -> Settings:
    """Returns cached singleton application settings instance."""
    return Settings()
