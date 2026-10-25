# Architecture & Product Decisions (ADR Log)

This document tracks all critical technical, architectural, and product decisions for the **Credit Card Fraud Detection App**. Every significant change to system architecture, model lifecycle, or technology choices must be logged here.

---

## Decision Log Summary

| ADR ID | Date | Decision Title | Status | Category |
| :--- | :--- | :--- | :--- | :--- |
| [ADR-001](#adr-001-imbalanced-classification-algorithm-selection) | 2026-10-25 | Imbalanced Classification Algorithm Selection | Accepted | Machine Learning |
| [ADR-002](#adr-002-dual-layer-application-architecture-fastapi--modern-ui) | 2026-10-25 | Dual-Layer Architecture: FastAPI & Modern UI | Accepted | Architecture |
| [ADR-003](#adr-003-model-explainability-via-shap-integration) | 2026-10-25 | Model Explainability via SHAP Integration | Accepted | UX / Compliance |
| [ADR-004](#adr-004-persistent-ai-context-system-adoption) | 2026-10-25 | Adoption of 4-File Persistent AI Context Framework | Accepted | Governance |
| [ADR-005](#adr-005-decoupled-frontend-and-backend-subfolder-architecture) | 2026-10-25 | Decoupled Frontend and Backend Subfolder Architecture | Accepted | Architecture |

---

## Template for New Decisions

When logging a new decision, duplicate the following section block:

```markdown
### ADR-XXX: [Descriptive Title]

- **Date:** YYYY-MM-DD
- **Status:** [Proposed | Accepted | Superseded | Deprecated]
- **Deciders:** [Name / Team]

#### Context / Problem
[Describe the context, constraints, and specific problem triggering this decision]

#### Decision Taken
[Explicit statement of the chosen path or architecture]

#### Reasoning
[Why this approach was selected over others, backed by benchmarks, trade-offs, or constraints]

#### Alternatives Considered
- **Alternative 1:** [Why it was rejected]
- **Alternative 2:** [Why it was rejected]

#### Impact on Project
- **Positive:** [Benefits and advantages]
- **Negative / Risks:** [Trade-offs, performance cost, complexity added]
- **Mitigation:** [How negative consequences are mitigated]
```

---

## Recorded Decisions

### ADR-001: Imbalanced Classification Algorithm Selection

- **Date:** 2026-10-25
- **Status:** Accepted
- **Deciders:** AI Engineering Team

#### Context / Problem
Credit card fraud detection datasets (e.g., European cardholder benchmark) are notoriously imbalanced, typically featuring fraud rates below 0.2% (approx. 492 frauds out of 284,807 transactions). Standard classification metrics (like raw accuracy) yield misleading 99.8% scores while missing nearly all actual fraudulent cases. We need an algorithm and validation methodology robust against severe skew.

#### Decision Taken
Adopt **XGBoost (Extreme Gradient Boosting)** as the primary production classifier, with **LightGBM** and **Random Forest** as baseline benchmarks. Optimize models using **PR-AUC (Precision-Recall Area Under Curve)** and **F1-Score / Recall at controlled false positive rate**, rather than ROC-AUC or Accuracy. Combine with algorithmic cost-sensitive weighting (`scale_pos_weight`) and optional SMOTE / Random Under-Sampling during cross-validation only.

#### Reasoning
1. Gradient boosted decision trees excel on tabular data with non-linear feature interactions.
2. `scale_pos_weight` directly handles extreme imbalance without synthetic artifact distortion from oversampling.
3. Fast inference latency (< 5ms per transaction) suitable for real-time risk scoring.

#### Alternatives Considered
- **Standard Logistic Regression:** Fast and interpretable, but fails to capture complex non-linear combinations of PCA features ($V_1$ through $V_{28}$).
- **Deep Neural Networks (MLP / Autoencoders):** Autoencoders are effective for anomaly detection, but require more compute, have higher inference latency, and offer less direct interpretability for financial compliance.
- **Isolation Forests:** Good unsupervised fallback, but underperforms supervised boosted trees when historical labeled data exists.

#### Impact on Project
- **Positive:** High detection recall for fraud, low latency, robust tabular performance.
- **Negative / Risks:** Requires careful hyperparameter tuning and threshold calibration to avoid high false-positive rates that annoy cardholders.
- **Mitigation:** Implement probability threshold calibration (`predict_proba` with configurable cutoff threshold, default ~0.3-0.4 instead of 0.5).

---

### ADR-002: Dual-Layer Application Architecture (FastAPI + Modern UI)

- **Date:** 2026-10-25
- **Status:** Accepted
- **Deciders:** Full-Stack & ML Engineering

#### Context / Problem
The fraud detection system requires two core capabilities:
1. Low-latency, schema-validated prediction APIs for both single transaction scoring and batch processing.
2. An intuitive, real-time interactive analytical dashboard for fraud analysts and investigators to inspect suspicious transactions.

#### Decision Taken
Decouple the solution into:
- **Backend / Inference Engine:** Python **FastAPI** with Pydantic v2 schemas and Joblib/ONNX model serialization.
- **Frontend / Analyst Dashboard:** Modern lightweight client dashboard with responsive UI, real-time risk gauge, transaction history table, and explainability breakdown.

#### Reasoning
- FastAPI provides automatic OpenAPI documentation, asynchronous endpoint handling, strict type enforcement via Pydantic, and high throughput.
- Decoupling allows the ML inference API to be scaled independently or consumed by external banking microservices.

#### Alternatives Considered
- **Monolithic Streamlit-only App:** Rapid to prototype, but poor for microservice integration, difficult to customize aesthetics, and limited multi-user session performance.
- **Flask Monolith:** Less modern asynchronous support, requires manual swagger generation, slower serialization than Pydantic v2.

#### Impact on Project
- **Positive:** Production-ready API architecture, clean separation of concerns, testable endpoints.
- **Negative / Risks:** Requires managing API communication, CORS, and deployment for client and server.
- **Mitigation:** Provide centralized environment configuration and a unified start script for local development.

---

### ADR-003: Model Explainability via SHAP Integration

- **Date:** 2026-10-25
- **Status:** Accepted
- **Deciders:** Product & Governance

#### Context / Problem
Financial regulations (e.g., Fair Credit Reporting Act, GDPR Article 22) require automated decisions affecting financial transactions to be auditable and explainable. A raw "0.89 fraud score" is insufficient for an investigator evaluating whether to freeze an account.

#### Decision Taken
Integrate **SHAP (SHapley Additive exPlanations)** using `TreeExplainer` for XGBoost to provide per-transaction feature contributions (waterfall / force contribution) in both the API response and dashboard view.

#### Reasoning
- `TreeExplainer` computes exact Shapley values in polynomial time for tree ensembles.
- Returns explicit positive and negative contributions for top predictive features ($V_i$, transaction amount, time deltas).

#### Alternatives Considered
- **LIME:** Perturbation-based, slower for real-time single instances, and produces sampling variance.
- **Global Feature Importance only:** Fails to explain individual transaction anomalies.

#### Impact on Project
- **Positive:** Regulatory compliance, investigator trust, actionable transaction diagnostics.
- **Negative / Risks:** SHAP computations add 10-30ms to single-inference requests.
- **Mitigation:** Enable SHAP explanation optionally via query parameter (`include_explanation=true`) so high-throughput batch scoring remains unaffected.

---

### ADR-004: Persistent AI Context System Adoption

- **Date:** 2026-10-25
- **Status:** Accepted
- **Deciders:** Core Team

#### Context / Problem
As AI coding assistants work on this repository across multiple sessions, knowledge can be lost, leading to inconsistent styling, broken features, and architectural drift.

#### Decision Taken
Adopt a standard 4-file persistent context framework at the repository root:
1. `decisions.md`: Architecture and product decision records.
2. `rules.md`: Unbreakable coding, folder structure, UI, and git conventions.
3. `memory.md`: Long-term project state, schema, roadmap, and pending tasks.
4. `changelog.md`: Chronological changelog following Keep-a-Changelog conventions.

#### Reasoning
Ensures all AI assistants and human developers operate with unified memory, clear boundaries, and full contextual awareness.

#### Alternatives Considered
- **Ad-hoc commit messages & scattered notes:** Leads to forgotten decisions and inconsistent patterns.

#### Impact on Project
- **Positive:** Zero context loss across AI sessions; predictable code quality.
- **Negative / Risks:** Requires discipline to update files when making major changes.
- **Mitigation:** Codified in `rules.md` as mandatory agent behavior.

---

### ADR-005: Decoupled Frontend and Backend Subfolder Architecture

- **Date:** 2026-10-25
- **Status:** Accepted
- **Deciders:** Full-Stack Architecture Team

#### Context / Problem
Previously, frontend static assets and backend Python logic resided within a single unified tree (`src/ui`, `src/api`, `src/ml`, `src/db`). As the application grew to incorporate Supabase SSR, Next.js components, and complex frontend build pipelines, coupling Python ML dependencies with Node.js dependencies caused tooling friction, deployment ambiguity, and cluttered root configurations.

#### Decision Taken
Refactor the repository into two strictly isolated subdirectories:
- `frontend/`: Standalone Next.js & Sentinel Triage Studio UI with its own `package.json`, TypeScript configuration, Supabase client helpers, and dedicated `.env`.
- `backend/`: Standalone FastAPI microservice containing ML models, SQLite audit trail, pytest test suite, `requirements.txt`, Dockerfile, and dedicated `.env`.
- Root level contains only orchestration (`package.json`, `docker-compose.yml`, CI workflows) and governance documentation.
- The frontend interacts with the backend strictly via HTTP REST API (`/api/v1/predict`, `/api/v1/health`, etc.) with CORS enabled.

#### Reasoning
- Separation of concerns: Python/ML stack runs independently from Node/TypeScript stack.
- Independent CI/CD: Backend unit tests and frontend type checks can run in parallel.
- Cloud deployment flexibility: Backend can be containerized to AWS/GCP/Render while frontend deploys seamlessly to Vercel/Cloudflare Pages.
- Environment isolation: Sensitive backend database credentials never risk exposure to frontend client bundles.

#### Alternatives Considered
- **Monolithic combined `src/`:** Simpler for tiny demos, but unwieldy for modern full-stack web applications with separate Node and Python runtimes.
- **Separate git repositories:** High overhead for a coordinated ML demo project; monorepo with distinct subfolders provides the optimal balance.

#### Impact on Project
- **Positive:** Clear boundaries, zero dependency collision, independent deployment and testing.
- **Negative / Risks:** Running locally requires launching two processes or using Docker Compose.
- **Mitigation:** Added root orchestration scripts (`npm run backend:dev`, `npm run frontend:dev`, `docker-compose up`) and full instructions in `README.md`.

