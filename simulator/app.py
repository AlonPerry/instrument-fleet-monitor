import os
import time
import threading
import logging
import psycopg2
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_USER = os.getenv("DB_USER", "fleet_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "fleet_db")

def get_db_connection():
    """Establishes a PostgreSQL connection using the required credentials."""
    if not DB_PASSWORD:
        raise RuntimeError("DB_PASSWORD environment variable must be set")

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=2
        )
        return conn
    except Exception:
        return None

def init_db():
    """Initializes the database table, retrying while PostgreSQL starts."""
    max_attempts = 10
    retry_delay = 2
    for attempt in range(1, max_attempts + 1):
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS fleet_telemetry (
                            id SERIAL PRIMARY KEY,
                            instrument_name VARCHAR(50),
                            instrument_type VARCHAR(20),
                            vacuum_pascal FLOAT,
                            turbo_rpm FLOAT,
                            high_voltage FLOAT,
                            leak_active BOOLEAN,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                conn.commit()
                return
            except psycopg2.Error as exc:
                logger.warning(
                    "Database initialization attempt %s/%s failed: %s",
                    attempt,
                    max_attempts,
                    exc,
                )
            finally:
                conn.close()
        else:
            logger.warning(
                "Could not connect to PostgreSQL for database initialization "
                "(attempt %s/%s)",
                attempt,
                max_attempts,
            )

        if attempt < max_attempts:
            time.sleep(retry_delay)

    logger.error(
        "Could not initialize the database table after %s attempts; "
        "continuing without database initialization",
        max_attempts,
    )

# Initialize DB on startup safely
init_db()

# Prometheus Metrics with Labels
gun_vacuum = Gauge('instrument_gun_vacuum_pascals', 'Gun Vacuum Pressure in Pascals', ['instrument_name', 'instrument_type'])
turbo_rpm = Gauge('instrument_turbo_pump_rpm', 'Turbo Pump Speed in RPM', ['instrument_name', 'instrument_type'])
high_voltage = Gauge('instrument_high_voltage_kv', 'High Voltage in kV', ['instrument_name', 'instrument_type'])

# Simulator Initial State
instruments_state = {
    "tem-01": {"type": "TEM", "leak_active": False, "vacuum_pascal": 3.0e-9, "turbo_rpm": 90000.0, "hv_kv": 200.0},
    "sem-01": {"type": "SEM", "leak_active": False, "vacuum_pascal": 1.0e-6, "turbo_rpm": 60000.0, "hv_kv": 30.0},
    "fib-01": {"type": "FIB", "leak_active": False, "vacuum_pascal": 5.0e-6, "turbo_rpm": 60000.0, "hv_kv": 30.0}
}

def update_simulation():
    """Background loop ensuring instant and stable telemetry response during leaks."""
    while True:
        conn = get_db_connection()
        cursor = conn.cursor() if conn else None

        for name, state in instruments_state.items():
            baseline = 3.0e-9 if state["type"] == "TEM" else 1.0e-6
            
            if state["leak_active"]:
                # Instant jump to bad vacuum (hard crash to 1.0e-4)
                state["vacuum_pascal"] = 1.0e-4
                state["turbo_rpm"] = 10000.0
                # Hard interlock trip: HV drops to 0 instantly and stays there
                state["hv_kv"] = 0.0
            else:
                # Recovery when leak is closed
                state["vacuum_pascal"] = baseline
                state["turbo_rpm"] = 90000.0 if state["type"] == "TEM" else 60000.0
                state["hv_kv"] = 200.0 if state["type"] == "TEM" else 30.0

            gun_vacuum.labels(instrument_name=name, instrument_type=state["type"]).set(state["vacuum_pascal"])
            turbo_rpm.labels(instrument_name=name, instrument_type=state["type"]).set(state["turbo_rpm"])
            high_voltage.labels(instrument_name=name, instrument_type=state["type"]).set(state["hv_kv"])

            if cursor:
                try:
                    cursor.execute('''
                        INSERT INTO fleet_telemetry (instrument_name, instrument_type, vacuum_pascal, turbo_rpm, high_voltage, leak_active)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (name, state["type"], state["vacuum_pascal"], state["turbo_rpm"], state["hv_kv"], state["leak_active"]))
                except Exception:
                    pass

        if conn:
            try:
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                pass

        time.sleep(1)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/toggle-leak/<string:inst_name>', methods=['GET', 'POST'])
def toggle_leak(inst_name):
    if inst_name in instruments_state:
        instruments_state[inst_name]["leak_active"] = not instruments_state[inst_name]["leak_active"]
        status = "LEAK ACTIVE 🚨" if instruments_state[inst_name]["leak_active"] else "SYSTEM NORMAL ✅"
        return f"<h1>Instrument: {inst_name} ({instruments_state[inst_name]['type']})</h1><h2>Status: {status}</h2><p>Current Pressure: {instruments_state[inst_name]['vacuum_pascal']:.2e} Pa</p>"
    return f"<h1>Instrument {inst_name} not found!</h1>", 404

if __name__ == '__main__':
    t = threading.Thread(target=update_simulation, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=8000)