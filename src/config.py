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
ANOMALY_THRESHOLD = 90.0 # Fail-Safe Hard Limit for alarms
ANOMALY_CHANCE = 0.1     # 10% probability of injecting an anomaly

WINDOW_SIZE = 50         # Sliding Window size for statistical learning
MIN_DATA_REQUIRED = 20   # Warm-up phase: Samples needed before detection starts