"""
SteelMind AI Wizard — Synthetic Sensor Data Generator
======================================================
Generates ~50,000 rows of 6-month sensor time-series data for 9 equipment
units across a steel plant.  Includes realistic daily/weekly cycles,
50+ fault scenarios with gradual degradation curves, and sudden-spike
failures.  Output CSV is directly consumed by the Anomaly Agent and
RUL prediction pipeline.

Usage:
    python -m src.data.generate_sensor_data
    python src/data/generate_sensor_data.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

SEED: int = int(os.getenv("STEELMIND_SEED", "42"))
OUTPUT_DIR: str = os.getenv(
    "STEELMIND_DATA_DIR",
    str(Path(__file__).resolve().parent),
)
OUTPUT_FILE: str = "sensor_data.csv"

# Date range — 6 months
START_DATE: str = "2025-12-01"
END_DATE: str = "2026-05-31"

# Target row-count (approximate — varies by equipment weighting)
TARGET_ROWS: int = 50_000

# ─── Equipment registry ────────────────────────────────────────
EQUIPMENT: dict[str, dict[str, Any]] = {
    "BF-001": {
        "type": "Blast Furnace",
        "prefix": "BF",
        "weight": 1.5,  # more readings from critical equipment
        "ranges": {
            "sensor_temperature": (1200, 1350),
            "sensor_vibration": (0.6, 1.8),
            "sensor_pressure": (160, 200),
            "sensor_rpm": (1420, 1580),
            "sensor_current": (85, 100),
        },
    },
    "BF-002": {
        "type": "Blast Furnace",
        "prefix": "BF",
        "weight": 1.5,
        "ranges": {
            "sensor_temperature": (1180, 1320),
            "sensor_vibration": (0.5, 1.9),
            "sensor_pressure": (155, 195),
            "sensor_rpm": (1430, 1590),
            "sensor_current": (82, 98),
        },
    },
    "RM-001": {
        "type": "Rolling Mill",
        "prefix": "RM",
        "weight": 1.2,
        "ranges": {
            "sensor_temperature": (350, 500),
            "sensor_vibration": (0.8, 2.5),
            "sensor_pressure": (180, 220),
            "sensor_rpm": (800, 1200),
            "sensor_current": (90, 120),
        },
    },
    "RM-002": {
        "type": "Rolling Mill",
        "prefix": "RM",
        "weight": 1.2,
        "ranges": {
            "sensor_temperature": (340, 490),
            "sensor_vibration": (0.7, 2.4),
            "sensor_pressure": (175, 215),
            "sensor_rpm": (810, 1210),
            "sensor_current": (88, 118),
        },
    },
    "CC-001": {
        "type": "Continuous Caster",
        "prefix": "CC",
        "weight": 1.3,
        "ranges": {
            "sensor_temperature": (1050, 1200),
            "sensor_vibration": (0.4, 1.6),
            "sensor_pressure": (100, 150),
            "sensor_rpm": (300, 600),
            "sensor_current": (70, 95),
        },
    },
    "HS-001": {
        "type": "Hydraulic System",
        "prefix": "HS",
        "weight": 1.0,
        "ranges": {
            "sensor_temperature": (40, 70),
            "sensor_vibration": (0.3, 1.2),
            "sensor_pressure": (200, 280),
            "sensor_rpm": (1400, 1600),
            "sensor_current": (30, 55),
        },
    },
    "EAF-001": {
        "type": "Electric Arc Furnace",
        "prefix": "EAF",
        "weight": 1.4,
        "ranges": {
            "sensor_temperature": (1500, 1700),
            "sensor_vibration": (1.0, 3.0),
            "sensor_pressure": (50, 100),
            "sensor_rpm": (0, 0),  # no rotating parts — always 0
            "sensor_current": (500, 800),
        },
    },
    "CV-001": {
        "type": "Conveyor System",
        "prefix": "CV",
        "weight": 0.8,
        "ranges": {
            "sensor_temperature": (30, 55),
            "sensor_vibration": (0.5, 2.0),
            "sensor_pressure": (0, 0),  # no pressure sensor
            "sensor_rpm": (50, 200),
            "sensor_current": (10, 30),
        },
    },
    "CP-001": {
        "type": "Compressor",
        "prefix": "CP",
        "weight": 0.9,
        "ranges": {
            "sensor_temperature": (60, 95),
            "sensor_vibration": (0.6, 2.2),
            "sensor_pressure": (600, 800),
            "sensor_rpm": (2800, 3200),
            "sensor_current": (40, 70),
        },
    },
}

# Sensor codes used in fault_code generation
SENSOR_CODES: dict[str, str] = {
    "sensor_temperature": "T",
    "sensor_vibration": "V",
    "sensor_pressure": "P",
    "sensor_rpm": "R",
    "sensor_current": "C",
}

SENSORS: list[str] = list(SENSOR_CODES.keys())

# Severity tiers — relative magnitude of deviation from normal
SEVERITY_MAP: dict[str, tuple[float, float]] = {
    "LOW": (0.10, 0.25),
    "MEDIUM": (0.25, 0.50),
    "HIGH": (0.50, 0.80),
    "CRITICAL": (0.80, 1.20),
}


# ═══════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════

def _daily_cycle(hours: np.ndarray) -> np.ndarray:
    """Return a sinusoidal daily-cycle factor in [-1, 1].

    Peak at ~14:00 (hot afternoon), trough at ~04:00 (early morning).
    """
    return np.sin(2 * np.pi * (hours - 4) / 24)


def _weekly_cycle(day_of_week: np.ndarray) -> np.ndarray:
    """Return a weekly-cycle factor in [-1, 1].

    Slightly lower readings on weekends (reduced load) with
    Monday ramp-up.
    """
    return np.cos(2 * np.pi * day_of_week / 7)


def _generate_normal_readings(
    timestamps: pd.DatetimeIndex,
    ranges: dict[str, tuple[float, float]],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate baseline sensor readings with realistic daily/weekly cycles.

    Args:
        timestamps: DatetimeIndex for the rows.
        ranges: Mapping of sensor name → (low, high) normal range.
        rng: NumPy random generator for reproducibility.

    Returns:
        DataFrame with one column per sensor.
    """
    n = len(timestamps)
    hours = timestamps.hour + timestamps.minute / 60.0
    dow = timestamps.dayofweek  # 0=Monday … 6=Sunday

    daily = _daily_cycle(hours.values.astype(float))
    weekly = _weekly_cycle(dow.values.astype(float))

    data: dict[str, np.ndarray] = {}
    for sensor, (lo, hi) in ranges.items():
        if lo == 0 and hi == 0:
            data[sensor] = np.zeros(n)
            continue
        mid = (lo + hi) / 2
        span = (hi - lo) / 2
        # base signal = mid + cyclic modulation (±25% of span)
        base = mid + 0.15 * span * daily + 0.10 * span * weekly
        # add Gaussian noise (σ ≈ 3% of span)
        noise = rng.normal(0, 0.03 * span, size=n)
        data[sensor] = np.clip(base + noise, lo * 0.95, hi * 1.05)

    return pd.DataFrame(data, index=timestamps)


