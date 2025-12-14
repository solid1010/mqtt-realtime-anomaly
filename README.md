
# 📡 MQTT Real-Time Anomaly Detection


> **"HTTP is for documents, MQTT is for data."**
>
> This project implements a production-grade **Software-in-the-Loop** MLOps pipeline. It replaces high-latency HTTP polling architectures with **event-driven MQTT streaming** to detect anomalies in industrial IoT sensors in real-time.

---

## 📑 Table of Contents
- [📍 Overview](#-overview)
- [🏗️ Architecture](#-architecture)
- [📂 Project Structure](#-project-structure)
- [⚡ Key Features & Engineering](#-key-features--engineering)
- [⚙️ Installation & Setup](#-installation--setup)
- [🚀 Usage / Simulation](#-usage--simulation)
- [🛠️ Configuration](#-configuration)
- [🔮 Future Roadmap](#-future-roadmap)

---

## 📍 Overview

In traditional Edge-to-Cloud systems, **HTTP polling** creates unnecessary network overhead and latency. This project demonstrates an **Event-Driven Architecture** where:

1.  **Sensors** push data asynchronously (Fire-and-forget or Guaranteed Delivery).
2.  **The Broker** handles high-throughput routing.
3.  **The AI Model** subscribes to streams and detects anomalies (e.g., overheating) instantly.

**Why this architecture?**
* **Latency:** Reduced from seconds (HTTP) to milliseconds (MQTT).
* **Bandwidth:** Packet overhead reduced from ~500 Bytes (HTTP) to **2 Bytes** (MQTT).
* **Resilience:** Handles network drops without data loss using **QoS 1** and **Persistent Sessions**.

---

## 🏗️ Architecture

The system follows a **Pub/Sub** pattern, completely decoupling the Edge devices from the Inference Engine.

```mermaid
graph LR
    subgraph Edge Layer [Edge Layer: Factory]
        P[Publisher / Virtual Sensor]
    end

    subgraph Transport Layer [Transport Layer: Network]
        B((Mosquitto Broker))
    end

    subgraph App Layer [App Layer: AI Core]
        S[Subscriber / ML Model]
        A[Alert Logic]
        D[Dashboard / Log]
    end

    P -- "Topic: factory/+/temp" --> B
    B -- "Push Stream (QoS 1)" --> S
    S -- "Inference" --> A
    A -- "Anomaly Detected!" --> D

    style P fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style S fill:#bfb,stroke:#333,stroke-width:2px
````

1.  **Publisher (Sensor Simulation):** Generates synthetic time-series data and randomly injects "fault" values.
2.  **Broker (Mosquitto):** The central nervous system. Routes messages and manages session states.
3.  **Subscriber (Anomaly Detector):** A Python service that listens to the topic, runs threshold-based analysis, and triggers alerts.

-----

## 📂 Project Structure

The project is organized to support scalability and containerization.

```bash
mqtt-realtime-anomaly/
├── .gitignore             # Python cache & env exclusions
├── README.md              # Project documentation
├── requirements.txt       # Dependencies (paho-mqtt, numpy)
├── docker-compose.yml     # (Optional) Container orchestration
├── src/
│   ├── __init__.py
│   ├── config.py          # Global configs (Brokers, Ports, Topics)
│   ├── publisher/
│   │   └── sensor_sim.py  # Virtual Sensor Logic (Edge)
│   └── subscriber/
│       └── ml_model.py    # Inference Logic (Server)
└── docs/
    └── mqtt_presentation.pdf   # Slide Deck
```

-----

## ⚡ Key Features & Engineering

This project implements specific **IoT Design Patterns** to ensure reliability in MLOps pipelines:

| Feature | Implementation | Engineering Value |
| :--- | :--- | :--- |
| **Guaranteed Delivery** | `QoS=1` (At Least Once) | Critical sensor data is acknowledged (`PUBACK`). Zero data loss even on unstable 3G/4G networks. |
| **Fault Detection** | **LWT (Last Will)** | If a sensor crashes (ungraceful disconnect), the Broker auto-publishes an "OFFLINE" alert to the model. |
| **State Persistence** | **Retained Messages** | Solves "Cold Start". New subscribers immediately get the *last known* status of a machine. |
| **Scalability** | **Wildcards (`+`)** | One model can monitor thousands of sensors via `factory/+/temperature` topic dynamic subscription. |
| **Efficiency** | **Binary Protocol** | Uses minimal overhead (2 Byte header) compared to verbose HTTP text headers. |

-----

## ⚙️ Installation & Setup

Follow these steps to run the project from scratch.

### Prerequisites

  * Python 3.8+
  * [Docker](https://www.docker.com/) (Recommended for Broker) OR Local Mosquitto installation.

### 1\. Clone the Repository

```bash
git clone [https://github.com/YOUR_USERNAME/mqtt-iot-mlops.git](https://github.com/YOUR_USERNAME/mqtt-iot-mlops.git)
cd mqtt-iot-mlops
```

### 2\. Environment Setup

Create a virtual environment and install dependencies.

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate
# Activate it (Mac/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3\. Start the MQTT Broker

You need an MQTT Broker running. The easiest way is using Docker:

```bash
docker run -it -p 1883:1883 eclipse-mosquitto
```

*(Alternatively, if you have Mosquitto installed locally, just run `mosquitto` in a new terminal).*

-----

## 🚀 Usage / Simulation

To see the pipeline in action, you need **two separate terminal windows**.

#### Terminal 1: Start the AI Service (Subscriber)

Start the listener first. It will wait for incoming data.

```bash
# Make sure your venv is activated
python src/subscriber/ml_model.py
```

**Expected Output:**

```text
[INFO] Connected to Broker at localhost:1883
[SYSTEM] Listening for topics: factory/+/temperature
[WAITING] Waiting for sensor data...
```

#### Terminal 2: Start the Edge Simulation (Publisher)

Start the virtual sensor. It will begin streaming data.

```bash
# Make sure your venv is activated
python src/publisher/sensor_sim.py
```

**Expected Output:**

```text
[SENSOR-01] Sending: 24.5°C
[SENSOR-01] Sending: 25.1°C
[SENSOR-01] Sending: 98.2°C  <-- ANOMALY INJECTED!
```

#### 👀 Result (Watch Terminal 1)

The subscriber captures the anomaly instantly:

```text
[DATA] Received 25.1°C from SENSOR-01
[DATA] Received 98.2°C from SENSOR-01
[ALERT] 🚨 CRITICAL ANOMALY DETECTED: 98.2°C!
```

-----

## 🛠️ Configuration

You can adjust system parameters in `src/config.py` (or directly in scripts):

  * **`BROKER_ADDRESS`**: Default `localhost`
  * **`TOPIC`**: Default `factory/machine1/temperature`
  * **`ANOMALY_THRESHOLD`**: Default `90.0`
  * **`TRANSMISSION_RATE`**: Default `1.0` second

-----

## 🔮 Future Roadmap

  - [ ] **Security:** Implement TLS/SSL (Port 8883) & Client Authentication.
  - [ ] **Integration:** Bridge MQTT topics to **Apache Kafka** for long-term storage.
  - [ ] **Visualization:** Connect real-time stream to a **Grafana** dashboard.
  - [ ] **Deployment:** Dockerize the Python scripts for Kubernetes deployment.

-----

