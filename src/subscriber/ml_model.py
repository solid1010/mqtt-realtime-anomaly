import json
import sys
import os
import numpy as np
from collections import deque

# Path setup to import config module from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
import paho.mqtt.client as mqtt

# --- ML Model Memory (Sliding Window) ---
# We use the WINDOW_SIZE from config.py
data_window = deque(maxlen=config.WINDOW_SIZE)

def detect_anomaly_zscore(new_value):
    """
    Z-Score Method: Statistical Anomaly Detection.
    """
    # Skip calculation if data is insufficient (Based on Config)
    if len(data_window) < config.MIN_DATA_REQUIRED:
        return False, 0.0

    mean = np.mean(data_window) 
    std = np.std(data_window)   

    if std == 0: return False, 0.0 

    z_score = (new_value - mean) / std

    # Threshold > 3 means anomaly
    if abs(z_score) > 3:
        return True, z_score
    return False, z_score

def on_connect(client, userdata, flags, rc):
    # Backward compatibility check
    if isinstance(rc, int):
        if rc == 0:
            print(f"[INFO] Connected to Broker at {config.BROKER_ADDRESS}")
            client.subscribe(config.TOPIC_NAME)
            print(f"[SYSTEM] Initializing Calibration Phase (Need {config.MIN_DATA_REQUIRED} samples)...")
    else:
        print(f"[INFO] Connected to Broker.")
        client.subscribe(config.TOPIC_NAME)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # Check for LWT
        if "status" in payload and payload["status"] == "OFFLINE":
            print(f"\n[WARNING] ⚠️ SENSOR LOST CONNECTION! (LWT Triggered)\n")
            return

        temp = payload.get("temperature")
        
        # --- Logic Flow: Calibration vs. Detection ---
        
        # 1. Warm-up Phase
        if len(data_window) < config.MIN_DATA_REQUIRED:
            data_window.append(temp)
            remaining = config.MIN_DATA_REQUIRED - len(data_window)
            print(f"[CALIBRATION] Reading: {temp}°C - {remaining} samples left...")
            if len(data_window) == config.MIN_DATA_REQUIRED:
                print(f"\n[SYSTEM] ✅ Calibration Complete! Hybrid Model ACTIVE.\n")
            return

        # 2. Hybrid Detection Phase (Statistical + Rule Based)
        is_stat_anomaly, score = detect_anomaly_zscore(temp)
        
        # Fail-Safe Rule using config
        is_hard_limit = temp >= config.ANOMALY_THRESHOLD

        if is_stat_anomaly or is_hard_limit:
            reason = "Hard Limit" if is_hard_limit else f"Z-Score {score:.2f}"
            print(f"[DATA] Received {temp}°C")
            print(f"[ALERT] 🚨 ANOMALY DETECTED! ({reason})")
            
            # Prevent Model Poisoning: Do NOT add anomalies to memory
        else:
            print(f"[DATA] Received {temp}°C (Normal)")
            data_window.append(temp)

    except Exception as e:
        print(f"[ERROR] Logic error: {e}")

# Configure Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "AI_Model_Subscriber")
client.on_connect = on_connect
client.on_message = on_message

# Connect
client.connect(config.BROKER_ADDRESS, config.BROKER_PORT, config.KEEP_ALIVE_INTERVAL)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[SYSTEM] AI Model stopped.")