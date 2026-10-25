# Changelog

All notable changes to the **Credit Card Fraud Detection App** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Change Categories Reference

- **`Added`**: New features, endpoints, or documentation introduced.
- **`Changed`**: Changes in existing functionality or architectural adjustments.
- **`Fixed`**: Bug fixes, schema corrections, or performance patches.
- **`Removed`**: Features or deprecated endpoints removed from the codebase.
- **`Security`**: Vulnerability patches, secrets handling, or authentication updates.

---

## [Unreleased]

### Fixed (Dev Workflow & Next.js App Router)
- Added missing root `npm run dev` script using `concurrently` to spin up both FastAPI backend (:8000) and Next.js frontend (:3000) simultaneously with unified color-coded logging.
- Created `frontend/src/app/layout.tsx` and `frontend/src/app/page.tsx` resolving Next.js 15 App Router directory requirement (`Couldn't find any 'pages' or 'app' directory`).
- Created `frontend/next.config.mjs` configuring `outputFileTracingRoot` to resolve monorepo multi-lockfile workspace inference warnings.
- Added `frontend/Dockerfile` production multi-stage build container and updated `docker-compose.yml`.
- Added comprehensive step-by-step production deployment documentation covering Vercel, Render/Railway, and Docker Compose.

### Added (Enterprise Security & Biometrics)
- Implemented Enterprise Authentication gateway in `frontend/src/index.html` with Sign In and Create Account modes.
- Added `frontend/src/js/auth.js` providing WebAuthn / FIDO2 Passkey biometric authentication (Windows Hello, Touch ID, Face ID).
- Added interactive Biometric Sensor modal with animated circular fingerprint scanner and sweeping laser HUD.
- Added password strength meter, remember-workstation persistent session management, and clearance role tier assignments.
- Added header Analyst Clearance Profile widget (`Smit Kulkarni`, `Level 3 · Senior Risk Investigator`, `🛡️ Biometric Active`, Lock/Sign-out action).

### Removed & Cleaned
- Completely removed demo terminology, demo placeholders (`tx_demo_01`), and demo CSV naming from frontend and backend presets.
- Upgraded transaction IDs to enterprise formatting (`TX-892104`, `TX-492105`, `TX-792106`, `TX-90218412`).
- Replaced demo preset labels with operational profiles (**Standard Retail**, **Velocity Spike**, **Compromised Vector**).

### Added
- Root-level orchestration `package.json` providing coordinated scripts (`npm run backend:dev`, `npm run frontend:dev`, `npm run backend:test`).
- Docker Compose dual-service configuration for frontend (port 3000) and backend (port 8000).
- Independent `.env` and `.env.example` configurations for `frontend/` and `backend/`.

### Changed
- **Decoupled Architecture Refactoring (ADR-005):**
  - Completely separated repository into standalone `frontend/` and `backend/` subfolders.
  - Moved all frontend assets, styles, Sentinel Triage Studio, Next.js page components, Supabase helpers, and TypeScript config into `frontend/`.
  - Moved all ML pipelines, models, SQLite databases, FastAPI server endpoints, and pytest suites into `backend/`.
  - Separated `package.json` files and runtime dependencies between tiers.
  - Updated API routing so frontend purely consumes backend through REST API calls at `http://127.0.0.1:8000/api/v1`.
  - Updated GitHub Actions CI workflow to run independent test jobs for backend (Python 3.10/3.11 pytest) and frontend (TypeScript check).
  - Updated master `README.md` with complete installation, startup, and dual-run instructions.

### Added (Supabase Cloud PostgreSQL Integration)
- Created `public.fraud_audit_records` table in Supabase project `eufrawprayanwthhuvaj` with indexes and Row-Level Security (RLS).
- Created `public.analyst_profiles` table for clearance role and biometric passkey enrollment tracking.
- Created `frontend/src/js/supabaseClient.js` delivering direct PostgREST synchronization and live audit trail fetching.
- Added asynchronous non-blocking worker thread in `backend/src/db/database.py` (`sync_record_to_supabase_async`) keeping scoring latency under 15ms.
- Added `GET /api/v1/analytics/supabase-history` endpoint in `backend/src/api/routes/analytics.py`.
- Updated `frontend/src/page.tsx` Next.js Server Component to query live fraud records and analyst clearance profiles directly from Supabase.
- Passed Supabase security audit via `get_advisors` with 0 security lints or RLS policy vulnerabilities.

### Planned for v0.6.0
- [ ] Streaming real-time Kafka transaction consumer.
- [ ] A/B model multi-version shadow evaluation.

