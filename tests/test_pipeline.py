"""
Unit tests for the LLM Automation Pipeline.
Tests run automatically in the CI/CD pipeline on every push.
"""

import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
from main import app
from pipeline import run_extraction_pipeline, run_summarisation_pipeline

client = TestClient(app)

# ── Health endpoint tests ─────────────────────────────────────────────────────
def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ready_returns_200():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

def test_root_returns_service_info():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "LLM Automation Pipeline"

# ── Extraction endpoint tests ─────────────────────────────────────────────────
def test_extract_entities_success():
    response = client.post("/extract", json={
        "text": "Subhadeep Barman works at Brainware University in Kolkata. Contact: test@example.com",
        "extraction_type": "entities"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "data" in body["result"]
    assert body["processing_time_ms"] > 0

def test_extract_keywords_success():
    response = client.post("/extract", json={
        "text": "DevOps engineers use Docker and Kubernetes to manage containerised applications on cloud platforms.",
        "extraction_type": "keywords"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    keywords = body["result"]["data"]["keywords"]
    assert len(keywords) > 0

def test_extract_summary_success():
    response = client.post("/extract", json={
        "text": "Python is a programming language. It is widely used in data science and DevOps automation. Many engineers prefer it for scripting tasks.",
        "extraction_type": "summary"
    })
    assert response.status_code == 200

def test_extract_empty_text_returns_400():
    response = client.post("/extract", json={
        "text": "",
        "extraction_type": "entities"
    })
    assert response.status_code == 400

def test_extract_text_too_long_returns_400():
    response = client.post("/extract", json={
        "text": "a" * 10001,
        "extraction_type": "entities"
    })
    assert response.status_code == 400

def test_pipeline_status():
    response = client.get("/pipeline/status")
    assert response.status_code == 200
    assert "entities" in response.json()["supported_extraction_types"]

# ── Pipeline unit tests ───────────────────────────────────────────────────────
def test_pipeline_entity_extraction():
    result = asyncio.run(run_extraction_pipeline(
        "Send an email to john@example.com about the 500 dollar budget.",
        "entities",
        500
    ))
    assert result["extraction_type"] == "entities"
    assert "emails" in result["data"]
    assert "john@example.com" in result["data"]["emails"]

def test_pipeline_keyword_extraction():
    result = asyncio.run(run_extraction_pipeline(
        "Kubernetes Docker containers cloud deployment pipeline automation",
        "keywords",
        500
    ))
    assert result["extraction_type"] == "keywords"
    assert len(result["data"]["keywords"]) > 0

def test_pipeline_invalid_type_raises():
    with pytest.raises(ValueError):
        asyncio.run(run_extraction_pipeline("some text", "invalid_type", 500))

def test_summarisation_pipeline():
    result = asyncio.run(run_summarisation_pipeline(
        "First sentence about DevOps. Second sentence about Docker. Third sentence about Kubernetes. Fourth sentence about CI/CD pipelines.",
        500
    ))
    assert "summary" in result["data"]
    assert result["data"]["compression_ratio"] <= 1.0
