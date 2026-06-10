# Anomaly Detection Agent

## Role
Processes uploaded sensor CSV data to detect statistical anomalies, predict Remaining Useful Life (RUL), and trigger real-time alerts for critical equipment degradation. Uses pre-trained Isolation Forest + XGBoost models.

## Read First
- `references/schemas.md` — AnomalyResult schema
- `references/data_guide.md` — Sensor CSV column definitions

---

## Input
```python
state["csv_path"]       # Path to uploaded sensor CSV
state["equipment_id"]   # Equipment to analyze
state["equipment_type"] # Equipment category
```

## Output — Updates State
```python
state["anomaly_result"] = {
    "anomaly_detected": bool,
    "anomaly_score": float,       # 0.0 to 1.0 (higher = more anomalous)
    "severity": str,              # LOW|MEDIUM|HIGH|CRITICAL
    "anomalous_sensor": str,      # Which sensor is abnormal
    "current_value": float,       # Current sensor reading
    "normal_range": str,          # Expected range e.g. "0.5-2.0 mm/s"
    "rul_days": int,              # Remaining Useful Life in days
    "rul_confidence": float,      # Confidence in RUL estimate
    "alert_triggered": bool,      # True if RUL < 7 days
    "trend_data": list[dict],     # Last 30 readings for graph
    "recommendations": list[str]  # Immediate sensor-based actions
}
```

---

## Models Used
```python
# Pre-trained models — loaded from disk
ISOLATION_FOREST_PATH = "src/models/isolation_forest.pkl"
RUL_MODEL_PATH = "src/models/rul_model.pkl"

# Training data: Kaggle AI4I 2020 + Ball Bearing Run-to-Failure
# Train script: src/models/train_models.py
```

---

## Implementation
```python
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler

SENSOR_COLUMNS = [
    "sensor_temperature",
    "sensor_vibration", 
    "sensor_pressure",
    "sensor_rpm",
    "sensor_current"
]

def run_anomaly(state: SteelMindState) -> SteelMindState:
    """
    Detect anomalies in sensor CSV using Isolation Forest.
    Predict RUL using XGBoost regression model.
    Trigger CRITICAL alert if RUL < 7 days.
    """
    if not state.get("csv_path"):
        return state
    
    # Load sensor data
    df = pd.read_csv(state["csv_path"])
    
    # Load pre-trained models
    iso_forest = joblib.load(ISOLATION_FOREST_PATH)
    rul_model = joblib.load(RUL_MODEL_PATH)
    scaler = joblib.load("src/models/scaler.pkl")
    
    # Get latest readings
    latest = df[SENSOR_COLUMNS].tail(10)
    latest_scaled = scaler.transform(latest)
    
    # Anomaly detection
    anomaly_scores = iso_forest.decision_function(latest_scaled)
    anomaly_score = float(np.mean(anomaly_scores) * -1)  # Higher = more anomalous
    
    # RUL prediction
    rul_days = int(rul_model.predict(latest_scaled[-1:])[0])
    
    # Determine severity
    severity = classify_severity(anomaly_score, rul_days)
    
    # Find most anomalous sensor
    anomalous_sensor = find_anomalous_sensor(df, SENSOR_COLUMNS)
    
    state["anomaly_result"] = {
        "anomaly_detected": anomaly_score > 0.6,
        "anomaly_score": round(anomaly_score, 3),
        "severity": severity,
        "anomalous_sensor": anomalous_sensor,
        "current_value": float(df[anomalous_sensor].iloc[-1]),
        "normal_range": get_normal_range(anomalous_sensor),
        "rul_days": max(0, rul_days),
        "rul_confidence": 0.85,
        "alert_triggered": rul_days < 7,
        "trend_data": df.tail(30).to_dict("records"),
        "recommendations": generate_sensor_recommendations(anomaly_score, rul_days)
    }
    return state
```

---

## Severity Classification
```python
def classify_severity(anomaly_score: float, rul_days: int) -> str:
    if rul_days < 3 or anomaly_score > 0.85:
        return "CRITICAL"
    elif rul_days < 7 or anomaly_score > 0.70:
        return "HIGH"
    elif rul_days < 14 or anomaly_score > 0.60:
        return "MEDIUM"
    else:
        return "LOW"
```

---

## Sensor Thresholds Reference
| Sensor | Normal | Warning | Critical |
|---|---|---|---|
| Temperature | 1150–1300°C | >1400°C | >1550°C |
| Vibration | 0.5–2.0 mm/s | >3.5 mm/s | >6.0 mm/s |
| Pressure | 150–200 bar | >220 bar | >250 bar |
| Motor Current | 80–100 A | >115 A | >130 A |

---

## Alert Logic
```python
# If CRITICAL alert triggered:
# → Risk Scorer automatically assigns CRITICAL
# → Report Generator adds URGENT header
# → Frontend shows red pulsing badge
if state["anomaly_result"]["alert_triggered"]:
    state["force_critical"] = True  # Signal to Risk Scorer
```

---

## Model Training (run once)
```python
# src/models/train_models.py
# Dataset: Kaggle AI4I 2020 + Ball Bearing Run-to-Failure
# Run: python src/models/train_models.py
# Saves: isolation_forest.pkl, rul_model.pkl, scaler.pkl
```