def _pick_fault_sensor(
    ranges: dict[str, tuple[float, float]],
    rng: np.random.Generator,
) -> str:
    """Pick a random sensor that is not constant-zero for fault injection.

    Args:
        ranges: Equipment sensor ranges.
        rng: NumPy random generator.

    Returns:
        Sensor column name.
    """
    candidates = [s for s, (lo, hi) in ranges.items() if not (lo == 0 and hi == 0)]
    return rng.choice(candidates)


def _inject_gradual_fault(
    df: pd.DataFrame,
    start_idx: int,
    duration: int,
    sensor: str,
    severity: str,
    ranges: dict[str, tuple[float, float]],
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, list[int]]:
    """Inject a gradual degradation curve into the DataFrame.

    Values ramp exponentially from normal to abnormal over ``duration``
    readings, then plateau for a short period before "repair" (values
    snap back).

    Args:
        df: The sensor DataFrame to modify in-place.
        start_idx: Row index where degradation begins.
        duration: Number of rows over which degradation occurs.
        sensor: Target sensor column.
        severity: One of LOW/MEDIUM/HIGH/CRITICAL.
        ranges: Equipment sensor ranges.
        rng: NumPy random generator.

    Returns:
        Modified DataFrame and list of affected row indices.
    """
    lo, hi = ranges[sensor]
    span = hi - lo if hi != lo else 1.0
    sev_lo, sev_hi = SEVERITY_MAP[severity]
    deviation = rng.uniform(sev_lo, sev_hi) * span

    end_idx = min(start_idx + duration, len(df))
    fault_indices = list(range(start_idx, end_idx))

    # Exponential ramp: goes from ~0 to 1 over the window
    t = np.linspace(0, 1, len(fault_indices))
    ramp = np.expm1(t * 3) / np.expm1(3)  # normalised exponential ramp

    for i, idx in enumerate(fault_indices):
        current = df.iloc[idx][sensor]
        df.iat[idx, df.columns.get_loc(sensor)] = current + deviation * ramp[i]
        # Also add cross-sensor correlation (vibration rises with temp)
        if sensor == "sensor_temperature" and "sensor_vibration" in df.columns:
            vib_col = df.columns.get_loc("sensor_vibration")
            df.iat[idx, vib_col] += 0.3 * deviation * ramp[i] / span

    return df, fault_indices


