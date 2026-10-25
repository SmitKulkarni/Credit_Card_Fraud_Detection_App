"""FastAPI application entrypoint for the Credit Card Fraud Detection system.

Configures application lifespan, CORS middleware, global exception handlers,
and registers API routers under /api/v1.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.config import get_settings
from src.api.routes import (
    SessionStatsTracker,
    analytics_router,
    health_router,
    predict_router,
)
from src.ml.predictor import FraudPredictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("src.api.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup (model loading) and shutdown cleanup."""
    settings = get_settings()
    logger.info("Initializing %s v%s...", settings.APP_NAME, settings.APP_VERSION)

    # 1. Initialize in-memory session stats
    app.state.stats = SessionStatsTracker()

    # 2. Initialize persistent database schema
    try:
        from src.db.database import init_db
        init_db()
    except Exception as db_exc:
        logger.error("Failed to initialize database schema: %s", db_exc)

    # 3. Initialize drift detector with baseline transactions
    try:
        from src.ml.drift_detector import DriftDetector
        from src.ml.data_loader import generate_synthetic_transactions
        baseline_df = generate_synthetic_transactions(n_samples=2000, random_state=42)
        app.state.drift_detector = DriftDetector(baseline_df=baseline_df)
        logger.info("DriftDetector baseline initialized with %d reference records.", len(baseline_df))
    except Exception as drift_exc:
        logger.warning("Could not initialize DriftDetector baseline: %s", drift_exc)
        app.state.drift_detector = None

    # 4. Attempt loading production ML artifacts into application state
    try:
        app.state.predictor = FraudPredictor.load(
            model_path=settings.model_path,
            preprocessor_path=settings.preprocessor_path,
            fraud_threshold=settings.FRAUD_PROBABILITY_THRESHOLD,
            review_threshold=settings.REVIEW_PROBABILITY_THRESHOLD,
        )
        logger.info("Production FraudPredictor successfully loaded into app.state.")
    except Exception as exc:
        logger.error(
            "Could not load ML artifacts from %s: %s. Run python -m src.ml.train to generate them.",
            settings.MODEL_DIR,
            exc,
        )
        app.state.predictor = None

    yield

    logger.info("Shutting down %s...", settings.APP_NAME)


def create_application() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Real-time and batch credit card fraud detection engine powered by "
            "XGBoost, PR-AUC cost-weighted threshold calibration, and Tree SHAP explainability."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Validation Error Handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Transaction payload failed schema validation.",
                "details": exc.errors(),
            },
        )

    # Global Uncaught Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error processing request: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred.",
            },
        )

    # Root Info Endpoint
    @app.get("/", tags=["General"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "docsUrl": "/docs",
            "dashboardUrl": "/dashboard",
            "healthCheck": f"{settings.API_PREFIX}/health",
            "modelMetadata": f"{settings.API_PREFIX}/model/metadata",
        }

    # Register Route Controllers
    app.include_router(health_router, prefix=settings.API_PREFIX)
    app.include_router(predict_router, prefix=settings.API_PREFIX)
    app.include_router(analytics_router, prefix=settings.API_PREFIX)

    # Mount Interactive Analyst Dashboard (if available)
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    ui_candidate = repo_root / "frontend" / "src"
    if not ui_candidate.is_dir():
        ui_candidate = Path("../frontend/src")
    if not ui_candidate.is_dir():
        ui_candidate = Path("src/ui")
    if ui_candidate.is_dir():
        from starlette.staticfiles import StaticFiles
        app.mount("/dashboard", StaticFiles(directory=str(ui_candidate), html=True), name="dashboard")
        logger.info("Mounted Analyst Dashboard at /dashboard from %s", ui_candidate)

    return app


app = create_application()
