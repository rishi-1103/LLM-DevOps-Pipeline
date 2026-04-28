"""
Pipeline orchestration module.
Implements LLM-based extraction workflows with retry logic,
exponential backoff, and structured error handling.
"""

import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── Retry decorator with exponential backoff ──────────────────────────────────
def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator that retries an async function with exponential backoff.
    Teaches pattern: don't just fail — retry intelligently.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    delay = base_delay * (2 ** (attempt - 1))  # exponential backoff
                    logger.warning(f"{func.__name__} attempt {attempt} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


# ── Pipeline step: entity extraction ─────────────────────────────────────────
@with_retry(max_attempts=3)
async def _extract_entities(text: str) -> dict:
    """
    Extracts named entities from text.
    In production this calls an LLM API (e.g. Anthropic/OpenAI).
    Here we demonstrate the pipeline structure with rule-based extraction.
    """
    logger.info("Running entity extraction step")

    # Simulate processing delay (real LLM API call would go here)
    await asyncio.sleep(0.05)

    # Rule-based entity detection (replace with LLM API call in production)
    words = text.split()
    entities = {
        "persons": [w for w in words if w.istitle() and len(w) > 2],
        "numbers": re.findall(r'\b\d+(?:\.\d+)?\b', text),
        "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
        "urls": re.findall(r'https?://\S+', text),
        "word_count": len(words),
        "char_count": len(text)
    }

    logger.info(f"Entity extraction complete: found {len(entities['persons'])} persons, {len(entities['numbers'])} numbers")
    return entities


# ── Pipeline step: keyword extraction ────────────────────────────────────────
@with_retry(max_attempts=3)
async def _extract_keywords(text: str) -> dict:
    """Extracts keywords using frequency analysis."""
    logger.info("Running keyword extraction step")
    await asyncio.sleep(0.03)

    # Stopwords filter
    stopwords = {"the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
                 "of", "and", "or", "but", "with", "this", "that", "are", "was",
                 "be", "by", "from", "as", "have", "has", "had", "not", "we", "i"}

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    freq = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1

    # Top 10 keywords by frequency
    top_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]

    logger.info(f"Keyword extraction complete: {len(top_keywords)} top keywords found")
    return {
        "keywords": [{"word": k, "frequency": v} for k, v in top_keywords],
        "unique_word_count": len(freq),
        "total_words": len(words)
    }


# ── Pipeline step: summarisation ─────────────────────────────────────────────
@with_retry(max_attempts=3)
async def _summarise(text: str, max_tokens: int) -> dict:
    """Generates a summary of the input text."""
    logger.info(f"Running summarisation step: max_tokens={max_tokens}")
    await asyncio.sleep(0.05)

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Simple extractive summary: first 2 sentences + last sentence
    if len(sentences) <= 3:
        summary_sentences = sentences
    else:
        summary_sentences = sentences[:2] + [sentences[-1]]

    summary = " ".join(summary_sentences)
    # Respect token approximation (1 token ≈ 4 chars)
    if len(summary) > max_tokens * 4:
        summary = summary[:max_tokens * 4] + "..."

    logger.info(f"Summarisation complete: {len(sentences)} sentences → {len(summary_sentences)} sentence summary")
    return {
        "summary": summary,
        "original_sentence_count": len(sentences),
        "summary_sentence_count": len(summary_sentences),
        "compression_ratio": round(len(summary) / len(text), 2)
    }


# ── Public pipeline runners ───────────────────────────────────────────────────
async def run_extraction_pipeline(text: str, extraction_type: str, max_tokens: int) -> dict:
    """
    Orchestrates the extraction pipeline.
    Validates input → routes to correct step → returns structured result.
    This is the LangGraph-style orchestration layer.
    """
    logger.info(f"Starting extraction pipeline: type={extraction_type}")

    # Input validation (fail fast)
    if extraction_type not in ("entities", "keywords"):
        raise ValueError(f"Unsupported extraction type: {extraction_type}. Use 'entities' or 'keywords'.")

    # Route to correct pipeline step
    if extraction_type == "entities":
        result = await _extract_entities(text)
    else:
        result = await _extract_keywords(text)

    return {"extraction_type": extraction_type, "data": result}


async def run_summarisation_pipeline(text: str, max_tokens: int) -> dict:
    """Orchestrates the summarisation pipeline."""
    logger.info("Starting summarisation pipeline")
    result = await _summarise(text, max_tokens)
    return {"extraction_type": "summary", "data": result}
