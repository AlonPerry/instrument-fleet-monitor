# 🔬 Instrument Fleet Monitor & Telemetry Simulator

A full-stack DevOps monitoring platform built to simulate real-time microscope vacuum metrics, safety interlocks (vacuum degradation triggering High Voltage/HT shutdown), and telemetry alerts.

---

## 🛠️ Key Features

* **Telemetry Data Exporter:** Python service simulating real-time vacuum sensor metrics (Pirani/Penning log scale metrics).
* **Metrics Ingestion:** Prometheus custom exporter scraping live system state metrics.
* **Visualization & Dashboards:** Grafana dashboards configured with logarithmic scales and dynamic alert thresholds.
* **Containerized Deployment:** Orchestrated using Docker & Docker Compose for single-command environment deployment.

---

## 🏗️ Architecture & Tech Stack

* **Language:** Python 3
* **Containerization:** Docker, Docker Compose
* **Observability:** Prometheus, Grafana
* **Version Control:** Git, GitHub Actions

---

## 🚀 Quick Start & Operations

### 1. Spin up the environment
```bash
docker compose up -d