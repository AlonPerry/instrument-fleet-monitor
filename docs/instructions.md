# 📝 Interview Cheat Sheet & Quick Commands

## 🚀 Terminal Commands
* **Start Stack:** `docker compose up -d`
* **Check Status:** `docker compose ps`
* **Check Logs:** `docker compose logs -f`
* **Stop Stack:** `docker compose down`

## 🌐 Local Web Endpoints
* **Grafana Dashboard:** http://localhost:3000
* **Prometheus UI:** http://localhost:9090
* **Python Simulator Metrics:** http://localhost:8000/metrics
* **Simulate Vacuum Leak (Toggle):** http://localhost:8000/toggle-leak

## 💡 Demo Flow Steps for Interview
1. Show GitHub repo architecture.
2. Spin up stack: `docker compose up -d`.
3. Open Grafana at `localhost:3000`.
4. Trigger leak at `localhost:8000/toggle-leak` and show HT Interlock shutdown on Grafana graph.