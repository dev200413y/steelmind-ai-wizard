"""
SteelMind AI Wizard — Anomaly Agent
====================================
Processes uploaded sensor CSV data to detect statistical anomalies, predict
Remaining Useful Life (RUL), and trigger real-time alerts.
"""

import logging
import pandas as pd
import numpy as np
import joblib

from src.schemas import SteelMindState

logger = logging.getLogger(__name__)

ISOLATION_FOREST_PATH = "src/models/isolation_forest.pkl"
RUL_MODEL_PATH = "src/models/rul_model.pkl"
SCALER_PATH = "src/models/scaler.pkl"

SENSOR_COLUMNS = [
    "sensor_temperature",
    "sensor_vibration",
    "sensor_pressure",
    "sensor_rpm",
    "sensor_current"
]

def classify_severity(anomaly_score: float, rul_days: int) -> str:
    """Classify anomaly severity based on score and predicted RUL."""
    if rul_days < 3 or anomaly_score > 0.85:
        return "CRITICAL"
    elif rul_days < 7 or anomaly_score > 0.70:
        return "HIGH"
    elif rul_days < 14 or anomaly_score > 0.60:
        return "MEDIUM"
    else:
        return "LOW"

def find_anomalous_sensor(df: pd.DataFrame, columns: list) -> str:
    """Find the sensor whose latest reading deviates most from its historical mean."""
    deviations = {}
    for col in columns:
        mean_val = df[col].mean()
        std_val = df[col].std()
        latest_val = df[col].iloc[-1]
        
        # Avoid division by zero
        if std_val == 0:
            deviations[col] = 0
        else:
            deviations[col] = abs(latest_val - mean_val) / std_val
            
    return max(deviations, key=deviations.get)

def get_normal_range(sensor_name: str) -> str:
    """Return hardcoded normal ranges for display purposes."""
    ranges = {
        "sensor_temperature": "1150-1300°C",
        "sensor_vibration": "0.5-2.0 mm/s",
        "sensor_pressure": "150-200 bar",
        "sensor_rpm": "1400-1600 RPM",
        "sensor_current": "80-100 A"
    }
    return ranges.get(sensor_name, "Unknown")

def generate_sensor_recommendations(anomaly_score: float, rul_days: int) -> list:
    """Generate recommendations based on severity."""
    recs = []
    if rul_days < 7:
        recs.append("Immediate inspection required: RUL critically low.")
        recs.append("Prepare spare parts for imminent replacement.")
    elif anomaly_score > 0.6:
        recs.append("Monitor sensor readings closely for next 24 hours.")
        recs.append("Schedule proactive maintenance during next available window.")
    else:
        recs.append("Sensor readings within acceptable limits.")
    return recs

def run_anomaly(state: SteelMindState) -> SteelMindState:
    """
    Detect anomalies in sensor CSV using Isolation Forest.
    Predict RUL using XGBoost regression model.
    """
    logger.info("📊 Running Anomaly Agent")
    
    if not state.get("csv_path"):
        logger.info("   No CSV path provided. Skipping anomaly detection.")
        return state
        
    try:
        # Load sensor data
        df = pd.read_csv(state["csv_path"])
        
        if len(df) < 10:
            logger.warning("   CSV has fewer than 10 rows. Need more data for accurate prediction.")
            return state

        # Load models
        iso_forest = joblib.load(ISOLATION_FOREST_PATH)
        rul_model = joblib.load(RUL_MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        
        # Get latest readings
        latest = df[SENSOR_COLUMNS].tail(10)
        latest_scaled = scaler.transform(latest)
        
        # Anomaly detection (Isolation Forest outputs negative for anomaly)
        anomaly_scores = iso_forest.decision_function(latest_scaled)
        # Convert to a positive score 0-1 for simplicity (rough scaling)
        # Decision function is usually <0 for anomalies, >0 for normal.
        # Let's map it: highly negative -> score ~1.0. Positive -> score ~0.0
        avg_score = float(np.mean(anomaly_scores))
        anomaly_score_normalized = max(0.0, min(1.0, 0.5 - (avg_score * 2.0)))
        
        # RUL prediction
        rul_pred = rul_model.predict(latest_scaled[-1:])
        rul_days = int(max(0, rul_pred[0]))
        
        severity = classify_severity(anomaly_score_normalized, rul_days)
        anomalous_sensor = find_anomalous_sensor(df, SENSOR_COLUMNS)
        alert_triggered = rul_days < 7
        
        state["anomaly_result"] = {
            "anomaly_detected": anomaly_score_normalized > 0.6,
            "anomaly_score": round(anomaly_score_normalized, 3),
            "severity": severity,
            "anomalous_sensor": anomalous_sensor,
            "current_value": float(df[anomalous_sensor].iloc[-1]),
            "normal_range": get_normal_range(anomalous_sensor),
            "rul_days": rul_days,
            "rul_confidence": 0.85,
            "alert_triggered": alert_triggered,
            "trend_data": df.tail(30).to_dict("records"),
            "recommendations": generate_sensor_recommendations(anomaly_score_normalized, rul_days)
        }
        
        if alert_triggered:
            state["force_critical"] = True
            logger.warning("   🚨 CRITICAL ALERT TRIGGERED: RUL < 7 days")
            
        logger.info(f"   Anomaly analysis complete. Score: {anomaly_score_normalized:.2f}, RUL: {rul_days} days")
        
    except Exception as e:
        logger.error(f"❌ Anomaly Agent failed: {str(e)}")
        
    return state
