# P2P Fraud Detective FR — image Docker multi-stage
# Build : docker build -t p2p-fraud-detective .
# Run   : docker run -p 8000:8000 -e FRAUD_API_SECRET=secret p2p-fraud-detective

# ─── Stage 1 : builder ────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Dépendances système pour weasyprint et lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn[standard] gunicorn && \
    pip install --no-cache-dir -r requirements.txt

# ─── Stage 2 : runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Dépendances système (runtime uniquement)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ /app/src/
COPY data/ /app/data/
COPY pyproject.toml /app/

RUN pip install --no-cache-dir -e /app

# Utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Variables d'environnement par défaut (à surcharger en production)
ENV FRAUD_API_SECRET="" \
    FRAUD_CASES_DB="/app/data/cases.db" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# API FastAPI (mode production : gunicorn + uvicorn worker)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "p2p_fraud.api.main:app"]
