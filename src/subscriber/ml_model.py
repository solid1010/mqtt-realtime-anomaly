import json
import sys
import os

# Path setup to import config module from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"[INFO] Connected to Broker at {config.BROKER_ADDRESS}")
    # Subscribe immediately upon connection
    client.subscribe(config.TOPIC_NAME)
    print(f"[SYSTEM] Listening for topics: {config.TOPIC_NAME}")
    print("[WAITING] Waiting for sensor data...")

def on_message(client, userdata, msg):
    try:
        # Decode incoming data (JSON Decoding)
        payload = json.loads(msg.payload.decode())
        
        # Check for LWT message (If sensor died)
        if "status" in payload and payload["status"] == "OFFLINE":
            print(f"\n[WARNING] ⚠️ SENSOR LOST CONNECTION! (LWT Triggered)\n")
            return

        temp = payload.get("temperature")
        
        # --- Simple Anomaly Detection (Inference) ---
        if temp >= config.ANOMALY_THRESHOLD:
            print(f"[DATA] Received {temp}°C from SENSOR-01")
            print(f"[ALERT] 🚨 CRITICAL ANOMALY DETECTED: {temp}°C!")
        else:
            # Log normal data (Keep output clean for non-anomalies)
            print(f"[DATA] Received {temp}°C (Normal)")

    except Exception as e:
        print(f"[ERROR] Could not parse message: {e}")

# Configure Client
client = mqtt.Client("AI_Model_Subscriber")
client.on_connect = on_connect
client.on_message = on_message

# Connect and Start Listening
client.connect(config.BROKER_ADDRESS, config.BROKER_PORT, config.KEEP_ALIVE_INTERVAL)

# Infinite loop (Listens until Ctrl+C is pressed)
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[SYSTEM] AI Model stopped.")
    client.disconnect()