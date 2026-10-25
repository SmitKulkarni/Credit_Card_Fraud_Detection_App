# AI & Project Operational Rules

This document establishes the mandatory rules, standards, and conventions for the **Credit Card Fraud Detection App**. 
**All AI coding assistants and developers MUST strictly comply with these rules.**

---

## 1. Prime Directive: Non-Destructive Continuity

> [!IMPORTANT]
> **NEVER break or regress existing functionality unless explicitly instructed by the user.**
> - Do not delete, rewrite, or alter working endpoints, modules, models, or UI views without direct instruction.
> - Always preserve existing comments, documentation, and interface contracts.
> - Before finishing any feature, verify that existing tests pass and dependencies remain intact.

---

## 2. Coding Standards

### 2.1 Python (Backend & ML)
- **Standard:** Strict compliance with **PEP 8**.
- **Type Annotations:** All functions, methods, and API models must use complete type hints (`typing` module or native Python 3.10+ types).
- **Docstrings:** Use Google-style or Sphinx-style docstrings for all classes and public functions:
  ```python
  def predict_transaction(transaction: TransactionSchema) -> PredictionResult:
      """Evaluates transaction risk using the primary fraud detection model.

      Args:
          transaction: Structured payload containing transaction features.

      Returns:
          PredictionResult containing fraud score, classification, and metadata.

      Raises:
          ModelNotLoadedError: If the inference model has not been initialized.
      """
  ```
- **Error Handling:** Avoid bare `except:`. Use specific exceptions and return standard HTTP status codes (`400` Bad Request, `404` Not Found, `422` Validation Error, `500` Internal Error).
- **Data Validation:** Use **Pydantic v2** models for all API request bodies, response payloads, and configuration settings.

### 2.2 Frontend (HTML / CSS / JavaScript)
- **Structure:** Clean, semantic HTML5 tags (`<main>`, `<header>`, `<section>`, `<article>`, `<nav>`).
- **Styling:** Vanilla CSS or scoped CSS variables. Maintain a unified color palette and design system.
- **JavaScript:** ES6+ standards, `async`/`await` for network calls, explicit error catches with user-friendly alerts.
- **No Inline Styles:** Use CSS classes defined in stylesheet files; avoid arbitrary `style="..."` attributes.

---

## 3. Folder Structure Rules

The project must strictly adhere to the following directory layout:

```text
Credit_Card_Fraud_Detection_App/
├── .env.example              # Template for environment variables (committed)
├── .gitignore                # Git ignore rules (secrets, venv, data, models)
├── README.md                 # Project overview and quickstart
├── decisions.md              # Architecture Decision Records (ADRs)
├── rules.md                  # Project rules for AI & engineers (this file)
├── memory.md                 # Long-term project memory and status
├── changelog.md              # Chronological change history
├── requirements.txt          # Python dependencies
│
├── data/                     # Data directory (GITIGNORED - no raw data in git)
│   ├── raw/                  # Original datasets (e.g. creditcard.csv)
│   └── processed/            # Engineered features & preprocessed splits
│
├── models/                   # Serialized ML artifacts (.joblib, .onnx, .json)
│   └── .gitkeep
│
├── src/                      # Source code
│   ├── ml/                   # Machine learning core
│   │   ├── __init__.py
│   │   ├── data_loader.py    # Ingestion & cleaning
│   │   ├── preprocessor.py   # Feature scaling & transformations
│   │   ├── train.py          # Model training & cross-validation
│   │   ├── evaluate.py       # PR-AUC, ROC-AUC, Confusion Matrix
│   │   ├── explainer.py      # SHAP / Interpretability logic
│   │   └── predictor.py      # Inference wrapper
│   │
│   ├── api/                  # FastAPI Application
│   │   ├── __init__.py
│   │   ├── main.py           # Application entrypoint & middleware
│   │   ├── config.py         # App settings & environment loaders
│   │   ├── schemas/          # Pydantic models (requests, responses)
│   │   │   ├── __init__.py
│   │   │   └── transaction.py
│   │   └── routes/           # API route controllers
│   │       ├── __init__.py
│   │       ├── health.py     # System liveness & readiness
│   │       ├── predict.py    # Single & batch prediction
│   │       └── analytics.py  # Model stats & audit logs
│   │
│   └── ui/                   # Frontend analyst interface
│       ├── index.html        # Main dashboard view
│       ├── css/
│       │   └── styles.css    # Core design system & theme
│       └── js/
│           └── app.js        # UI logic & API client
│
└── tests/                    # Automated test suites
    ├── conftest.py           # Pytest fixtures & mock models
    ├── test_api.py           # Endpoint integration tests
    ├── test_ml.py            # Feature transformation & inference tests
    └── test_schemas.py       # Pydantic validation tests
```

---

## 4. Naming Conventions

