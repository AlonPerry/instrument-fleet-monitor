# Instrument Fleet Monitor

A telemetry and observability demo for microscope equipment. The simulator
generates vacuum, turbo-pump, and high-voltage readings, stores telemetry in
PostgreSQL, and exposes metrics and a leak-toggle endpoint.

## Architecture

- **Simulator:** Flask serves `/metrics` and `/toggle-leak/<instrument>`. Its
  Prometheus vacuum metric is `instrument_gun_vacuum_pascals`.
- **PostgreSQL:** Stores telemetry; Kubernetes and Helm deployments use
  persistent storage.
- **Prometheus:** Scrapes the simulator and evaluates the vacuum-leak alert.
- **Grafana:** Reads Prometheus and displays the fleet dashboard.
- **Deployment:** Docker Compose for local use, Kubernetes on Minikube via
  `deploy.sh`, or the chart in `helm/fleet-monitor/`.

![Grafana dashboard](<./docs/images/Screenshot From 2026-11-14 17-47-49.png>)

## Project Structure

```text
├── .env.example
├── .github/workflows/ci.yml
├── demo.sh
├── deploy.sh
├── docker-compose.yaml
├── docs/
│   ├── images/
│   └── learning-log.md
├── helm/fleet-monitor/
│   ├── templates/
│   └── values.yaml
├── k8s/
├── monitoring/
├── simulator/
│   └── tests/
└── README.md
```

## Credentials

Copy `.env.example` to `.env` and set private local values for
`DB_PASSWORD` and `GRAFANA_ADMIN_PASSWORD`. `.env` is ignored by Git; do not
commit real credentials. `deploy.sh` reads these values and creates the
Kubernetes Secrets before applying manifests. Direct Helm installs require the
configured Secrets to exist in the release namespace.

## Local Setup with Docker Compose

If `.env` does not already exist, copy the example and restrict its permissions.
Set both required values before starting the stack:

```bash
[ -f .env ] || cp .env.example .env
chmod 600 .env
# Set DB_PASSWORD and GRAFANA_ADMIN_PASSWORD in .env.
docker compose up --build -d
```

Stop the local stack with `docker compose down`.

## Minikube Quick Start

Ensure Minikube, `kubectl`, and Docker are installed. Create and configure `.env`
if needed, then deploy:

```bash
[ -f .env ] || cp .env.example .env
chmod 600 .env
# Set DB_PASSWORD and GRAFANA_ADMIN_PASSWORD in .env.
./deploy.sh
```

`deploy.sh` creates the namespaces and Secrets, applies the Kubernetes
manifests, and waits for the Deployments to become ready.

## Accessing Services

The helper starts port-forwards for Grafana and the simulator, prints their
URLs and PIDs, and provides `status` and `down` commands:

```bash
./demo.sh up
./demo.sh status
./demo.sh down
```

Open Grafana at `http://localhost:3000`; simulator metrics are at
`http://localhost:8000/metrics`.

For manual port-forwards, run each command in its own terminal:

```bash
kubectl port-forward -n monitoring svc/grafana-service 3000:3000
kubectl port-forward -n monitoring svc/prometheus-service 9090:9090
kubectl port-forward -n fleet-system svc/fleet-simulator-service 8000:8000
```

## Trigger a Simulated Vacuum Leak

With the simulator port-forward active, toggle a leak on `tem-01`:

```bash
curl -s http://localhost:8000/toggle-leak/tem-01
```

The vacuum metric rises, Prometheus evaluates `VacuumLeakDetected`, and Grafana
shows the changing telemetry. Repeat the request to return the instrument to
normal.

## CI

`.github/workflows/ci.yml` checks Python syntax and unit tests, Docker Compose
configuration, Helm lint and rendered manifests, raw Kubernetes manifests with
`kubeconform`, and `deploy.sh` syntax with `bash -n`.