---


## [0.5.0] - 2026-10-25

### Added
- **Phase 4: Production Hardening, Monitoring & Deployment:**
  - Implemented [`src/db/models.py`](./src/db/models.py) with `TransactionAuditRecord` SQLAlchemy schema for persistent compliance logging.
  - Implemented [`src/db/database.py`](./src/db/database.py) managing database engine, transactional sessions, and `init_db()` table auto-creation.
  - Implemented [`src/ml/drift_detector.py`](./src/ml/drift_detector.py) computing Population Stability Index (PSI) with thresholds for `STABLE`, `MODERATE_DRIFT`, and `CRITICAL_DRIFT`.
  - Added `/api/v1/analytics/history` endpoint with limit/offset pagination and risk tier filtering.
  - Added `/api/v1/analytics/drift-check` endpoint for batch distribution shift detection.
  - Wired real-time and batch scoring in [`src/api/routes/predict.py`](./src/api/routes/predict.py) to automatically save audit logs into SQLite.
  - Authored production multi-stage [`Dockerfile`](./Dockerfile) using unprivileged `appuser` and container healthchecks.
  - Authored [`docker-compose.yml`](./docker-compose.yml) orchestrating persistent container storage.
  - Authored [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) running automated training smoke tests and pytest across Python 3.10 and 3.11.
  - Implemented [`tests/test_audit_and_drift.py`](./tests/test_audit_and_drift.py) adding 7 automated tests.

### Changed
- Total automated test suite expanded to 28 passing tests with 100% pass rate.
- Promoted Phase 4 status to **Completed** across all context files.
- Master Phase Implementation roadmap 100% completed.

## [0.4.0] - 2026-10-25

### Added
- **Phase 3: Interactive Analyst Dashboard & XAI Visualization:**
  - Implemented [`index.html`](./src/ui/index.html) providing an end-to-end FinTech triage workstation with live KPI ribbon, dual view modes, preset scenario injectors, and an interactive audit trail.
  - Implemented [`css/styles.css`](./src/ui/css/styles.css) with a bespoke dark-mode design system, glassmorphism, responsive CSS grid, and high-contrast financial risk color tokens (`#10b981`, `#f59e0b`, `#ef4444`).
  - Implemented [`js/presets.js`](./src/ui/js/presets.js) containing curated test fixtures (Normal Retail, Suspicious Velocity, Confirmed Fraud) and random transaction generator.
  - Implemented [`js/chart.js`](./src/ui/js/chart.js) featuring an animated SVG circular risk gauge and directional Tree SHAP waterfall feature breakdown.
  - Implemented [`js/app.js`](./src/ui/js/app.js) with live REST client integration, dynamic $V_1 - V_{28}$ accordion, and drag-and-drop batch CSV processor with sample template generator.
  - Mounted the dashboard at `/dashboard` within FastAPI in [`main.py`](./src/api/main.py).
  - Added dashboard mount integration test in [`tests/test_api.py`](./tests/test_api.py) bringing total test suite to 21 passing tests.

### Changed
- Promoted Phase 3 status to **Completed** in `phases.md` and `memory.md`.
- FastAPI root descriptor at `GET /` updated to link to `/dashboard`.

## [0.3.0] - 2026-10-25

### Added
- **Phase 2: High-Performance FastAPI Serving Engine:**
  - Implemented [`main.py`](./src/api/main.py) with application factory, asynchronous lifespan model loading, CORS middleware, and standardized JSON exception envelopes.
  - Implemented [`config.py`](./src/api/config.py) using Pydantic Settings with `.env` reading, threshold constants, and artifact paths.
  - Implemented [`schemas/transaction.py`](./src/api/schemas/transaction.py) with Pydantic v2 schemas (`TransactionInput`, `PredictionResponse`, `BatchTransactionRequest`, `BatchPredictionResponse`, `PresetScenario`).
  - Implemented [`routes/health.py`](./src/api/routes/health.py) with `/api/v1/health` and `/api/v1/model/metadata` diagnostic routes.
  - Implemented [`routes/predict.py`](./src/api/routes/predict.py) delivering `/api/v1/predict` (single scoring + Tree SHAP factors), `/api/v1/predict/batch` (parallel vectorized batch scoring), and `/api/v1/predict/presets` (Normal, Suspicious, Fraud demo presets).
  - Implemented [`routes/analytics.py`](./src/api/routes/analytics.py) with `/api/v1/analytics/stats` tracking rolling session throughput, approval/review rates, and latency percentiles.
  - Implemented [`tests/test_api.py`](./tests/test_api.py) with 9 integration tests covering all endpoints, presets, and validation edge cases.

