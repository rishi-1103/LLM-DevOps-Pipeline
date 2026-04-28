"""
Health check endpoints.
Cloud Run and Kubernetes both probe /health for liveness and readiness.
This is a required pattern for any production containerised service.
"""

import os
import time
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()
START_TIME = time.time()

@router.get("/health")
async def health():
    """
    Liveness probe — Cloud Run and Kubernetes call this to check if the
    container is alive. If this returns non-200, the container is restarted.
    """
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@router.get("/ready")
async def ready():
    """
    Readiness probe — signals the container is ready to receive traffic.
    In production you'd check DB connections, model load status, etc.
    """
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }
