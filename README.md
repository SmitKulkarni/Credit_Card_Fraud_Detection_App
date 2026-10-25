# 🛡️ Sentinel Triage Studio - Credit Card Fraud Detection

> **Production-Grade FinTech Machine Learning Platform**  
> Decoupled architecture with independent FastAPI/XGBoost backend microservice and modern Next.js / Sentinel Triage Studio frontend client.

[![CI Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.14-blue)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143.0-teal)](#)
[![Next.js](https://img.shields.io/badge/Next.js-15.1.0-black)](#)
[![XGBoost](https://img.shields.io/badge/XGBoost-PR--AUC%200.9803-orange)](#)
[![Tests Passing](https://img.shields.io/badge/tests-28%2F28%20passing-success)](#)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📁 Project Architecture & Directory Layout

The project is cleanly decoupled into two autonomous, self-contained sub-environments: `frontend/` and `backend/`.

```text
Credit_Card_Fraud_Detection_App/
├── frontend/                     # Modern Frontend Client & UI Layer
│   ├── src/                      # Source code (Sentinel Studio, CSS, JS, TypeScript)
│   │   ├── css/                  # FinTech dark-mode design system & animations
│   │   ├── js/                   # Pure API client, chart renders, presets
│   │   ├── utils/supabase/       # Supabase SSR client, server & middleware helpers
│   │   ├── index.html            # Sentinel Triage Studio analyst workstation
│   │   └── page.tsx              # Next.js Server Component page
│   ├── public/                   # Public static assets & mirrors
│   ├── .env                      # Frontend environment variables (API URL, Supabase)
│   ├── .env.example              # Frontend environment template
│   ├── package.json              # Frontend npm dependencies & run scripts
│   └── tsconfig.json             # TypeScript configuration
│
├── backend/                      # Production FastAPI & XGBoost Inference Engine
│   ├── src/                      # Backend microservice source code
│   │   ├── api/                  # FastAPI routers, schemas, configs, lifespan
│   │   │   ├── routes/           # /health, /predict, /analytics endpoints
│   │   │   ├── schemas/          # Pydantic v2 validation contracts
│   │   │   ├── config.py         # Dynamic environment settings
│   │   │   └── main.py           # Application entrypoint & CORS middleware
│   │   ├── db/                   # SQLite audit trail & SQLAlchemy models
│   │   └── ml/                   # ML pipeline (XGBoost, Tree SHAP, PSI drift)
│   ├── data/                     # Raw datasets & persistent SQLite database
│   ├── models/                   # Serialized model (.joblib) & metrics metadata
│   ├── tests/                    # 28-test automated pytest verification suite
│   ├── .env                      # Backend environment variables (Ports, Thresholds)
│   ├── .env.example              # Backend environment template
│   ├── Dockerfile                # Production multi-stage backend container
│   ├── package.json              # Backend npm task runner scripts
│   └── requirements.txt          # Python runtime dependencies
│
├── .github/workflows/ci.yml      # CI pipeline testing backend & frontend
├── docker-compose.yml            # Multi-service composition (frontend + backend)
├── package.json                  # Root convenience orchestration scripts
├── README.md                     # Master project documentation
├── .gitignore                    # Version control exclusion rules
├── decisions.md                  # Persistent Architecture Decision Records (ADRs)
├── rules.md                      # AI coding & architectural rules
├── memory.md                     # Long-term persistent project memory
├── phases.md                     # Roadmap & phase tracking
└── changelog.md                  # Chronological change history
```

---

## ⚡ Quickstart Guide

You can run the frontend and backend independently or orchestrate them together.

### Option 1: Run Both Together (Recommended)

#### Using Docker Compose:
```bash
docker-compose up --build
```
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Embedded Analyst Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)

#### Using Root NPM Scripts (Concurrent / Single-Command):
From the project root:
```bash
# 1. Install all dependencies
npm run backend:install
npm run frontend:install

# 2. Run both frontend and backend concurrently in a single command
npm run dev

# Or run them independently from the root:
npm run dev:backend    # FastAPI server on http://127.0.0.1:8000
npm run dev:frontend   # Next.js app on http://localhost:3000
```

---

### Option 2: Running Backend Independently

#### 1. Navigate to Backend Directory
```bash
cd backend
```

#### 2. Install Backend Dependencies
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

#### 3. Configure Backend Environment
Copy the example environment file:
```bash
cp .env.example .env
```
Key configuration parameters in `backend/.env`:
- `PORT=8000`
- `DECISION_THRESHOLD_SUSPICIOUS=0.20`
- `DECISION_THRESHOLD_FRAUD=0.35`
- `DATABASE_URL=sqlite:///./data/fraud_audit.db`

#### 4. Model Training (Optional - Baseline Artifacts Pre-packaged)
```bash
# Via Python module:
python -m src.ml.train --synthetic-samples 25000 --n-estimators 150

# Or via npm script:
npm run train
```

#### 5. Start Backend Server
```bash
# Via uvicorn:
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload

# Or via npm script:
npm run dev
```

#### 6. Run Backend Tests
Execute the comprehensive 28-test verification suite:
```bash
python -m pytest tests/ -v
# Or:
npm test
```

Backend URLs:
- **API Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI JSON Spec**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

### Option 3: Running Frontend Independently

#### 1. Navigate to Frontend Directory
```bash
cd frontend
```

#### 2. Install Frontend Dependencies
Ensure Node.js 18+ is installed:
```bash
npm install
```

#### 3. Configure Frontend Environment
Copy the example environment file:
```bash
cp .env.example .env
```
Key configuration parameters in `frontend/.env`:
- `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1`
- `NEXT_PUBLIC_SUPABASE_URL=https://eufrawprayanwthhuvaj.supabase.co`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_3YczReP6yNU8WPGQuS8V9A_CFJaeYA1`

#### 4. Start Frontend Client
```bash
# Start Next.js Development Server (Port 3000):
npm run dev

# Or serve static Sentinel Triage Studio directly:
npm run serve
```

#### 5. Verify Frontend Types & Code
```bash
npm run lint
```

Frontend URLs:
- **Next.js Application**: [http://localhost:3000](http://localhost:3000)
- **Sentinel Triage Studio (Static)**: [http://localhost:3000/src/index.html](http://localhost:3000/src/index.html)

---

## 🔌 Frontend-to-Backend API Communication

The frontend client communicates purely via HTTP REST API calls:
- All prediction requests are dispatched to `POST /api/v1/predict/` with `V1`–`V28` PCA vectors and `Amount`.
- Batch transactions are submitted as arrays to `POST /api/v1/predict/batch`.
- Health and model metrics are queried via `GET /api/v1/health` and `GET /api/v1/analytics/stats`.
- Pre-configured fraud/legitimate presets are fetched from `GET /api/v1/predict/presets`.
- Full CORS middleware is enabled on the backend to permit requests from `http://localhost:3000` and all local origin variants.

---

## 🧪 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically isolates and tests both tiers independently on every push:
1. **`backend-test` Job**: Sets up Python 3.10 & 3.11, installs `backend/requirements.txt`, and runs `pytest tests/` inside `backend/`.
2. **`frontend-test` Job**: Sets up Node.js 20, installs `frontend/package.json`, and runs TypeScript type checking (`tsc --noEmit`).

---

## 📖 Persistent AI Context Framework

This repository uses a persistent context system for continuous AI alignment:
- [`decisions.md`](./decisions.md) - Architecture Decision Records (including ADR-005: Decoupled Structure).
- [`rules.md`](./rules.md) - Mandatory coding, security, and git standards.
- [`memory.md`](./memory.md) - Living knowledge base, active schemas, and roadmap.
- [`phases.md`](./phases.md) - Implementation milestones and tracking.
- [`changelog.md`](./changelog.md) - Keep-a-Changelog SemVer change history.

---

## 🚀 Step-by-Step Production Deployment Guide

You can deploy the decoupled Frontend and Backend using **Docker Compose** (single VPS / VM) or via **Modern Cloud Services** (Vercel for Frontend + Render / Railway for Backend).

### Strategy A: Cloud Microservice Deployment (Vercel + Render / Railway)

This is the recommended modern architecture for decoupled web applications.

#### Part 1: Deploy Backend (FastAPI + XGBoost Inference Engine)
Deploying to **Render**, **Railway**, or **Fly.io**:

1. **Push your code to GitHub**:
   Ensure all changes are committed and pushed to your GitHub repository.

2. **Create New Web Service on Render / Railway**:
   - Log into [Render](https://render.com) or [Railway](https://railway.app).
   - Select **New Web Service** and connect your GitHub repository.
   - Set **Root Directory**: `backend`
   - Set **Runtime**: `Python 3` (or **Docker** using `backend/Dockerfile`).
   - If using Python native runtime:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

3. **Configure Backend Environment Variables**:
   Under the service **Environment Variables** tab, define:
   ```env
   ENVIRONMENT=production
   PORT=8000
   HOST=0.0.0.0
   FRAUD_PROBABILITY_THRESHOLD=0.35
   REVIEW_PROBABILITY_THRESHOLD=0.20
   DATABASE_URL=sqlite:///./data/fraud_audit.db
   CORS_ORIGINS=["https://your-frontend-domain.vercel.app","http://localhost:3000"]
   SUPABASE_URL=https://eufrawprayanwthhuvaj.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   ```

4. **Verify Deployment**:
   Once build completes, verify health via:
   `https://your-backend-api.onrender.com/api/v1/health`

---

#### Part 2: Deploy Frontend (Next.js + Sentinel Studio)
Deploying to **Vercel** (the native host for Next.js):

1. **Import Project to Vercel**:
   - Log into [Vercel](https://vercel.com) and click **Add New Project**.
   - Select your GitHub repository.

2. **Configure Project Settings**:
   - **Root Directory**: Click *Edit* and select `frontend`.
   - **Framework Preset**: `Next.js` (automatically detected).
   - **Build Command**: `next build` (default).
   - **Output Directory**: `.next` (default).

3. **Configure Frontend Environment Variables**:
   Under **Environment Variables**, provide:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-api.onrender.com/api/v1
   NEXT_PUBLIC_SUPABASE_URL=https://eufrawprayanwthhuvaj.supabase.co
   NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_3YczReP6yNU8WPGQuS8V9A_CFJaeYA1
   ```

4. **Deploy**:
   - Click **Deploy**. Vercel will install dependencies, compile the TypeScript App Router pages, and link all assets.
   - Your Next.js app will be live at `https://your-frontend.vercel.app/`
   - Your static Sentinel Triage Studio workstation will be available at `https://your-frontend.vercel.app/index.html`.

---

### Strategy B: Docker & Docker Compose Deployment (Single VPS / AWS EC2 / DigitalOcean)

Ideal for deploying the entire platform on a single virtual server:

1. **SSH into your server and install Docker & Docker Compose**:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose git
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/SmitKulkarni/Credit_Card_Fraud_Detection_App.git
   cd Credit_Card_Fraud_Detection_App
   ```

3. **Verify Environment Configurations**:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

4. **Build and Launch Containers in Detached Mode**:
   ```bash
   docker-compose up -d --build
   ```

5. **Inspect Running Containers**:
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```
   - **Frontend**: Accessible on `http://<your-server-ip>:3000`
   - **Backend API**: Accessible on `http://<your-server-ip>:8000/api/v1`
   - **Swagger Docs**: Accessible on `http://<your-server-ip>:8000/docs`

---

## 📄 License
This project is licensed under the MIT License.

