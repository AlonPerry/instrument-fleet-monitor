#!/bin/bash
set -e

echo "==> 0. Checking Minikube Status..."
if ! minikube status &>/dev/null; then
    echo "Minikube is not running. Starting Minikube..."
    minikube start
fi

echo "==> 1. Building Docker Image (No Cache)..."
docker build --no-cache -t fleet-simulator:latest ./simulator

echo "==> 2. Loading Simulator Image into Minikube..."
minikube image load fleet-simulator:latest

echo "==> 3. Applying Kubernetes Manifests (fleet-system)..."
kubectl apply -f k8s/

echo "==> 4. Ensuring Monitoring Namespace Exists..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "==> 5. Applying Monitoring Stack (monitoring)..."
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml

echo "==> Deployment completed successfully!"