### Changed
- Promoted Phase 2 status to **Completed** in `phases.md` and `memory.md`.
- Active API endpoint suite increased to 7 fully operational endpoints.
- Total automated test coverage reached 20 tests with 100% pass rate in pytest.

---

## [0.2.0] - 2026-10-25

### Added
- **Phase 1: Machine Learning & Modeling Core:**
  - Implemented [`data_loader.py`](./src/ml/data_loader.py) with schema validation and synthetic generation fallback.
  - Implemented [`preprocessor.py`](./src/ml/preprocessor.py) with `RobustScaler` for Amount, Time normalization, and 30-feature vector transformation.
  - Implemented [`evaluate.py`](./src/ml/evaluate.py) computing PR-AUC, ROC-AUC, confusion matrices, and financial cost-weighted penalty metrics.
  - Implemented [`explainer.py`](./src/ml/explainer.py) providing exact Tree SHAP feature attributions and risk directionality.
  - Implemented [`predictor.py`](./src/ml/predictor.py) offering single-record and vectorized batch inference with latency profiling.
  - Implemented [`train.py`](./src/ml/train.py) orchestrating Stratified 5-Fold cross-validation, `scale_pos_weight` imbalance handling, and model export.
  - Implemented [`test_ml.py`](./tests/test_ml.py) with 11 automated unit and integration tests (100% pass rate).
  - Serialized baseline production model artifacts: `models/preprocessor.joblib`, `models/fraud_detector_xgb.joblib`, and `models/model_metrics.json`.
  - Added project dependency specification in `requirements.txt`, `.gitignore`, and `.env.example`.

### Changed
- Promoted Phase 1 status to **Completed** in `phases.md` and `memory.md`.
- Baseline model cross-validation PR-AUC achieved: `0.9803 (+/- 0.0245)`.

## [0.1.0] - 2026-10-25

### Added
- **Persistent AI Governance Architecture:**
  - Created [`decisions.md`](./decisions.md) establishing initial Architecture Decision Records:
    - `ADR-001`: Imbalanced Classification Algorithm Selection (XGBoost / LightGBM, PR-AUC).
    - `ADR-002`: Dual-Layer Architecture (FastAPI backend + Modern UI dashboard).
    - `ADR-003`: Model Explainability via SHAP Integration.
    - `ADR-004`: Persistent 4-file AI Context Framework.
  - Created [`rules.md`](./rules.md) defining strict development constraints:
    - Non-destructive continuity rule (never break existing functionality).
    - PEP 8 and Pydantic v2 coding standards.
    - Standardized project directory layout (`src/ml`, `src/api`, `src/ui`, `tests`, `models`).
    - Naming conventions across Python, API endpoints, JSON keys, and UI components.
    - UI/UX consistency guidelines with financial risk color palette (Emerald, Amber, Crimson).
    - Git Conventional Commit rules.
    - Security and environment variable rules (zero secrets in git, PII masking, input bounds).
  - Created [`memory.md`](./memory.md) capturing project context:
    - High-level overview and domain problem statement.
    - Target technology stack (FastAPI, XGBoost, SHAP, Modern Vanilla CSS).
    - Completed and pending feature checklists across development phases.
    - REST API contracts for single and batch fraud scoring with sample JSON payloads.
    - Database schema design (Transactions, Predictions, Model Registry).
    - Core business logic: decision thresholds (0.25 / 0.65) and cost matrix trade-offs.
    - Known technical constraints and 4-phase project roadmap.
  - Created [`phases.md`](./phases.md) defining the comprehensive 4-phase implementation plan, task checklists, and acceptance criteria.
  - Created [`changelog.md`](./changelog.md) conforming to Keep-a-Changelog specification.

### Changed
- Baseline repository structure organized for Artificial Intelligence & Data Science (AIDS) fraud detection application.

### Fixed
- Initial repository setup and baseline documentation alignment.

### Removed
- None (initial release).

---

## Maintenance Guidelines for AI Agents

Whenever you introduce changes to this codebase:
1. Append all newly created features under the `[Unreleased]` section.
2. Group items under the appropriate subheadings: `### Added`, `### Changed`, `### Fixed`, `### Removed`, or `### Security`.
3. When releasing a formal version, promote `[Unreleased]` into a versioned header (e.g., `## [0.2.0] - YYYY-MM-DD`).
4. Cross-reference related issue keys or ADR numbers where applicable.
