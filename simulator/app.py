import time
import random
from prometheus_client import start_http_server, Gauge

# הגדרת המטריקה
vacuum_gauge = Gauge('instrument_gun_vacuum_pascals', 'Gun Vacuum Pressure in Pascals', ['instrument_id'])

start_time = time.time()

def generate_vacuum_reading():
    elapsed = time.time() - start_time
    
    # סימולציית דליפת ואקום: לאחר 45 שניות של עבודה תקינה, הלחץ מתחיל לעלות בחדות
    if elapsed > 45:
        # עליית לחץ הדרגתית (אובדן ואקום) מ-2.5e-8 לכיוון 1e-5 Pa
        leak_factor = (elapsed - 45) * 5.0e-8
        base_pressure = 2.5e-8 + leak_factor
        noise = random.uniform(-0.1e-8, 0.1e-8)
        return max(1.0e-8, base_pressure + noise)
    else:
        # מצב תקין סביב 2.5e-8 Pa
        base_pressure = 2.5e-8
        noise = random.uniform(-0.3e-8, 0.3e-8)
        return max(1.0e-8, base_pressure + noise)

if __name__ == '__main__':
    start_http_server(8000)
    print("Simulator with leak scenario running on port 8000...")
    while True:
        val = generate_vacuum_reading()
        vacuum_gauge.labels(instrument_id='TEM1').set(val)
        time.sleep(2)