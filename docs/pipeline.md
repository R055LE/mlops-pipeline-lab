# CI/CD Pipeline

## Overview

The pipeline runs on every push and PR against `main`. It follows a gated flow:

```
lint → test → build → scan → SBOM → push → deploy (via ArgoCD)
```

Two jobs run sequentially: `lint-and-test` must pass before `build-scan-push` begins.

## Stages

### Lint & Test (`lint-and-test`)
- **Ruff** for Python linting
- **pytest** for unit/integration tests against the FastAPI app
- Uses pip caching keyed on `app/requirements.txt` for faster runs

### Build
- Multi-stage Docker build from `docker/Dockerfile`
- Model is downloaded and baked into the image during build (not at runtime)
- Non-root execution (UID 999), slim base image
- Tagged with both git short SHA and `latest`
- Image name is lowercased at build time — GHCR requires lowercase, but `${{ github.repository }}` preserves GitHub's case

### Trivy Scan (Security Gate)
- Scans the built image for **CRITICAL** severity vulnerabilities
- Pipeline fails with exit code 1 if any are found
- HIGH severity is reported but does not gate — upstream `python:3.12-slim` carries HIGH CVEs (e.g., ncurses) that are not actionable at the application level

### SBOM Generation
- **Syft** generates an SPDX SBOM from the built image
- Uploaded as a GitHub Actions artifact (`sbom.spdx.json`)
- Provides a full software bill of materials for supply chain visibility

### Push (main only)
- Only runs on pushes to `main` (not on PRs)
- Authenticates to GHCR using the built-in `GITHUB_TOKEN`
- Pushes both the SHA-tagged and `latest` images

### Deploy
- Not directly in the pipeline — handled by ArgoCD
- ArgoCD watches the `k8s/` directory for manifest changes
- Auto-sync with pruning and self-heal enabled
- Push to main → CI builds and pushes image → update image tag in K8s manifests → ArgoCD syncs

## Required Permissions

The `build-scan-push` job requires these GitHub token permissions:
- `contents: read` — checkout the repository
- `packages: write` — push images to GHCR
- `security-events: write` — for Trivy scan results

## GitHub Actions vs GitLab CI

Both configurations implement the same pipeline stages:
- **GitHub Actions** (`.github/workflows/ci.yml`) — primary, fully functional, runs on every push
- **GitLab CI** (`.gitlab-ci.yml`) — reference config for portability. Uses Docker-in-Docker for builds, Trivy container image for scanning, and GitLab Container Registry for pushes

Key differences in the GitLab config:
- Uses `docker save`/`docker load` with artifacts to pass the image between stages
- Trivy runs as a separate container (`aquasec/trivy:latest`) scanning a tarball
- SBOM generation is a parallel job in the scan stage
