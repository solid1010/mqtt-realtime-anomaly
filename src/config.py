# src/config.py

# MQTT Broker Settings
BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
KEEP_ALIVE_INTERVAL = 60

# Topic Settings
TOPIC_NAME = "factory/machine1/temperature"

# Simulation Settings
TRANSMISSION_RATE = 1.0  # Data transmission rate (seconds)
NORMAL_TEMP_MEAN = 25.0  # Mean normal temperature
ANOMALY_THRESHOLD = 90.0 # Threshold for triggering alarms
ANOMALY_CHANCE = 0.1     # 10% probability of injecting an anomaly