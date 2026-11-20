#!/bin/bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

: "${DB_PASSWORD:?DB_PASSWORD must be set in .env or the environment}"
: "${GRAFANA_ADMIN_PASSWORD:?GRAFANA_ADMIN_PASSWORD must be set in .env or the environment}"

echo "==> 0. Checking Minikube Status..."
if ! minikube status &>/dev/null; then
  echo "Minikube is not running. Starting Minikube..."
  minikube start
fi

echo "==> 1. Building Docker Image (No Cache)..."
docker build --no-cache -t fleet-simulator:1.0.0 ./simulator

echo "==> 2. Loading Simulator Image into Minikube..."
minikube image load fleet-simulator:1.0.0

echo "==> 3. Ensuring Kubernetes Namespaces Exist..."
for namespace in fleet-system monitoring; do
  kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
done

echo "==> 4. Creating or Updating Kubernetes Secrets..."
kubectl create secret generic postgres-secret \
  --namespace fleet-system \
  --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic grafana-secret \
  --namespace monitoring \
  --from-literal=GF_SECURITY_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> 5. Applying Kubernetes Manifests (fleet-system & k8s)..."
kubectl apply -f k8s/

echo "==> 6. Applying Monitoring Stack (monitoring)..."
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml

echo "==> 7. Waiting for Deployments to Become Ready..."
kubectl rollout status deployment/postgres-deployment --namespace fleet-system --timeout=180s
kubectl rollout status deployment/simulator-deployment --namespace fleet-system --timeout=180s
kubectl rollout status deployment/prometheus-deployment --namespace monitoring --timeout=180s
kubectl rollout status deployment/grafana-deployment --namespace monitoring --timeout=180s

echo "==> Deployment completed successfully!"