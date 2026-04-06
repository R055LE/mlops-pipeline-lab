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
| FastAPI App | Sentiment analysis REST API | `app/` |
| Dockerfile | Multi-stage hardened container build | `docker/` |
| CI Pipeline | Lint, test, build, scan, push | `.github/workflows/` |
| K8s Manifests | Deployment, Service, Ingress, HPA | `k8s/` |
| ArgoCD | GitOps continuous delivery | `argocd/` |
| Prometheus | Metrics collection and alerting | `monitoring/prometheus/` |
| Grafana | Metrics visualization dashboards | `monitoring/grafana/` |
| Loki | Log aggregation | `monitoring/loki/` |
| Kyverno | Policy enforcement (security gates) | `policies/` |

## Key Design Decisions

- **CPU-only inference**: The model (`distilbert-base-uncased-finetuned-sst-2-english`) runs on CPU. The infrastructure patterns are the focus, not GPU optimization.
- **GitOps over kubectl apply**: ArgoCD watches the repo and auto-syncs, eliminating manual deployment steps and ensuring the cluster matches git state.
- **Security gates at every layer**: Trivy in CI, Kyverno in-cluster, non-root containers, read-only filesystem, dropped capabilities.
- **HPA for scaling**: Horizontal Pod Autoscaler scales based on CPU utilization (70% threshold, 2-5 replicas).
