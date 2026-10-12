# Learning Log

## 2026-09-21

### What I Did
- Created GitHub repository `instrument-fleet-monitor` and project directory layout.
- Configured Python virtual environment (`.venv`) and installed `prometheus_client`.
- Developed a TEM vacuum simulator (`simulator/app.py`) reporting in Pascals.
- Exposed metrics on HTTP port 8000 and verified output via browser.

### Issues & Solutions
- **Git identity missing:** Configured user email and name using `git config --global`.
- **Module import error:** Fixed typo from `prometheus_clint` to `prometheus_client`.
- **Python syntax errors:** Corrected function syntax (`__name__`, `random.uniform`) and line separation.

### What I Learned
- Prometheus telemetry concept: Exposing raw metrics over HTTP endpoints for scraping.
- Using Prometheus `Gauge` to track continuous physical values (vacuum level).
- Terminal navigation, virtual environments, and GitHub authentication workflow.