"""
NOVA Voice Assistant — Vercel Serverless Entry Point (NOVA 3.0 Enterprise Architecture)
Exposes the FastAPI application for Vercel's serverless Python runtime.
"""

import os
import sys

# ── Make backend modules importable ───────────────────────────────────────────
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app
