# Local Setup Guide

## Prerequisites

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

Test it:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing!"}'
curl http://localhost:8000/metrics
```

## 2. Build and Run with Docker

```bash
docker build -f docker/Dockerfile -t sentiment-api:local .
docker run -p 8000:8000 sentiment-api:local
```

## 3. Deploy to K3s

```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/
```

## 4. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f argocd/application.yml
```

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

## 6. Install Kyverno Policies

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
kubectl apply -f policies/
```

## DNS (for Ingress)

Add to `/etc/hosts`:

```
127.0.0.1 sentiment.local
```