def _inject_sudden_spike(
    df: pd.DataFrame,
    idx: int,
    sensor: str,
    ranges: dict[str, tuple[float, float]],
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, list[int]]:
    """Inject a sudden spike failure (1–3 readings).

    Args:
        df: The sensor DataFrame to modify in-place.
        idx: Row index for the spike.
        sensor: Target sensor column.
        ranges: Equipment sensor ranges.
        rng: NumPy random generator.

    Returns:
        Modified DataFrame and list of affected row indices.
    """
    lo, hi = ranges[sensor]
    span = hi - lo if hi != lo else 1.0
    spike_magnitude = rng.uniform(0.8, 1.5) * span

    spike_len = rng.integers(1, 4)
    fault_indices = list(range(idx, min(idx + spike_len, len(df))))

    for fi in fault_indices:
        current = df.iloc[fi][sensor]
        df.iat[fi, df.columns.get_loc(sensor)] = current + spike_magnitude

    return df, fault_indices


def _fault_code(prefix: str, sensor: str, seq: int) -> str:
    """Generate a structured fault code.

    Format: ERR-{equipment_prefix}-{sensor_code}{zero-padded number}
    e.g. ERR-BF-T02

    Args:
        prefix: Equipment prefix (BF, RM, etc.).
        sensor: Sensor column name.
        seq: Sequential fault number (1-based).

    Returns:
        Fault code string.
    """
    code = SENSOR_CODES.get(sensor, "X")
    return f"ERR-{prefix}-{code}{seq:02d}"


def _compute_rul(
    total_rows: int,
    fault_indices: list[int],
    severity: str,
    rng: np.random.Generator,
) -> dict[int, int]:
    """Compute Remaining Useful Life (RUL) for fault indices.

    RUL decreases linearly across the fault window, starting from a
    severity-dependent maximum.

    Args:
        total_rows: Total rows in the equipment's DataFrame.
        fault_indices: Row indices flagged as faulty.
        severity: Fault severity level.
        rng: NumPy random generator.

    Returns:
        Mapping of row index → RUL in days.
    """
    max_rul_map = {"LOW": 90, "MEDIUM": 45, "HIGH": 14, "CRITICAL": 3}
    max_rul = max_rul_map.get(severity, 30) + rng.integers(-3, 4)
    max_rul = max(max_rul, 1)

    rul_values: dict[int, int] = {}
    n = len(fault_indices)
    for i, idx in enumerate(fault_indices):
        rul = max(1, int(max_rul * (1 - i / max(n, 1))))
        rul_values[idx] = rul

    return rul_values


# ═══════════════════════════════════════════════════════════════════
# Main Generator
# ═══════════════════════════════════════════════════════════════════

