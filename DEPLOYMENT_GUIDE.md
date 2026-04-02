# NOVA Voice Assistant - Deployment Guide

## Project Overview
- **Frontend**: React + Vite (builds to static files)
- **Backend**: Python Flask with SocketIO
- **Requirements**: Docker, API keys (Gemini)

---

## 📦 Docker Setup (Local Development & Testing)

### Prerequisites
- Docker Desktop installed
- `.env` file configured with `GEMINI_API_KEY`

### Running Locally with Docker

```bash
# Build the image
docker build -t voiceassistant:latest .

# Run the container
docker run -p 5000:5000 --env-file .env voiceassistant:latest

# Or use docker-compose
docker-compose up --build
```

**Access**: http://localhost:5000

---

## 🚀 Free Hosting Deployment Plan

### Option 1: **Railway.app** (Recommended) ⭐
**Cost**: Free tier includes $5/month credits, auto-pause when inactive

#### Setup Steps:
1. Create account at [railway.app](https://railway.app)
2. Connect GitHub repository
3. Create new project from GitHub
4. Add environment variables (Railway dashboard):
   - `GEMINI_API_KEY`
   - `SECRET_KEY` (generate: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `DEBUG=False`
5. Deploy via GitHub auto-deploy or manual railway deploy

#### Configuration:
- Create `railway.toml` in root:
```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "python -m flask run --host=0.0.0.0 --port=$PORT"
```

---

### Option 2: **Render.com**
**Cost**: Free tier with 15-minute inactivity auto-spin down

#### Setup Steps:
1. Create account at [render.com](https://render.com)
2. Connect GitHub repository
3. Create new "Web Service" 
4. Select Docker environment
5. Add environment variables
6. Deploy

**Pros**: Easy GitHub integration, persistent free tier
**Cons**: 15-minute auto-sleep, slower cold starts

---

### Option 3: **PythonAnywhere**
**Cost**: Free tier with limited resources

#### Setup Steps:
1. Upload code to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Configure Flask app
3. Set up environment variables in WebApp settings
4. Add your domain or use pythonanywhere.com subdomain

**Pros**: Python-native, no Docker required
**Cons**: Limited only to Python, resource constraints

---

## Frontend Hosting Options

### Option 1: **Vercel** (Recommended) ⭐
**Cost**: Free tier generous, perfect for React

#### Setup:
1. Build frontend: `npm run build`
2. Deploy to [vercel.com](https://vercel.com):
   - Connect GitHub repository
   - Vercel auto-detects Vite
   - Set build: `npm run build`
   - Output directory: `dist`

#### Environment:
Add `.env.production`:
```
VITE_API_URL=https://your-railway-app.up.railway.app
```

---

### Option 2: **Netlify**
**Cost**: Free tier with deployment limits

#### Setup:
1. Connect GitHub to [netlify.com](https://netlify.com)
2. Build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
3. Set redirect rules for API in `netlify.toml`

---

### Option 3: **GitHub Pages**
**Cost**: Free

#### Setup:
```bash
npm run build
# Deploy dist folder to gh-pages branch
```

---

## ⚡ Recommended Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│              Frontend (React/Vite)              │
│         Hosted on Vercel or Netlify             │
│   (Auto-deploy from GitHub on push to main)     │
└────────────┬────────────────────────────────────┘
             │
             │ API Calls + WebSocket
             │
┌────────────▼────────────────────────────────────┐
│        Backend (Flask + SocketIO)               │
│    Hosted on Railway or Render (Docker)         │
│ (Auto-deploy from GitHub on push to main)       │
└─────────────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Deployment Process

### Phase 1: Prepare Repository
```bash
# 1. Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: NOVA Voice Assistant"

# 2. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/voiceassistant.git
git push -u origin main
```

### Phase 2: Deploy Backend
```bash
# Using Railway (Recommended):
npm install -g @railway/cli
railway link
railway up --detach
```

Or go to Railway dashboard, connect GitHub, and deploy via UI.

### Phase 3: Deploy Frontend
1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com) → Import Project
3. Select your GitHub repository
4. Vercel auto-configures for Vite
5. Add environment variable: `VITE_API_URL=<your-railway-backend-url>`
6. Deploy

### Phase 4: Configure API URL
Update [services/api.js](frontend/src/services/api.js):
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
```

---

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` to secure random string
- [ ] Set `DEBUG=False` in production
- [ ] Use `HTTPS` (auto-handled by Railway/Netlify/Vercel)
- [ ] Add `GEMINI_API_KEY` to hosting provider secret management
- [ ] Update CORS settings for production domain
- [ ] Add rate limiting to API endpoints
- [ ] Use environment-specific `.env` files

---

## 💾 Environment Variables for Production

Create these in your hosting provider's dashboard:

**Backend**:
```
SECRET_KEY=<random-32-char-string>
DEBUG=False
GEMINI_API_KEY=<your-api-key>
PORT=5000
HOST=0.0.0.0
```

**Frontend (Vercel/Netlify)**:
```
VITE_API_URL=https://your-backend-url.com
```

---

## 🧪 Testing Deployment

1. **Backend Health Check**:
   ```bash
   curl https://your-backend-url.com/api/health
   ```

2. **Frontend Load**:
   - Visit frontend URL
   - Check browser console for API connection errors
   - Test WebSocket connection

3. **End-to-End Test**:
   - Send a voice command from frontend
   - Verify response from backend

---

## 🛠 Troubleshooting

### Port Issues
- Railway/Render automatically assign ports using `$PORT` env var
- Dockerfile exposes port 5000, but hosting assigns actual port

### CORS Errors
- Update CORS in [backend/app.py](backend/app.py)
- Add production domain to allowed origins

### WebSocket Connection Issues
- Ensure SocketIO client points to correct API URL
- Check that hosting provider supports long-lived connections (most do)

### Build Failures
- Check Docker build logs
- Ensure all dependencies in `requirements.txt`
- Verify Node version compatibility

---

## 📊 Cost Breakdown

| Service | Cost | Best For |
|---------|------|----------|
| Railway | $5/month free credits | Backend (Python) |
| Render | Free (limited) | Backend alternative |
| Vercel | Free | Frontend |
| Netlify | Free | Frontend alternative |
| Custom VPS | $3-5/month | Full control |

**Total Estimated Cost**: $0-5/month (both free tiers)

---

## 🔄 Continuous Deployment Setup

### Option A: GitHub Actions (Recommended)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway up --detach
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Option B: Platform Auto-Deploy
- Railway: Enable auto-deploy from GitHub branch
- Vercel/Netlify: Enable GitHub integration (automatic)

---

## 📝 Next Steps

1. **Prepare Docker locally**: `docker-compose up`
2. **Test everything works**: Visit http://localhost:5000
3. **Push to GitHub**: `git push origin main`
4. **Deploy Backend**: Use Railway dashboard or CLI
5. **Deploy Frontend**: Connect Vercel to GitHub repo
6. **Update API URLs**: Configure frontend to use production backend
7. **Monitor**: Set up alerts in hosting provider dashboard

---

## 🚨 Important Notes

- **Voice Input**: Works in browser only (requires HTTPS in production)
- **Microphone Permissions**: Users must grant browser microphone access
- **System Control**: System commands won't work on hosted backend (no system access)
- **Storage**: Use persistent volumes for `output/` and `notes/` directories

---

For questions or issues, check the hosting provider documentation:
- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
