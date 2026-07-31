"""
NOVA Voice Assistant - FastAPI Application Entry Point
Refactored, high-performance, async-enabled AI Operating Assistant.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from core.assistant import Assistant
from routes.api import router as api_router, init_assistant
from routes.ws import ws_router, init_ws_assistant
import uvicorn
import logging

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nova.app")

# Shared assistant instance
assistant: Assistant = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global assistant
    logger.info("Initializing NOVA Assistant Core...")
    assistant = Assistant()
    init_assistant(assistant)
    init_ws_assistant(assistant)
    yield
    logger.info("Shutting down NOVA Assistant Core...")
    if assistant and assistant.is_running:
        assistant.stop()

# Initialize FastAPI application
app = FastAPI(
    title="NOVA AI Operating Assistant",
    description="Tool-based AI Operating Assistant powered by Gemini Function Calling & Plugin Architecture",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for React/Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(api_router)
app.include_router(ws_router)

@app.get("/")
def root():
    return {
        "name": settings.ASSISTANT_NAME,
        "role": "AI Operating Assistant",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    print(f"""
    ===================================================
          NOVA AI Operating Assistant
          Running on http://{settings.HOST}:{settings.PORT}
          Interactive Docs: http://localhost:{settings.PORT}/docs
    ===================================================
    """)
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
