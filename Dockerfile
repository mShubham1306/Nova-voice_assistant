# ─── NOVA Backend — Render.com Production Deployment ────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Create writable data directories
RUN mkdir -p /tmp/nova_data/notes /tmp/nova_data/screenshots /tmp/nova_data/output && \
    chmod -R 777 /tmp/nova_data

# ── CRITICAL: PYTHONPATH must include backend/ so 'config', 'core', etc. resolve
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV HOST=0.0.0.0

EXPOSE 10000

# Run from /app/backend so relative imports work correctly
WORKDIR /app/backend

CMD uvicorn app:app \
    --host 0.0.0.0 \
    --port ${PORT:-10000} \
    --workers 1 \
    --loop uvloop \
    --http h11 \
    --proxy-headers \
    --forwarded-allow-ips='*'
