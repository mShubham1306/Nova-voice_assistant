# Docker Quick Start Guide

## Prerequisites
- Docker Desktop installed (includes docker-compose)
- `.env` file with required API keys

## Build & Run

### Option 1: Using docker-compose (Easiest)
```bash
# Development mode with hot-reload
docker-compose up --build

# Production mode
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Manual Docker commands
```bash
# Build the image
docker build -t voiceassistant:latest .

# Run the container
docker run -p 5000:5000 \
  --env-file .env \
  --name voiceassistant \
  voiceassistant:latest

# Stop and remove
docker stop voiceassistant
docker rm voiceassistant
```

## Access
- **Frontend**: http://localhost:5000
- **API**: http://localhost:5000/api

## Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Troubleshooting

### Port already in use
```bash
# Find process using port 5000
lsof -i :5000
# Or use different port
docker run -p 5001:5000 voiceassistant:latest
```

### Build fails
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker build --no-cache -t voiceassistant:latest .
```

### Check logs
```bash
docker logs voiceassistant
docker logs -f voiceassistant  # Follow logs
```

## For Production Deployment
See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
