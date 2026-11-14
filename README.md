# Fleet Equipment Telemetry & Monitoring System

An end-to-end DevOps observability and simulation platform designed to monitor critical telemetry metrics of electron microscopy fleets (Turbo Pump RPM, High Voltage, and Gun Vacuum Pressure) with automated safety interlock behavior, alerting, and CI/CD pipelines.

![Grafana Dashboard Interlock Status](docs/images/Screenshot%20From%202026-11-14%2017-47-49.png)

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

Quick Start (Single-Command Deployment)
Ensure Minikube and kubectl are installed, then run the single-command deployment script to spin up the entire stack:
chmod +x deploy.sh
./deploy.sh
Accessing Services & Fault Simulation
After deployment, you can access the observability dashboards and test automated safety interlocks using port-forwarding:

Grafana Dashboard:
kubectl port-forward svc/grafana 3000:3000 -n monitoring
(Then open http://localhost:3000 in your browser)
Prometheus UI:
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring
- **Trigger Simulated Vacuum Leak (Fault Injection):**
  To test the automated high-voltage interlock trip, forward the simulator port and trigger a leak on an active instrument (e.g., `tem-01`):
  ```bash
  kubectl port-forward svc/simulator-service 8000:8000 -n monitoring
Then in another terminal, use the command for the desired instrument:
# For TEM instrument
curl -X POST http://localhost:8000/toggle-leak/tem-01

# For SEM instrument
curl -X POST http://localhost:8000/toggle-leak/sem-01

# For FIB instrument
curl -X POST http://localhost:8000/toggle-leak/fib-01
