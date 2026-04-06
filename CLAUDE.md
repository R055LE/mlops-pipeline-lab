# CLAUDE.md — mlops-pipeline-lab

## Project Overview

A production-grade MLOps deployment pipeline that takes a pre-trained HuggingFace model, containerizes it with security hardening, deploys it to Kubernetes via GitOps, and instruments it with full observability. Demonstrates infrastructure engineering discipline applied to ML workloads — not model building, but everything around operating a model in production.

**Portfolio narrative:** "The same infrastructure rigor I apply to traditional workloads — container hardening, CI/CD automation, GitOps deployment, observability, policy enforcement — applied to AI/ML serving infrastructure."

## Git Conventions

- **Do NOT add co-author trailers to commits.** No `Co-authored-by` lines. Just write clean conventional commits.
- Use conventional commit format: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, etc.
- Keep commits atomic and descriptive.

## Architecture

### Model Serving Layer
- FastAPI application wrapping a small HuggingFace model (sentiment analysis or text classification)
- Must run on CPU only — no GPU dependencies
- Expose REST API endpoints: `/predict`, `/health`, `/metrics`
- Prometheus metrics instrumented directly in the app (request latency histograms, prediction counters, error counters)

### Container Build
- Hardened Dockerfile: multi-stage build, distroless or python-slim final image
- Non-root execution
- Trivy vulnerability scanning integrated into CI
- Syft SBOM generation as build artifact
- Push to GitHub Container Registry (ghcr.io)

### CI/CD
- **GitHub Actions** (`.github/workflows/`) — primary, fully functional, runs on push
- **GitLab CI** (`.gitlab-ci.yml`) — included as a functional reference config; tested against GitLab.com is a longer-term goal
- Pipeline stages: lint → test → build → scan → push → deploy
- Security scanning gate: pipeline fails if critical/high vulnerabilities found

### GitOps Deployment
- ArgoCD application manifests watching the repo for changes
- Target: local K3s cluster
- Kubernetes manifests in `k8s/` directory (Deployment, Service, Ingress, HPA)
- Namespace isolation for the ML workload

### Observability Stack
- Prometheus: scrape FastAPI app metrics + K8s cluster metrics
- Grafana: pre-built dashboards for model serving (request latency, throughput, error rate, prediction distribution)
- Loki: log aggregation from the model serving pods
- All deployed via Helm charts or manifests in `monitoring/`

### Policy Enforcement
- OPA/Kyverno policies in `policies/`
- Enforce: only scanned images deploy, SBOM must exist, non-root containers only, resource limits required
- Ties directly to the container-hardening-lab project narrative

## Directory Structure

```
mlops-pipeline-lab/
├── CLAUDE.md
├── README.md
├── LICENSE (MIT)
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitlab-ci.yml
├── app/
│   ├── main.py              # FastAPI application
│   ├── model.py              # HuggingFace model loading/inference
│   ├── metrics.py            # Prometheus instrumentation
│   ├── requirements.txt
│   └── tests/
│       └── test_api.py
├── docker/
│   └── Dockerfile            # Multi-stage hardened build
├── k8s/
│   ├── namespace.yml
│   ├── deployment.yml
│   ├── service.yml
│   ├── ingress.yml
│   └── hpa.yml
├── argocd/
│   └── application.yml       # ArgoCD app definition
├── monitoring/
│   ├── prometheus/
│   │   └── values.yml        # Helm values or config
│   ├── grafana/
│   │   ├── values.yml
│   │   └── dashboards/
│   │       └── model-serving.json
│   └── loki/
│       └── values.yml
├── policies/
│   ├── require-scan.yml
│   ├── require-sbom.yml
│   ├── require-nonroot.yml
│   └── require-resource-limits.yml
└── docs/
    ├── setup.md              # Local K3s + tooling setup
    ├── pipeline.md           # CI/CD walkthrough
    └── architecture.md       # System design diagram/explanation
```

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI + Uvicorn
- **ML:** HuggingFace Transformers (small CPU model, e.g. `distilbert-base-uncased-finetuned-sst-2-english`)
- **Container:** Docker, multi-stage build, distroless/slim base
- **Registry:** GitHub Container Registry (ghcr.io)
- **CI/CD:** GitHub Actions (primary), GitLab CI (reference config)
- **Kubernetes:** K3s (local)
- **GitOps:** ArgoCD
- **Monitoring:** Prometheus, Grafana, Loki
- **Security:** Trivy (vuln scan), Syft (SBOM), OPA or Kyverno (policy)
- **IaC:** Kubernetes manifests (YAML), Helm where appropriate

## Build Order

Recommended implementation sequence:

1. **App first** — FastAPI + HuggingFace model loading + /predict endpoint + basic tests
2. **Dockerfile** — Multi-stage hardened build, verify it runs locally
3. **CI pipeline** — GitHub Actions: lint, test, build, scan, push to GHCR
4. **K8s manifests** — Deployment, Service, get it running on K3s manually
5. **ArgoCD** — GitOps automation pointing at the k8s/ directory
6. **Monitoring** — Deploy Prometheus/Grafana/Loki, wire up dashboards
7. **Policies** — OPA/Kyverno enforcement rules
8. **GitLab CI** — Port the pipeline config, test against GitLab.com (stretch goal)
9. **Docs + README** — Architecture diagrams, setup guide, polish

## Key Constraints

- Everything must run locally on WSL/K3s — no cloud costs
- CPU-only model inference — no GPU requirements
- Keep the ML model simple; the infrastructure is the point
- GHCR for public visibility — anyone can pull and verify
- README should clearly explain what this demonstrates and why it matters for production ML serving

## Relationship to Other Projects

- **container-hardening-lab**: This project reuses the same hardening patterns (Trivy, Syft, non-root, distroless). Cross-reference in README.
- **Future: ml-security-scanner-lab (planned)**: Will extend into model supply chain security — scanning ML artifacts the way Iron Bank scans container images.
