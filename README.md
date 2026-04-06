# mlops-pipeline-lab

Production-grade MLOps deployment pipeline demonstrating infrastructure engineering discipline applied to ML workloads. Takes a pre-trained HuggingFace sentiment analysis model and wraps it with container hardening, CI/CD automation, GitOps deployment, observability, and policy enforcement.

**The infrastructure is the point** — not the model.

## What This Demonstrates

- **Model Serving**: FastAPI wrapping `distilbert-base-uncased-finetuned-sst-2-english` with `/predict`, `/health`, `/metrics` endpoints
- **Container Hardening**: Multi-stage Docker build, non-root execution, read-only filesystem, dropped capabilities
- **CI/CD Pipeline**: GitHub Actions with lint → test → build → Trivy scan → Syft SBOM → GHCR push
- **GitOps**: ArgoCD auto-syncing Kubernetes manifests from this repo
- **Observability**: Prometheus metrics, Grafana dashboards (latency, throughput, error rate, prediction distribution), Loki log aggregation
- **Policy Enforcement**: Kyverno policies requiring scanned images, SBOMs, non-root containers, and resource limits

## Quick Start

```bash
# Run locally
python3 -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload

# Test
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is great!"}'
```

```bash
# Docker
docker build -f docker/Dockerfile -t sentiment-api:local .
docker run -p 8000:8000 sentiment-api:local
```

See [docs/setup.md](docs/setup.md) for full K3s + monitoring stack setup.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness/readiness check |
| `/predict` | POST | Sentiment analysis (`{"text": "..."}` → `{"label": "POSITIVE", "score": 0.99}`) |
| `/metrics` | GET | Prometheus metrics (request latency, prediction counts, errors) |

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system diagram.

## Related Projects

- [container-hardening-lab](https://github.com/R055LE/container-hardening-lab) — Reuses the same hardening patterns (Trivy, Syft, non-root, distroless)

## License

MIT
