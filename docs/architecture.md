# Architecture

## System Design

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Developer   │────▶│  GitHub      │────▶│  GitHub Actions │
│  (git push)  │     │  Repository  │     │  CI Pipeline    │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                           ┌───────────────────────┼──────────────┐
                           │                       │              │
                           ▼                       ▼              ▼
                    ┌──────────┐          ┌──────────┐    ┌───────────┐
                    │  Trivy   │          │  Syft    │    │   GHCR    │
                    │  Scan    │          │  SBOM    │    │   Push    │
                    └──────────┘          └──────────┘    └─────┬─────┘
                                                                │
                    ┌───────────────────────────────────────────┘
                    ▼
             ┌─────────────┐     ┌──────────────────────────────────┐
             │   ArgoCD    │────▶│        K3s Cluster               │
             │   GitOps    │     │  ┌────────────────────────────┐  │
             └─────────────┘     │  │   ml-serving namespace     │  │
                                 │  │  ┌──────────────────────┐  │  │
                                 │  │  │  sentiment-api pods  │  │  │
                                 │  │  │  (HPA: 2-5 replicas) │  │  │
                                 │  │  └──────────┬───────────┘  │  │
                                 │  └─────────────┼──────────────┘  │
                                 │                │                  │
                                 │  ┌─────────────▼──────────────┐  │
                                 │  │   monitoring namespace     │  │
                                 │  │  Prometheus ◀─── scrape    │  │
                                 │  │  Grafana (dashboards)      │  │
                                 │  │  Loki (logs)               │  │
                                 │  └────────────────────────────┘  │
                                 │                                   │
                                 │  ┌────────────────────────────┐  │
                                 │  │   Kyverno Policies         │  │
                                 │  │   - require scan           │  │
                                 │  │   - require SBOM           │  │
                                 │  │   - require non-root       │  │
                                 │  │   - require resource limits│  │
                                 │  └────────────────────────────┘  │
                                 └──────────────────────────────────┘
```

## Components

| Component | Purpose | Location |
|-----------|---------|----------|
| FastAPI App | Sentiment analysis REST API with Prometheus instrumentation | `app/` |
| Dockerfile | Multi-stage hardened build with model baked in | `docker/` |
| CI Pipeline | Lint, test, build, scan, SBOM, push | `.github/workflows/` |
| GitLab CI | Reference pipeline config for portability | `.gitlab-ci.yml` |
| K8s Manifests | Deployment, Service, Ingress, HPA | `k8s/` |
| ArgoCD | GitOps continuous delivery | `argocd/` |
| Prometheus | Metrics collection from app pods | `monitoring/prometheus/` |
| Grafana | Dashboards for model serving metrics | `monitoring/grafana/` |
| Loki | Log aggregation | `monitoring/loki/` |
| Kyverno | In-cluster policy enforcement | `policies/` |

## Key Design Decisions

### Model baked into the image
The HuggingFace model is downloaded during `docker build` and cached in the image. At runtime, `TRANSFORMERS_OFFLINE=1` prevents any network calls to HuggingFace. This ensures:
- Containers work in air-gapped or network-restricted environments
- No runtime dependency on an external service
- Reproducible inference — the model version is locked at build time

### CPU-only inference
The model (`distilbert-base-uncased-finetuned-sst-2-english`) runs on CPU. The infrastructure patterns are the focus, not GPU optimization. This keeps the project runnable on any machine without CUDA or GPU hardware.

**Trade-off:** PyTorch bundles CUDA libraries even for CPU-only usage, resulting in a ~3.2GB image. A future optimization could use CPU-only wheels from `https://download.pytorch.org/whl/cpu` to significantly reduce image size.

### Security at every layer
- **Build time:** Trivy scans for CRITICAL CVEs (gate), Syft generates SBOM
- **Container:** Non-root (UID 999), read-only root filesystem, all capabilities dropped, no privilege escalation
- **Cluster:** Kyverno policies enforce scanned images, SBOM annotations, non-root, and resource limits
- **K8s:** seccomp RuntimeDefault profile, emptyDir volumes for `/tmp` and `/app/.cache` (required by read-only root filesystem)