def generate_sensor_data(
    seed: int = SEED,
    target_rows: int = TARGET_ROWS,
) -> pd.DataFrame:
    """Generate the full synthetic sensor dataset.

    Steps:
        1. Create timestamps for each equipment based on weight.
        2. Generate normal readings with cycles.
        3. Inject 50+ fault scenarios (90% gradual, 10% sudden).
        4. Assign fault_code, severity, rul_days.

    Args:
        seed: Random seed for reproducibility.
        target_rows: Approximate total row count.

    Returns:
        Complete DataFrame ready for CSV export.
    """
    rng = np.random.default_rng(seed)
    all_frames: list[pd.DataFrame] = []

    total_weight = sum(eq["weight"] for eq in EQUIPMENT.values())

    for eq_id, eq_info in EQUIPMENT.items():
        # ── Timestamps ──────────────────────────────────────────
        eq_rows = int(target_rows * eq_info["weight"] / total_weight)
        timestamps = pd.date_range(
            start=START_DATE,
            end=END_DATE,
            periods=eq_rows,
        )

        # ── Normal baseline ─────────────────────────────────────
        df = _generate_normal_readings(timestamps, eq_info["ranges"], rng)
        df.insert(0, "timestamp", timestamps)
        df.insert(1, "equipment_id", eq_id)
        df.insert(2, "equipment_type", eq_info["type"])
        df["anomaly_flag"] = 0
        df["fault_code"] = ""
        df["severity"] = "NORMAL"
        df["rul_days"] = -1  # -1 = healthy / not applicable

        # ── Fault injection ─────────────────────────────────────
        num_faults = rng.integers(6, 10)  # 6–9 faults per equipment
        fault_seq = 0
        used_indices: set[int] = set()

        for _ in range(num_faults):
            fault_seq += 1
            sensor = _pick_fault_sensor(eq_info["ranges"], rng)
            severity = rng.choice(
                ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                p=[0.25, 0.35, 0.25, 0.15],
            )
            is_sudden = rng.random() < 0.10

            # Pick a start index that doesn't overlap existing faults
            max_attempts = 50
            for _ in range(max_attempts):
                start = rng.integers(100, eq_rows - 200)
                if start not in used_indices:
                    break

            if is_sudden:
                df, indices = _inject_sudden_spike(
                    df, start, sensor, eq_info["ranges"], rng,
                )
                severity = "CRITICAL"  # sudden spikes are always critical
            else:
                duration = rng.integers(30, 180)
                df, indices = _inject_gradual_fault(
                    df, start, duration, sensor, severity,
                    eq_info["ranges"], rng,
                )

            used_indices.update(indices)
            code = _fault_code(eq_info["prefix"], sensor, fault_seq)
            rul_map = _compute_rul(eq_rows, indices, severity, rng)

            for idx in indices:
                df.iat[idx, df.columns.get_loc("anomaly_flag")] = 1
                df.iat[idx, df.columns.get_loc("fault_code")] = code
                df.iat[idx, df.columns.get_loc("severity")] = severity

            for idx, rul in rul_map.items():
                df.iat[idx, df.columns.get_loc("rul_days")] = rul

        # Round sensor values for readability
        for sensor in SENSORS:
            df[sensor] = df[sensor].round(2)

        all_frames.append(df.reset_index(drop=True))

    # Combine, sort by time, reset index
    result = pd.concat(all_frames, ignore_index=True)
    result.sort_values("timestamp", inplace=True)
    result.reset_index(drop=True, inplace=True)

    return result


def save_sensor_data(df: pd.DataFrame, output_dir: str = OUTPUT_DIR) -> Path:
    """Save the sensor DataFrame to CSV.

    Args:
        df: Sensor data DataFrame.
        output_dir: Directory to write the CSV into.

    Returns:
        Path to the written CSV file.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    csv_path = out_path / OUTPUT_FILE
    df.to_csv(csv_path, index=False)
    return csv_path


# ═══════════════════════════════════════════════════════════════════
# CLI Entry-Point
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 60)
    print("  SteelMind AI Wizard — Sensor Data Generator")
    print("═" * 60)

    df = generate_sensor_data()
    path = save_sensor_data(df)

    # Summary stats
    total = len(df)
    anomalies = df["anomaly_flag"].sum()
    equipments = df["equipment_id"].nunique()
    faults = df[df["fault_code"] != ""]["fault_code"].nunique()

    print(f"\n  Total rows       : {total:,}")
    print(f"  Equipment units  : {equipments}")
    print(f"  Anomaly rows     : {anomalies:,} ({anomalies/total*100:.1f}%)")
    print(f"  Unique faults    : {faults}")
    print(f"  Date range       : {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"\n  Saved to: {path}")
    print("═" * 60)
