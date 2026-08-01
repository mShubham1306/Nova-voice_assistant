# ─── NOVA Backend — Render.com Production Deployment ────────────────────────
# Serves ONLY the FastAPI backend. Frontend is served separately on Vercel.

FROM python:3.11-slim

WORKDIR /app

# Minimal system deps — build tools only
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

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV HOST=0.0.0.0

# Render injects $PORT dynamically (defaults to 10000)
EXPOSE 10000

CMD uvicorn backend.app:app \
    --host 0.0.0.0 \
    --port ${PORT:-10000} \
    --workers 2 \
    --loop uvloop \
    --http h11 \
    --proxy-headers \
    --forwarded-allow-ips='*'
