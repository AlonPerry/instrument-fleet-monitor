import time
import threading
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# 1. Prometheus Metrics Definition
gun_vacuum = Gauge('instrument_gun_vacuum_pascals', 'Gun Vacuum Pressure in Pascals')
turbo_rpm = Gauge('instrument_turbo_pump_rpm', 'Turbo Pump Speed in RPM')
high_voltage = Gauge('instrument_high_voltage_kv', 'High Voltage in kV')

# 2. Simulator Initial State
sim_state = {
    "leak_active": False,
    "vacuum_pascal": 3.0e-9,  # Base normal ultra-high vacuum: 3 nPa (3e-9 Pa)
    "turbo_rpm": 90000.0,     # Full turbo pump speed in RPM
    "hv_kv": 200.0            # Normal HT operating voltage: 200 kV
}

def update_simulation():
    """Background loop updating physical state and applying safety interlocks."""
    while True:
        if sim_state["leak_active"]:
            # Leak scenario: Pressure rises exponentially past 1e-8 Pa
            sim_state["vacuum_pascal"] = min(1.0e-4, sim_state["vacuum_pascal"] * 1.25)
            
            # Safety Interlock: Automatically trip High Voltage (0 kV) if vacuum exceeds threshold
            if sim_state["vacuum_pascal"] > 5.0e-8:
                sim_state["hv_kv"] = 0.0
        else:
            # Normal recovery scenario: Vacuum returns to baseline 3 nPa
            sim_state["vacuum_pascal"] = max(3.0e-9, sim_state["vacuum_pascal"] * 0.75)
            sim_state["turbo_rpm"] = 90000.0
            
            # Auto-restore High Voltage once vacuum recovers below 1e-8 Pa
            if sim_state["vacuum_pascal"] <= 1.0e-8:
                sim_state["hv_kv"] = 200.0

        # Update Prometheus metrics gauge values
        gun_vacuum.set(sim_state["vacuum_pascal"])
        turbo_rpm.set(sim_state["turbo_rpm"])
        high_voltage.set(sim_state["hv_kv"])

        time.sleep(1)

@app.route('/metrics')
def metrics():
    """Prometheus metrics scraping endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/toggle-leak', methods=['GET', 'POST'])
def toggle_leak():
    """Control endpoint to simulate a vacuum leak directly from browser."""
    sim_state["leak_active"] = not sim_state["leak_active"]
    status = "LEAK ACTIVE 🚨" if sim_state["leak_active"] else "SYSTEM NORMAL ✅"
    return f"<h1>Vacuum Status: {status}</h1><p>Current Pressure: {sim_state['vacuum_pascal']:.2e} Pa</p>"

if __name__ == '__main__':
    # Start simulation loop in a background thread
    t = threading.Thread(target=update_simulation, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=8000)
