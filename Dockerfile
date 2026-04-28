# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# Install dependencies in a separate stage to keep the final image lean
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy only requirements first — Docker layer caching means this layer
# is only rebuilt when requirements.txt changes, not on every code change
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt --target=/build/deps

# ── Stage 2: Production image ─────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /build/deps /usr/local/lib/python3.11/site-packages/

# Copy application source
COPY src/ .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# CRITICAL: Read PORT from environment variable — do NOT hardcode.
# GCP Cloud Run injects PORT at runtime. Azure Container Apps does the same.
# Hardcoding a port is the #1 cause of container crashes on cloud platforms.
ENV PORT=8080

EXPOSE 8080

# Health check — Docker will mark the container unhealthy if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

# Start the application
CMD ["sh", "-c", "python main.py"]
