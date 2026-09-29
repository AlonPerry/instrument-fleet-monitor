import time
import threading
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# 1. הגדרת המדדים של Prometheus
gun_vacuum = Gauge('instrument_gun_vacuum_pascals', 'Gun Vacuum Pressure in Pascals')
turbo_rpm = Gauge('instrument_turbo_pump_rpm', 'Turbo Pump Speed in RPM')
high_voltage = Gauge('instrument_high_voltage_kv', 'High Voltage in kV')

# 2. משתני המצב של הסימולטור
sim_state = {
    "leak_active": False,
    "vacuum_pascal": 3.0e-9,  # וואקום בסיס תקין: 3 nPa (3e-9 Pa)
    "turbo_rpm": 90000.0,     # סל"ד משאבת טורבו מלא: 90,000 RPM
    "hv_kv": 200.0            # מתח עבודה תקין: 200 kV
}

def update_simulation():
    """לולאה הרצה ברקע ומעדכנת את ערכי הפיזיקה מדי שנייה"""
    while True:
        if sim_state["leak_active"]:
            # תרחיש דליפה: הלחץ עולה בקצב מהיר מעבר ל-10^-8 Pa
            sim_state["vacuum_pascal"] = min(1.0e-4, sim_state["vacuum_pascal"] * 1.25)
            
            # הגנת ואקום: אם הוואקום חוצה 5e-8 Pa, ה-HV מנותק אוטומטית (0 kV)
            if sim_state["vacuum_pascal"] > 5.0e-8:
                sim_state["hv_kv"] = 0.0
        else:
            # תרחיש תקין: המשאבות שואבות חזרה לוואקום בסיס של 3e-9 Pa
            sim_state["vacuum_pascal"] = max(3.0e-9, sim_state["vacuum_pascal"] * 0.75)
            sim_state["turbo_rpm"] = 90000.0
            
            # החזרת המתח הגבוה ברגע שהלחץ יורד חזרה מתחת ל-1e-8 Pa
            if sim_state["vacuum_pascal"] <= 1.0e-8:
                sim_state["hv_kv"] = 200.0

        # עדכון המדדים ב-Prometheus Client
        gun_vacuum.set(sim_state["vacuum_pascal"])
        turbo_rpm.set(sim_state["turbo_rpm"])
        high_voltage.set(sim_state["hv_kv"])
        
        time.sleep(1)

@app.route('/metrics')
def metrics():
    """הנקודה שדרכה Prometheus דוגם את הנתונים"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/toggle-leak', methods=['GET', 'POST'])
def toggle_leak():
    """מתג שליטה להדגמת דליפה בלחיצת כפתור בדפדפן"""
    sim_state["leak_active"] = not sim_state["leak_active"]
    status = "LEAK ACTIVE 🚨" if sim_state["leak_active"] else "SYSTEM NORMAL ✅"
    return f"<h1>Vacuum Status: {status}</h1><p>Current Pressure: {sim_state['vacuum_pascal']:.2e} Pa</p>"

if __name__ == '__main__':
    # הרצת לולאת הסימולציה ב-Thread נפרד כדי שלא תחסום את שרת ה-Flask
    t = threading.Thread(target=update_simulation, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=8000)