| Entity | Convention | Example |
| :--- | :--- | :--- |
| **Python Files / Modules** | `snake_case.py` | `feature_pipeline.py`, `data_loader.py` |
| **Python Classes** | `PascalCase` | `FraudClassifier`, `TransactionPayload` |
| **Python Functions / Methods** | `snake_case()` | `compute_shap_values()`, `predict_proba()` |
| **Python Constants** | `UPPER_SNAKE_CASE` | `DEFAULT_FRAUD_THRESHOLD`, `MAX_BATCH_SIZE` |
| **API Endpoints (URLs)** | `kebab-case`, plural nouns | `/api/v1/fraud-predictions`, `/api/v1/model-metrics` |
| **JSON Payload Keys** | `camelCase` or `snake_case` (consistent) | `transactionAmount`, `riskScore` (camelCase for JSON) |
| **Frontend Files** | `kebab-case.extension` | `fraud-card.css`, `transaction-modal.js` |
| **CSS Classes** | `kebab-case` (BEM encouraged) | `risk-badge`, `risk-badge--high`, `card__header` |
| **Git Branches** | `type/short-description` | `feat/fastapi-inference`, `fix/shap-memory-leak` |

---

## 5. UI/UX Consistency Rules

1. **Financial Risk Color Palette:**
   - **Low Risk (Normal):** Emerald / Green (`#10b981` / `rgba(16, 185, 129, 0.15)`)
   - **Medium Risk (Suspicious):** Amber / Orange (`#f59e0b` / `rgba(245, 158, 11, 0.15)`)
   - **High Risk (Fraud Alert):** Crimson / Rose (`#ef4444` / `rgba(239, 68, 68, 0.15)`)
   - **Accent / Primary Brand:** Slate / Indigo (`#6366f1` / `#4f46e5`)
   - **Background Dark Mode:** Deep Charcoal / Navy (`#0f172a`, `#1e293b`)
2. **Visual Hierarchy:**
   - Always display the **Risk Score (0.00% to 100.00%)** prominently with an accompanying status badge (`Legitimate`, `Review`, `Fraud Blocked`).
   - Latency indicators (`Response: 14ms`) must be clearly visible for live inference validation.
3. **Typography:**
   - Modern clean sans-serif (e.g., `Inter`, `system-ui`, or `Roboto`).
   - Monospace font (`JetBrains Mono`, `Fira Code`) for transaction IDs, raw feature values, and timestamps.
4. **Accessibility & Clarity:**
   - High contrast ratios (WCAG AA compliant).
   - Form inputs for features $V_1 - V_{28}$ must include pre-fillable demo presets (e.g., "Load Normal Sample", "Load Fraud Sample") so users don't have to manually type 28 floats.

---

## 6. Git Commit Rules

Follow the **Conventional Commits** specification:

```text
<type>(<scope>): <short imperative description>

[optional longer body]

[optional issue reference]
```

### Allowed Types:
- `feat`: A new feature (e.g., `feat(api): add batch prediction endpoint`).
- `fix`: A bug fix (e.g., `fix(ml): prevent division by zero in amount scaler`).
- `docs`: Documentation updates (e.g., `docs: update memory.md with latest metrics`).
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `perf`: Code change that improves performance.
- `test`: Adding or correcting tests.
- `chore`: Build process, package updates, gitignore changes.

**Commit Message Rules:**
- Write in imperative present tense ("add feature", NOT "added feature").
- Limit first line to 72 characters.
- Do not commit large datasets, model weights > 50MB, or temporary cache files (`__pycache__`, `.pytest_cache`).

---

## 7. Security & Environment Variable Rules

1. **Zero Secrets in Repository:**
   - Never commit API keys, database credentials, passwords, or cloud credentials.
   - All sensitive configs must reside in `.env` (which MUST be listed in `.gitignore`).
   - Maintain an up-to-date `.env.example` displaying required variables with sanitized dummy values.
2. **PII (Personally Identifiable Information) Protection:**
   - Credit card numbers must never be accepted in plain text. Only anonymized tokens, masked numbers (`****-****-****-1234`), or PCA-transformed features ($V_1 - V_{28}$) are processed.
3. **Input Sanitization & Validation:**
   - All API endpoints must strictly validate numeric ranges using Pydantic fields (`ge`, `le`).
   - Maximum batch payload limits must be enforced (e.g., max 1,000 transactions per batch) to prevent memory denial-of-service.
4. **CORS Configuration:**
   - Do not use wildcard `allow_origins=["*"]` in production configurations; whitelist explicit frontend origins.

---

## 8. AI Assistant Workflow Requirements

When an AI assistant implements or updates any part of this repository:
1. **Consult Context:** Read `rules.md` and `memory.md` before initiating architecture changes.
2. **Keep Decisions Updated:** If introducing a new library or structural shift, record it in `decisions.md`.
3. **Maintain Memory:** Update `memory.md` with newly implemented features, endpoints, or schema adjustments.
4. **Log Changes:** Append a corresponding entry in `changelog.md`.
5. **Verify Code:** Ensure code is free of syntax errors, type mismatches, and broken imports before completing tasks.
