# ─── Stage 1: Build Frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python Backend Runtime ─────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio (portaudio), GUI (xvfb, scrot),
# and build tools (gcc). These are needed by pyttsx3, sounddevice, pyautogui.
RUN apt-get update && apt-get install -y \
    gcc \
    portaudio19-dev \
    libespeak-ng1 \
    espeak-ng \
    libxcb-xinerama0 \
    scrot \
    python3-xlib \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy pre-built frontend
COPY --from=frontend-build /app/frontend/dist ./backend/static

# Create writable data directories
RUN mkdir -p ./backend/data/notes ./backend/data/screenshots ./backend/data/workflows

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=5000

EXPOSE 5000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "5000"]
