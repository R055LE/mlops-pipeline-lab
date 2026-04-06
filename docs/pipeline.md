# CI/CD Pipeline

## Overview

The pipeline runs on every push and PR against `main`. It follows a gated flow:

```
lint → test → build → scan → push → deploy (via ArgoCD)
```

## Stages

### Lint & Test
- **Ruff** for Python linting
- **pytest** for unit/integration tests against the FastAPI app

### Build
- Multi-stage Docker build from `docker/Dockerfile`
- Non-root execution, slim base image
- Tagged with git short SHA and `latest`

### Scan
- **Trivy** scans the built image for CRITICAL and HIGH vulnerabilities
- Pipeline fails if any are found (security gate)
- **Syft** generates an SPDX SBOM uploaded as a build artifact

### Push
- Only on `main` branch pushes (not PRs)
- Pushes to GitHub Container Registry (`ghcr.io`)

### Deploy
- ArgoCD watches the `k8s/` directory for changes
- Auto-sync with pruning and self-heal enabled
- No manual deploy step needed — push to main triggers the full flow

## GitHub Actions vs GitLab CI

Both configurations implement the same pipeline stages:
- **GitHub Actions** (`.github/workflows/ci.yml`) — primary, runs on GitHub
- **GitLab CI** (`.gitlab-ci.yml`) — reference config for portability
