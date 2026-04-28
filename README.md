# LLM Automation Pipeline 🚀

A **cloud-native FastAPI service** for LLM-based data extraction and automation workflows, deployed on **Google Cloud Platform** with a fully automated **CI/CD pipeline** using GitHub Actions.

> Built by [Subhadeep Barman](https://linkedin.com/in/subhadeep-barman-254a38215) — demonstrating end-to-end DevOps practices: containerisation, CI/CD automation, cloud deployment, observability, and security best practices.

---

## Architecture

```
Developer pushes code
        │
        ▼
┌─────────────────────────────────────────────────────┐
│              GitHub Actions CI/CD Pipeline           │
│                                                     │
│  [Lint] ──► [Test] ──► [Build & Push] ──► [Deploy] │
│   ~30s       ~45s         ~2 min           ~1 min   │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────┐     ┌──────────────────────┐
│  GCP Artifact       │────►│  GCP Cloud Run       │
│  Registry           │     │  (auto-scaling,      │
│  (Docker images)    │     │   0 to 3 instances)  │
└─────────────────────┘     └──────────────────────┘
        │                           │
        │                   ┌───────▼──────────┐
        │                   │  GCP Cloud       │
        └───────────────────│  Logging         │
                            │  (observability) │
                            └──────────────────┘
```

## Features

- **REST API** built with FastAPI — entity extraction, keyword extraction, summarisation
- **Retry logic with exponential backoff** — fault-tolerant pipeline execution
- **Docker multi-stage build** — lean production image, non-root user, health checks
- **GitHub Actions CI/CD** — lint → test → build → deploy in ~4 minutes end-to-end
- **GCP Cloud Run deployment** — serverless, auto-scaling, zero cold-start cost when idle
- **Structured JSON logging** — compatible with GCP Cloud Logging
- **Liveness & readiness probes** — `/health` and `/ready` endpoints for Kubernetes/Cloud Run

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Framework | FastAPI + Uvicorn |
| Containerisation | Docker (multi-stage build) |
| CI/CD | GitHub Actions |
| Container Registry | GCP Artifact Registry |
| Cloud Platform | Google Cloud Platform (Cloud Run) |
| Observability | GCP Cloud Logging (structured JSON) |
| Testing | pytest |
| Code Quality | flake8, black |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/extract` | Run extraction pipeline |
| GET | `/pipeline/status` | Pipeline configuration |

### Example Request

```bash
curl -X POST https://your-cloud-run-url/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Subhadeep Barman is a DevOps engineer based in Kolkata. Contact: subhadeep@example.com",
    "extraction_type": "entities"
  }'
```

### Example Response

```json
{
  "status": "success",
  "result": {
    "extraction_type": "entities",
    "data": {
      "persons": ["Subhadeep", "Barman", "DevOps", "Kolkata"],
      "emails": ["subhadeep@example.com"],
      "numbers": [],
      "word_count": 14
    }
  },
  "processing_time_ms": 52.3,
  "timestamp": "2026-04-28T10:30:00.000Z"
}
```

---

## Running Locally

### With Docker (recommended)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/llm-devops-pipeline.git
cd llm-devops-pipeline

# Build and run with Docker Compose
docker-compose up --build

# Service available at http://localhost:8080
curl http://localhost:8080/health
```

### Without Docker

```bash
cd src
pip install -r ../requirements.txt
python main.py
```

### Run Tests

```bash
pip install -r requirements.txt
cd tests
pytest test_pipeline.py -v
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/cicd.yml`) has four jobs:

```
Push to main
    │
    ├── lint        flake8 + black formatting check (~30s)
    │                         │ fail fast
    ├── test        pytest unit tests (~45s)
    │                         │ only if tests pass
    ├── build       Docker build → tag with commit SHA → push to Artifact Registry (~2min)
    │                         │ only on main branch
    └── deploy      Cloud Run deploy → health check verification (~1min)
```

**Image tagging strategy:** Every image is tagged with the Git commit SHA (e.g. `image:a3f2c1b`) so every running instance maps back to an exact code commit — enabling precise rollbacks.

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GCP_SA_KEY` | GCP Service Account JSON key (with Cloud Run Admin + Artifact Registry Writer roles) |
| `GCP_PROJECT_ID` | Your GCP project ID |

---

## Key Engineering Decisions

**Why multi-stage Docker build?**
The builder stage installs all dependencies; the production stage copies only what's needed. This reduces the final image size by ~60% and reduces attack surface.

**Why tag images with commit SHA?**
Rolling back a broken deployment is a single command: redeploy the previous SHA tag. No guessing which image was running before.

**Why read PORT from environment variable?**
GCP Cloud Run (and Azure Container Apps) injects the PORT at runtime. Hardcoding port 5000 was the #1 cause of container crashes on cloud platforms — this pattern prevents that.

**Why non-root user in Docker?**
Running as root inside a container is a security risk. If the container is compromised, the attacker gets root access. Non-root user limits the blast radius.

---

## Author

**Subhadeep Barman**
- LinkedIn: [linkedin.com/in/subhadeep-barman-254a38215](https://linkedin.com/in/subhadeep-barman-254a38215)
- LeetCode: [leetcode.com/u/rishi_0311](https://leetcode.com/u/rishi_0311)
- Email: barmanrishi11@gmail.com
