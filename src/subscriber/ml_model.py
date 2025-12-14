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
# The model will NOT make predictions for the first 20 readings.
MIN_DATA_REQUIRED = 20 

def detect_anomaly_zscore(new_value):
    """
    Z-Score Method: Statistical Anomaly Detection.
    """
    # Skip calculation if data is insufficient
    if len(data_window) < MIN_DATA_REQUIRED:
        return False, 0.0

    mean = np.mean(data_window) # Calculate the average
    std = np.std(data_window)   # Calculate standard deviation

    if std == 0: return False, 0.0 # Prevent division by zero

    # Calculate Z-Score
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
        
        # 1. If insufficient data, operate in 'Calibration' mode only
        if len(data_window) < MIN_DATA_REQUIRED:
            data_window.append(temp)
            remaining = MIN_DATA_REQUIRED - len(data_window)
            print(f"[CALIBRATION] Reading: {temp}°C - {remaining} samples left to start detection...")
            
            if len(data_window) == MIN_DATA_REQUIRED:
                print(f"\n[SYSTEM] ✅ Calibration Complete! Model is now ACTIVE.\n")
            return

        # 2. If sufficient data, switch to 'Detection' mode
        is_anomaly, score = detect_anomaly_zscore(temp)

        if is_anomaly:
            print(f"[DATA] Received {temp}°C")
            print(f"[ALERT] 🚨 STATISTICAL ANOMALY DETECTED! (Z-Score: {score:.2f})")
        else:
            # System is stable; no need to print 'Learning' continuously
            print(f"[DATA] Received {temp}°C (Normal)")
        
        # Continue adding data to memory (Continuous Learning)
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