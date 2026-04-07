# MLOps Pipeline Lab

Production-grade MLOps deployment pipeline demonstrating infrastructure engineering discipline applied to ML workloads. Takes a pre-trained HuggingFace sentiment analysis model and wraps it with container hardening, CI/CD automation, GitOps deployment, observability, and policy enforcement.

**The infrastructure is the point** — not the model.

## Why This Exists

The same infrastructure rigor applied to traditional workloads — container hardening, CI/CD automation, GitOps deployment, observability, policy enforcement — applied to AI/ML serving infrastructure. The model is deliberately simple (sentiment analysis). Everything around operating it in production is the focus.

## What This Demonstrates

- **Model Serving**: FastAPI wrapping `distilbert-base-uncased-finetuned-sst-2-english` with `/predict`, `/health`, `/metrics` endpoints
- **Container Hardening**: Multi-stage Docker build, non-root execution (UID 999), read-only filesystem, dropped capabilities, model baked into image for offline operation
- **CI/CD Pipeline**: GitHub Actions with lint → test → build → Trivy scan → Syft SBOM → GHCR push
- **GitOps**: ArgoCD auto-syncing Kubernetes manifests from this repo
- **Observability**: Prometheus metrics (request latency histograms, prediction counters, error counters), Grafana dashboards, Loki log aggregation
- **Policy Enforcement**: Kyverno policies requiring scanned images, SBOMs, non-root containers, and resource limits

## Quick Start

### Run Locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload
```

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Sentiment prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is great!"}'
# → {"label":"POSITIVE","score":0.9999}

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Run with Docker

```bash
docker build -f docker/Dockerfile -t sentiment-api:local .
docker run -p 8000:8000 sentiment-api:local
```

See [docs/setup.md](docs/setup.md) for full K3s cluster + monitoring stack setup.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness/readiness check |
| `/predict` | POST | Sentiment analysis (`{"text": "..."}` → `{"label": "POSITIVE", "score": 0.99}`) |
| `/metrics` | GET | Prometheus metrics (request latency, prediction counts, errors) |

### Example Request/Response

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "The deployment pipeline works perfectly"}'
```

```json
{"label": "POSITIVE", "score": 0.9998}
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system diagram and design decisions.

## Project Structure

```
mlops-pipeline-lab/
├── app/                    # FastAPI application
│   ├── main.py             # API endpoints and middleware
│   ├── model.py            # HuggingFace model loading/inference
│   ├── metrics.py          # Prometheus instrumentation
│   ├── requirements.txt    # Pinned Python dependencies
│   └── tests/
│       └── test_api.py     # Endpoint tests
├── docker/
│   └── Dockerfile          # Multi-stage hardened build with baked-in model
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI pipeline
├── .gitlab-ci.yml          # GitLab CI reference config
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yml       # ml-serving namespace
│   ├── deployment.yml      # Hardened deployment (non-root, read-only fs, resource limits)
│   ├── service.yml         # ClusterIP service
│   ├── ingress.yml         # Nginx ingress
│   └── hpa.yml             # Horizontal Pod Autoscaler (2-5 replicas)
├── argocd/
│   └── application.yml     # ArgoCD GitOps application
├── monitoring/
│   ├── prometheus/         # Scrape config for sentiment-api pods
│   ├── grafana/            # Dashboards (latency, throughput, errors, prediction distribution)
│   └── loki/               # Log aggregation config
├── policies/               # Kyverno cluster policies
│   ├── require-scan.yml    # Images must come from GHCR
│   ├── require-sbom.yml    # SBOM annotation required
│   ├── require-nonroot.yml # Non-root containers enforced
│   └── require-resource-limits.yml
└── docs/
    ├── setup.md            # Local setup walkthrough
    ├── pipeline.md         # CI/CD pipeline details
    └── architecture.md     # System design and decisions
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Model baked into Docker image | Containers must run offline — no runtime downloads from HuggingFace. Ensures reproducibility and removes external dependency at deploy time. |
| CPU-only inference | Infrastructure patterns are the focus, not GPU optimization. Keeps the project runnable on any machine. |
| Trivy gate on CRITICAL only | HIGH-severity CVEs in upstream `python:3.12-slim` (e.g., ncurses) are not actionable. CRITICAL gate avoids false-positive pipeline failures. |
| Image name lowercased in CI | GHCR requires lowercase repository names. GitHub's `${{ github.repository }}` preserves case, so the pipeline normalizes it. |
| Numeric `runAsUser: 999` in K8s | K8s `runAsNonRoot` cannot verify non-root status with named users (e.g., `appuser`). Numeric UID resolves this. |
| `TRANSFORMERS_OFFLINE=1` | Prevents the transformers library from attempting network calls at runtime, enforcing use of the baked-in model cache. |

## Related Projects

- [container-hardening-lab](https://github.com/R055LE/container-hardening-lab) — Reuses the same hardening patterns (Trivy, Syft, non-root, distroless)

## License

MIT
