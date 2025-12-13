import time
import json
import random
import sys
import os

# Path setup to import config module from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[SYSTEM] Connected to Broker at {config.BROKER_ADDRESS}")
    else:
        print(f"[ERROR] Failed to connect, return code {rc}")

# Create Client
client = mqtt.Client("Sensor-01")

# --- LWT (Last Will and Testament) Configuration ---
# The Broker will publish this message automatically if the sensor disconnects unexpectedly.
client.will_set(config.TOPIC_NAME, payload=json.dumps({"status": "OFFLINE", "error": "Sensor Lost"}), qos=1, retain=True)

# Connect
client.on_connect = on_connect
client.connect(config.BROKER_ADDRESS, config.BROKER_PORT, config.KEEP_ALIVE_INTERVAL)

client.loop_start()

try:
    while True:
        # 1. Generate Data (Simulation)
        # 10% chance of anomaly (90.0 - 105.0), otherwise normal value (20.0 - 30.0)
        if random.random() < config.ANOMALY_CHANCE:
            temperature = round(random.uniform(90.0, 105.0), 2)
            status = "CRITICAL"
        else:
            temperature = round(random.uniform(20.0, 30.0), 2)
            status = "NORMAL"

        payload = {
            "sensor_id": "sensor-01",
            "temperature": temperature,
            "timestamp": time.time()
        }

        # 2. Publish Data (QoS 1: Guaranteed Delivery)
        client.publish(config.TOPIC_NAME, json.dumps(payload), qos=1)
        
        # Terminal Output (Log)
        print(f"[SENSOR-01] Sending: {temperature}°C ({status})")
        
        time.sleep(config.TRANSMISSION_RATE)

except KeyboardInterrupt:
    print("\n[SYSTEM] Sensor stopped manually.")
    client.loop_stop()
    client.disconnect()