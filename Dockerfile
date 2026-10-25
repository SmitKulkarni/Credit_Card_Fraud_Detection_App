# ==============================================================================
# Multi-stage production Dockerfile for Credit Card Fraud Detection Application
# ==============================================================================

# Build Stage: compile dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Stage
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    ENVIRONMENT=production \
    PORT=8000 \
    HOST=0.0.0.0

# Install runtime libgomp for XGBoost C++ acceleration
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged security user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser

# Copy installed python wheels from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code and models
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser .env.example ./.env

# Create data directory with write permissions for SQLite database
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data /home/appuser

USER appuser

EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
