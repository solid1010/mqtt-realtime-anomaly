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
# We keep the last 50 data points to learn the "Normal" behavior dynamically.
window_size = 50
data_window = deque(maxlen=window_size)

# --- Warm-up Configuration ---
# Minimum data points required before starting detection.
MIN_DATA_REQUIRED = 20 

def detect_anomaly_zscore(new_value):
    """
    Z-Score Method: Statistical Anomaly Detection.
    """
    # Skip calculation if data is insufficient
    if len(data_window) < MIN_DATA_REQUIRED:
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
            print(f"[SYSTEM] Initializing Calibration Phase (Need {MIN_DATA_REQUIRED} samples)...")
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
        if len(data_window) < MIN_DATA_REQUIRED:
            data_window.append(temp)
            remaining = MIN_DATA_REQUIRED - len(data_window)
            print(f"[CALIBRATION] Reading: {temp}°C - {remaining} samples left...")
            if len(data_window) == MIN_DATA_REQUIRED:
                print(f"\n[SYSTEM] ✅ Calibration Complete! Hybrid Model ACTIVE.\n")
            return

        # 2. Hybrid Detection Phase (Statistical + Rule Based)
        is_stat_anomaly, score = detect_anomaly_zscore(temp)
        
        # Fail-Safe Rule: Even if statistics say it's fine, > 90.0 is ALWAYS critical.
        is_hard_limit = temp >= config.ANOMALY_THRESHOLD

        if is_stat_anomaly or is_hard_limit:
            reason = "Hard Limit" if is_hard_limit else f"Z-Score {score:.2f}"
            print(f"[DATA] Received {temp}°C")
            print(f"[ALERT] 🚨 ANOMALY DETECTED! ({reason})")
            
            # CRITICAL FIX: Do NOT add anomalies to the learning window!
            # If we add them, the model 'learns' that 90C is normal (Model Poisoning).
            # We keep the memory pure with only normal data.
        else:
            print(f"[DATA] Received {temp}°C (Normal)")
            # Only learn from normal data
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