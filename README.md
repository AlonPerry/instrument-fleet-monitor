# Fleet Equipment Telemetry & Monitoring System

An end-to-end DevOps observability and simulation platform designed to monitor critical telemetry metrics of electron microscopy fleets (Turbo Pump RPM, High Voltage, and Gun Vacuum Pressure) with automated safety interlock behavior, alerting, and CI/CD pipelines.

## Architecture & Tech Stack

- **Telemetry Simulator (Python / Flask):** Exposes Prometheus metrics (`/metrics`) and provides an interactive fault-injection API (`/toggle-leak/<instrument_id>`) to simulate vacuum leaks and automatic high-voltage interlock trips.
- **Database (PostgreSQL):** Stores persistent telemetry and state records.
- **Monitoring & Alerting (Prometheus & Grafana):** Scrapes metrics every 5 seconds, evaluates critical alert rules (`VacuumLeakDetected` when `vacuum_pascal >= 1.0e-4`), and visualizes real-time fleet health via pre-provisioned dashboards.
- **Orchestration & Packaging (Kubernetes & Helm):** Deployed on Minikube and packaged as a professional Helm chart (`helm/fleet-monitor/`), unified under a single-command deployment script (`deploy.sh`).
- **CI/CD (GitHub Actions):** Automated validation of Python dependencies and Kubernetes YAML schemas (`kubeconform`) on every push to `main`.

## Project Structure

```text
├── .github/workflows/ci.yml   # Automated CI pipeline
├── helm/fleet-monitor/        # Packaged Helm Chart (Chart.yaml, values.yaml, templates/)
├── k8s/                       # Kubernetes manifests (Namespaces, Deployments, Services, ConfigMaps, Alerts)
├── monitoring/                # Grafana dashboard JSON definitions
├── simulator/                 # Python Flask telemetry simulator & Dockerfile
├── deploy.sh                  # Single-point-of-entry deployment script
└── INSTRUCTIONS.md            # Operational runbook & fault simulation guide
