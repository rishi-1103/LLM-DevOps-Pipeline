"""
LLM Automation Pipeline Service
Author: Subhadeep Barman
Description: A cloud-native FastAPI service that orchestrates LLM-based
             data extraction and automation workflows.
"""

import os
import logging
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline import run_extraction_pipeline, run_summarisation_pipeline
from health import router as health_router

# ── Structured logging setup ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# ── App init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="LLM Automation Pipeline",
    description="Cloud-native LLM service for data extraction and automation workflows",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)

# ── Request / Response models ─────────────────────────────────────────────────
class ExtractionRequest(BaseModel):
    text: str
    extraction_type: str = "entities"   # entities | keywords | summary
    max_tokens: Optional[int] = 500

class PipelineResponse(BaseModel):
    status: str
    result: dict
    processing_time_ms: float
    timestamp: str

# ── Middleware: request logging ───────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start).total_seconds() * 1000
    logger.info(json.dumps({
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round(duration, 2)
    }))
    return response

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": "LLM Automation Pipeline",
        "version": "1.0.0",
        "author": "Subhadeep Barman",
        "status": "running"
    }

@app.post("/extract", response_model=PipelineResponse)
async def extract(req: ExtractionRequest):
    """
    Run LLM-based extraction on input text.
    Supports entity extraction, keyword extraction, and summarisation.
    """
    start = datetime.utcnow()
    logger.info(f"Extraction request received: type={req.extraction_type}, text_length={len(req.text)}")

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")

    if len(req.text) > 10000:
        raise HTTPException(status_code=400, detail="Input text exceeds 10,000 character limit")

    try:
        if req.extraction_type == "summary":
            result = await run_summarisation_pipeline(req.text, req.max_tokens)
        else:
            result = await run_extraction_pipeline(req.text, req.extraction_type, req.max_tokens)

        duration = (datetime.utcnow() - start).total_seconds() * 1000
        logger.info(f"Extraction completed in {round(duration, 2)}ms")

        return PipelineResponse(
            status="success",
            result=result,
            processing_time_ms=round(duration, 2),
            timestamp=datetime.utcnow().isoformat()
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal pipeline error. Check logs for details.")

@app.get("/pipeline/status")
async def pipeline_status():
    """Returns current pipeline configuration and status."""
    return {
        "pipeline_version": "1.0.0",
        "supported_extraction_types": ["entities", "keywords", "summary"],
        "max_input_length": 10000,
        "environment": os.getenv("ENVIRONMENT", "production"),
        "timestamp": datetime.utcnow().isoformat()
    }

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))   # GCP Cloud Run injects PORT env var
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
