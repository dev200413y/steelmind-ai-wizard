"""
SteelMind AI Wizard — ML Model Training Script
================================================
Trains Isolation Forest (anomaly detection) and XGBoost (RUL prediction)
on synthetic sensor data.

Run:
    python src/models/train_models.py

Outputs:
    src/models/isolation_forest.pkl
    src/models/rul_model.pkl
    src/models/scaler.pkl
"""

import os
import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Paths
MODELS_DIR = Path(__file__).parent
DATA_DIR = Path(__file__).parent.parent / "data"
SENSOR_DATA_PATH = DATA_DIR / "sensor_data.csv"

SENSOR_COLUMNS = [
    "sensor_temperature",
    "sensor_vibration",
    "sensor_pressure",
    "sensor_rpm",
    "sensor_current",
]


def load_sensor_data() -> pd.DataFrame:
    """
    Load sensor data CSV. If it doesn't exist, generate it first.

    Returns:
        DataFrame with sensor readings
    """
    if not SENSOR_DATA_PATH.exists():
        logger.warning(f"⚠️  Sensor data not found at {SENSOR_DATA_PATH}")
        logger.info("📊 Generating synthetic sensor data first...")

        # Add parent path so we can import the generator
        sys.path.insert(0, str(DATA_DIR.parent.parent))
        from src.data.generate_sensor_data import generate_sensor_data
        generate_sensor_data()

    df = pd.read_csv(SENSOR_DATA_PATH)
    logger.info(f"📊 Loaded {len(df)} sensor readings from {SENSOR_DATA_PATH}")
    return df


def train_isolation_forest(df: pd.DataFrame, scaler: StandardScaler) -> IsolationForest:
    """
    Train Isolation Forest for anomaly detection on sensor data.

    Uses only normal data (anomaly_flag == 0) for training so the model
    learns what 'normal' looks like and flags deviations.

    Args:
        df: Full sensor DataFrame
        scaler: Fitted StandardScaler

    Returns:
        Trained IsolationForest model
    """
    logger.info("🌲 Training Isolation Forest...")

    # Use only normal readings for training
    normal_data = df[df["anomaly_flag"] == 0][SENSOR_COLUMNS].dropna()
    logger.info(f"   Normal samples for training: {len(normal_data)}")

    # Scale features
    normal_scaled = scaler.transform(normal_data)

    # Train Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=0.05,     # Expect ~5% anomalies
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    iso_forest.fit(normal_scaled)

    # Evaluate on full dataset
    all_scaled = scaler.transform(df[SENSOR_COLUMNS].dropna())
    predictions = iso_forest.predict(all_scaled)
    anomalies_detected = (predictions == -1).sum()
    logger.info(f"   Anomalies detected in full dataset: {anomalies_detected}/{len(predictions)}")

    return iso_forest


def train_rul_model(df: pd.DataFrame, scaler: StandardScaler):
    """
    Train XGBoost Regressor for Remaining Useful Life (RUL) prediction.

    Uses sensor readings as features and rul_days as target.
    Falls back to GradientBoosting if XGBoost is not installed.

    Args:
        df: Full sensor DataFrame with rul_days column
        scaler: Fitted StandardScaler

    Returns:
        Trained regression model (XGBoost or GradientBoosting)
    """
    logger.info("📈 Training RUL Prediction Model...")

    # Filter rows that have valid RUL values
    rul_data = df[df["rul_days"].notna() & (df["rul_days"] >= 0)].copy()

    if len(rul_data) < 100:
        logger.warning("⚠️  Not enough RUL data, creating synthetic RUL labels...")
        # Create synthetic RUL: higher sensor values = lower RUL
        df_copy = df.copy()
        df_copy["rul_days"] = df_copy["rul_days"].fillna(180)  # Default 180 days
        rul_data = df_copy[SENSOR_COLUMNS + ["rul_days"]].dropna()

    X = rul_data[SENSOR_COLUMNS].values
    y = rul_data["rul_days"].values

    # Scale features
    X_scaled = scaler.transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    # Try XGBoost first, fallback to sklearn
    try:
        from xgboost import XGBRegressor

        rul_model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1,
        )
        model_name = "XGBoost"
    except ImportError:
        logger.warning("⚠️  XGBoost not installed, using GradientBoosting")
        from sklearn.ensemble import GradientBoostingRegressor

        rul_model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
        )
        model_name = "GradientBoosting"

    rul_model.fit(X_train, y_train)

    # Evaluate
    train_score = rul_model.score(X_train, y_train)
    test_score = rul_model.score(X_test, y_test)
    logger.info(f"   {model_name} R² — Train: {train_score:.4f} | Test: {test_score:.4f}")

    return rul_model


def train_all_models():
    """
    Train all ML models and save to disk.

    Saves:
        - isolation_forest.pkl — Anomaly detection model
        - rul_model.pkl — RUL prediction model
        - scaler.pkl — Feature scaler (shared by both models)
    """
    logger.info("=" * 60)
    logger.info("🏭 SteelMind AI Wizard — Model Training")
    logger.info("=" * 60)

    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_sensor_data()

    # Fit scaler on ALL sensor data
    logger.info("📏 Fitting StandardScaler...")
    scaler = StandardScaler()
    scaler.fit(df[SENSOR_COLUMNS].dropna())

    # Save scaler
    scaler_path = MODELS_DIR / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    logger.info(f"✅ Scaler saved: {scaler_path}")

    # Train Isolation Forest
    iso_forest = train_isolation_forest(df, scaler)
    iso_path = MODELS_DIR / "isolation_forest.pkl"
    joblib.dump(iso_forest, iso_path)
    logger.info(f"✅ Isolation Forest saved: {iso_path}")

    # Train RUL Model
    rul_model = train_rul_model(df, scaler)
    rul_path = MODELS_DIR / "rul_model.pkl"
    joblib.dump(rul_model, rul_path)
    logger.info(f"✅ RUL Model saved: {rul_path}")

    logger.info("=" * 60)
    logger.info("🎉 All models trained and saved successfully!")
    logger.info(f"   📁 Models directory: {MODELS_DIR}")
    logger.info(f"   📄 isolation_forest.pkl: {iso_path.stat().st_size / 1024:.1f} KB")
    logger.info(f"   📄 rul_model.pkl: {rul_path.stat().st_size / 1024:.1f} KB")
    logger.info(f"   📄 scaler.pkl: {scaler_path.stat().st_size / 1024:.1f} KB")
    logger.info("=" * 60)


if __name__ == "__main__":
    train_all_models()