### Numeric UID in K8s security context
K8s `runAsNonRoot` cannot verify non-root status when the image specifies a named user (e.g., `USER appuser`). The deployment sets `runAsUser: 999` explicitly — the numeric UID assigned to `appuser` during image build — to satisfy this check.

### Trivy gate on CRITICAL only
The `python:3.12-slim` base image carries HIGH-severity CVEs (e.g., ncurses `CVE-2025-69720`) that are upstream and not patchable at the application level. Gating on CRITICAL avoids false-positive pipeline failures while still catching genuinely dangerous vulnerabilities.

### Traefik ingress (K3s default)
K3s ships with Traefik as the default ingress controller, not nginx. The ingress manifest uses `ingressClassName: traefik` accordingly. On clusters with nginx-ingress, this would need to change.

### WSL2 pod egress via host proxy
WSL2 in host networking mode breaks the pod → internet forwarding path. K3s flannel routes pod traffic through cni0 → flannel.1 → eth0, but WSL2's host networking shim doesn't forward the pod CIDR (10.42.0.0/16) to the outside world. A tinyproxy instance on the host bridges this gap — pods reach the host at 10.42.0.1:8888, and the host forwards to the internet. This is a WSL2-specific workaround; on a standard Linux host or cloud cluster, pod egress works natively.

### HPA scaling strategy
Horizontal Pod Autoscaler scales from 2 to 5 replicas based on CPU utilization (70% threshold). The floor of 2 ensures availability during rolling updates. CPU is the right scaling signal for CPU-bound inference workloads.

## Metrics Exposed

The FastAPI app instruments these Prometheus metrics:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `request_latency_seconds` | Histogram | method, endpoint, status_code | Request duration with percentile buckets |
| `requests_total` | Counter | method, endpoint, status_code | Total request count |
| `predictions_total` | Counter | label | Predictions by sentiment label (POSITIVE/NEGATIVE) |
| `prediction_errors_total` | Counter | — | Total prediction failures |

The Grafana dashboard (`monitoring/grafana/dashboards/model-serving.json`) visualizes these as:
- Request rate over time
- Latency percentiles (p50/p95/p99)
- Prediction distribution pie chart
- Error rate
- Throughput stat panel

## Observability Stack

| Component | Helm Chart | Purpose |
|-----------|-----------|---------|
| Prometheus | `prometheus-community/prometheus` | Scrapes `/metrics` from sentiment-api pods via pod annotations |
| Grafana | `grafana/grafana` | Dashboards for model serving metrics, datasources for Prometheus and Loki |
| Loki | `grafana/loki` (SingleBinary mode) | Log aggregation from model serving pods |

**Disabled components:**
- `prometheus-node-exporter` — incompatible with WSL2 mount propagation
- `alertmanager` — not needed for this demo
- `prometheus-pushgateway` — app pushes metrics via scrape, not push

Prometheus discovers sentiment-api pods via Kubernetes SD with pod annotation relabeling:
- `prometheus.io/scrape: "true"` — opt-in to scraping
- `prometheus.io/port: "8000"` — target port
- `prometheus.io/path: /metrics` — metrics endpoint path

## Policy Enforcement

Kyverno runs as an admission controller, intercepting pod creation requests and validating them against cluster policies before they reach the API server.

All four policies target the `ml-serving` namespace and use `validationFailureAction: Enforce`:

| Policy | Rule | Validates |
|--------|------|-----------|
| `require-vulnerability-scan` | `check-image-registry` | Image matches `ghcr.io/r055le/*` |
| `require-sbom-annotation` | `check-sbom-annotation` | Pod has `sbom/generated: "true"` annotation |
| `require-non-root` | `check-run-as-non-root` | Pod `runAsNonRoot: true`, containers `allowPrivilegeEscalation: false` |
| `require-resource-limits` | `check-resource-limits` | Containers have CPU and memory requests and limits |

### How policies connect to CI

The policies create a closed loop with the CI pipeline:
1. **CI** scans the image with Trivy and generates an SBOM with Syft
2. **CI** pushes the scanned image to `ghcr.io/r055le/`
3. **K8s deployment** sets `sbom/generated: "true"` annotation, `runAsNonRoot`, resource limits
4. **Kyverno** validates all of the above at admission time — unscanned images, missing SBOMs, root containers, or unbounded resources are rejected
