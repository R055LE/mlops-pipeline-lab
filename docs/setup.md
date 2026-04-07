# Local Setup Guide

## Prerequisites

- Python 3.12+ with `python3-venv` package
- Docker
- K3s (`curl -sfL https://get.k3s.io | sh -`)
- kubectl
- Helm 3
- ArgoCD CLI (optional)

## 1. Run the App Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload
```

The first `/predict` request will download the model from HuggingFace (~260MB) and cache it locally. Subsequent requests load from cache.

Test it:

```bash
curl http://localhost:8000/health
# → {"status":"healthy"}

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing!"}'
# → {"label":"POSITIVE","score":0.9999}

curl http://localhost:8000/metrics
# → Prometheus text format with request_latency_seconds, predictions_total, etc.
```

## 2. Build and Run with Docker

```bash
docker build -f docker/Dockerfile -t sentiment-api:local .
docker run -p 8000:8000 sentiment-api:local
```

The Docker build downloads and bakes the model into the image at build time. The container runs fully offline (`TRANSFORMERS_OFFLINE=1`) — it never contacts HuggingFace at runtime.

**Note:** The build context can be large if `.venv/` exists locally. The `.dockerignore` excludes it, but ensure you're using it.

**Note:** The image is ~3.2GB because PyTorch bundles CUDA libraries even for CPU-only usage. This is a known trade-off. A future optimization could use `torch` CPU-only wheels to reduce the image size significantly.

## 3. Deploy to K3s

### Set up kubeconfig

After installing K3s, copy the kubeconfig so kubectl works without sudo:

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
```

### Deploy the app

```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/
```

Wait for pods to be ready (image pull takes a while on first deploy due to the ~3.2GB image):

```bash
kubectl get pods -n ml-serving -w
```

### Verify from inside the cluster

```bash
kubectl run curl-test --rm -i --restart=Never \
  --image=curlimages/curl -n ml-serving -- \
  curl -s http://sentiment-api/health
# → {"status":"healthy"}

kubectl run curl-test --rm -i --restart=Never \
  --image=curlimages/curl -n ml-serving -- \
  curl -s -X POST http://sentiment-api/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Kubernetes is working"}'
# → {"label":"POSITIVE","score":0.9994}
```

## 4. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f argocd/application.yml
```

Once installed, ArgoCD watches the `k8s/` directory and auto-syncs changes on push to `main`.

## 5. Deploy Monitoring Stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

kubectl create namespace monitoring

helm install prometheus prometheus-community/prometheus \
  -n monitoring -f monitoring/prometheus/values.yml

helm install grafana grafana/grafana \
  -n monitoring -f monitoring/grafana/values.yml

helm install loki grafana/loki \
  -n monitoring -f monitoring/loki/values.yml
```

Default Grafana credentials: `admin` / `admin`.

The Grafana dashboard (`monitoring/grafana/dashboards/model-serving.json`) shows:
- Request rate to `/predict`
- Request latency percentiles (p50/p95/p99)
- Predictions by label (POSITIVE/NEGATIVE pie chart)
- Error rate
- Throughput (predictions/sec)

## 6. Install Kyverno Policies

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
kubectl apply -f policies/
```

Policies enforce in the `ml-serving` namespace:
- Images must come from `ghcr.io/r055le/`
- Pods must have `sbom/generated: "true"` annotation
- `runAsNonRoot: true` and `allowPrivilegeEscalation: false` required
- CPU and memory resource limits/requests required

## DNS (for Ingress)

Add to `/etc/hosts`:

```
127.0.0.1 sentiment.local
```

## Troubleshooting

### `CreateContainerConfigError: image has non-numeric user`

K8s `runAsNonRoot` can't verify non-root status with named users like `appuser`. The deployment uses `runAsUser: 999` (the numeric UID of `appuser` in the image) to resolve this.

### Pods crash-loop on `/predict` but `/health` works

The model may be trying to download from HuggingFace at runtime. Ensure the image was built with the model download step in the Dockerfile, and `TRANSFORMERS_OFFLINE=1` is set.

### Trivy scan fails in CI

The pipeline gates on CRITICAL severity only. If you see failures, there's a genuine critical CVE in the image — check the Trivy output in the GitHub Actions logs for details.
