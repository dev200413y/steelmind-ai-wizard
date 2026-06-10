"""
SteelMind AI Wizard — Synthetic Maintenance Log Generator
==========================================================
Generates 500+ maintenance log entries with realistic steel-plant fault
descriptions, multi-step actions, spare parts, and outcome distributions.
Output is consumed by the RAG Agent and Report Generator.

Usage:
    python -m src.data.generate_maintenance_logs
    python src/data/generate_maintenance_logs.py
"""

from __future__ import annotations

import os
from datetime import timedelta
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
OUTPUT_FILE: str = "maintenance_logs.csv"
NUM_LOGS: int = 550  # guaranteed > 500

START_DATE: str = "2024-06-01"
END_DATE: str = "2026-05-31"

ENGINEERS: list[str] = [
    "ENG-101", "ENG-102", "ENG-103", "ENG-104", "ENG-105",
    "ENG-106", "ENG-107", "ENG-108", "ENG-109", "ENG-110",
    "ENG-111", "ENG-112", "ENG-113", "ENG-114", "ENG-115",
]

# ─── Equipment registry ────────────────────────────────────────
EQUIPMENT: dict[str, str] = {
    "BF-001": "Blast Furnace",
    "BF-002": "Blast Furnace",
    "RM-001": "Rolling Mill",
    "RM-002": "Rolling Mill",
    "CC-001": "Continuous Caster",
    "HS-001": "Hydraulic System",
    "EAF-001": "Electric Arc Furnace",
    "CV-001": "Conveyor System",
    "CP-001": "Compressor",
}

# ─── Fault templates per equipment type ─────────────────────────
# Each entry: (fault_reported, root_cause, action_steps, spare_parts,
#              typical_downtime_range_hours)

FAULT_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "Blast Furnace": [
        {
            "fault": "Abnormal tuyere temperature spike above 1450°C",
            "root_cause": "Tuyere nose erosion allowing direct contact with hot metal",
            "actions": "Isolate affected tuyere; Reduce blast volume by 15%; Cool tuyere with emergency water injection; Replace tuyere nose assembly; Resume normal blast after thermal stabilisation",
            "parts": "Tuyere nose assembly, Copper cooling coil, Refractory patch kit",
            "downtime": (8, 24),
        },
        {
            "fault": "Excessive vibration detected on blast furnace blower unit",
            "root_cause": "Bearing wear on main blower shaft due to misalignment after last overhaul",
            "actions": "Emergency shutdown of blower; Measure bearing clearances; Re-align shaft using laser alignment tool; Replace worn bearing set; Run at 50% capacity for 2 hours; Verify vibration within spec",
            "parts": "SKF 6320 bearing set, Alignment shim pack, Coupling gasket",
            "downtime": (12, 36),
        },
        {
            "fault": "Hot blast stove dome temperature irregularity",
            "root_cause": "Refractory lining deterioration in stove dome causing heat loss",
            "actions": "Switch to standby stove; Cool affected stove to safe temperature; Inspect refractory integrity with IR camera; Patch damaged refractory sections; Cure refractory for 48 hours; Restart stove on low firing",
            "parts": "High alumina refractory bricks, Refractory mortar, Ceramic fibre blanket",
            "downtime": (48, 96),
        },
        {
            "fault": "Abnormal pressure drop across furnace throat",
            "root_cause": "Scaffold formation in burden column restricting gas flow",
            "actions": "Reduce charging rate; Increase tuyere velocity to break scaffold; Monitor pressure recovery; Resume normal charging once stable; Document scaffold location for pattern analysis",
            "parts": "None required",
            "downtime": (4, 12),
        },
        {
            "fault": "Cooling water leak detected at furnace belly region",
            "root_cause": "Corrosion-induced pinhole leak in cooling stave pipe",
            "actions": "Reduce furnace load; Isolate leaking stave segment; Apply emergency clamp repair; Schedule permanent stave replacement during next planned outage; Monitor water loss rate",
            "parts": "Emergency pipe clamp, Cooling stave segment, Gasket set, Corrosion inhibitor",
            "downtime": (6, 18),
        },
        {
            "fault": "Charging skip hoist motor tripping on overcurrent",
            "root_cause": "Worn skip wheel bearings increasing mechanical load beyond motor rating",
            "actions": "Lock out skip hoist; Inspect skip wheels and track; Replace worn wheel bearings; Lubricate track; Test motor current draw under load; Return to service",
            "parts": "Skip wheel bearing (pair), Track lubricant cartridge, Motor contactor",
            "downtime": (8, 16),
        },
    ],
    "Rolling Mill": [
        {
            "fault": "Bearing overheating on work roll stand #3",
            "root_cause": "Insufficient lubrication flow to bearing housing due to blocked grease line",
            "actions": "Stop mill immediately; Remove bearing housing cover; Flush blocked grease line with solvent; Replace grease cartridge; Verify flow to each bearing point; Restart mill at reduced speed",
            "parts": "EP2 grease cartridge (6x), Grease line filter element, Bearing seal ring",
            "downtime": (4, 10),
        },
        {
            "fault": "Strip thickness variation exceeding ±0.05 mm tolerance",
            "root_cause": "Work roll crown profile worn unevenly after extended campaign",
            "actions": "Remove work rolls; Measure crown profile with profilometer; Re-grind rolls to target crown; Re-install and calibrate AGC system; Run test strip and verify thickness",
            "parts": "None required (roll grinding consumables)",
            "downtime": (6, 14),
        },
        {
            "fault": "Hydraulic gap control cylinder leaking",
            "root_cause": "Seal degradation in main gap cylinder due to high-temperature exposure",
            "actions": "Depressurise hydraulic circuit; Remove cylinder assembly; Replace primary and secondary seals; Reassemble and bleed circuit; Test gap control response; Resume production",
            "parts": "Hydraulic cylinder seal kit, O-ring set (Viton), Hydraulic fluid ISO VG68 (20L)",
            "downtime": (8, 20),
        },
        {
            "fault": "Motor drive inverter fault alarm on stand #1",
            "root_cause": "IGBT module failure in variable frequency drive caused by power surge",
            "actions": "Bypass failed stand; Inspect inverter module; Replace IGBT power module; Test gate driver signals; Clear fault codes; Verify drive response under load",
            "parts": "IGBT module (Infineon FF600R12ME4), Gate driver board, DC bus capacitor",
            "downtime": (10, 24),
        },
        {
            "fault": "Excessive roll chatter causing surface defects on strip",
            "root_cause": "Third-octave vibration mode excited by rolling speed resonance with backup roll eccentricity",
            "actions": "Reduce mill speed by 20%; Measure backup roll roundness; Re-grind backup rolls; Install vibration dampener on housing; Resume speed gradually while monitoring vibration spectrum",
            "parts": "Backup roll dampener kit, Accelerometer sensor (spare)",
            "downtime": (12, 28),
        },
    ],
    "Continuous Caster": [
        {
            "fault": "Breakout alarm triggered at mould level",
            "root_cause": "Thermocouple array detected shell thinning caused by slag entrapment in mould flux",
            "actions": "Emergency casting stop; Drain tundish; Inspect mould copper plates; Clean mould flux nozzles; Replace damaged oscillation springs; Restart after mould condition verified",
            "parts": "Mould copper plate set, Submerged entry nozzle, Mould flux powder (200 kg)",
            "downtime": (12, 36),
        },
        {
            "fault": "Secondary cooling spray nozzle blockage in Zone 3",
            "root_cause": "Scale build-up in spray headers from unfiltered cooling water",
            "actions": "Isolate Zone 3 spray circuit; Backflush headers with descaling solution; Replace blocked nozzles; Install inline water filter; Verify spray pattern with test run",
            "parts": "Spray nozzle (Zone 3 type, 8x), Inline strainer basket, Descaling chemical (50L)",
            "downtime": (4, 10),
        },
        {
            "fault": "Strand misalignment detected — slab edge cracking",
            "root_cause": "Segment roll bearing failure causing strand guide misalignment",
            "actions": "Stop casting on affected strand; Realign segment rolls using laser tracker; Replace failed bearing; Verify roll gap settings; Resume casting with close monitoring",
            "parts": "Segment roll bearing (NTN 23232), Alignment target set, Roll gap gauge",
            "downtime": (10, 24),
        },
        {
            "fault": "Tundish nozzle clogging during long sequence casting",
            "root_cause": "Alumina inclusion build-up on nozzle inner wall from high-aluminium steel grade",
            "actions": "Switch to standby tundish; Remove clogged nozzle; Clean with oxygen lancing; Replace with argon-purged nozzle; Adjust steel composition to reduce alumina formation",
            "parts": "Submerged entry nozzle (zirconia-graphite), Argon purge plug, Tundish lining patch",
            "downtime": (6, 14),
        },
    ],
    "Hydraulic System": [
        {
            "fault": "Hydraulic pump pressure dropping below 180 bar threshold",
            "root_cause": "Internal gear wear in axial piston pump reducing volumetric efficiency",
            "actions": "Switch to standby pump; Disassemble primary pump; Measure gear tooth wear; Replace piston barrel assembly; Reassemble and test at rated pressure; Monitor for 4 hours",
            "parts": "Axial piston barrel assembly, Pump shaft seal kit, Hydraulic filter element",
            "downtime": (8, 20),
        },
        {
            "fault": "Hydraulic oil temperature exceeding 75°C in main reservoir",
            "root_cause": "Oil cooler heat exchanger fouling reducing cooling efficiency",
            "actions": "Reduce system load; Bypass and clean oil cooler with chemical flush; Inspect cooler tubes for corrosion; Top up hydraulic oil level; Verify temperature stabilises below 60°C",
            "parts": "Heat exchanger cleaning kit, Hydraulic oil ISO VG46 (100L), Temperature sensor",
            "downtime": (4, 10),
        },
        {
            "fault": "Servo valve oscillation causing erratic cylinder movement",
            "root_cause": "Contaminated hydraulic fluid blocking servo valve pilot stage",
            "actions": "Isolate affected circuit; Remove servo valve; Clean pilot stage with ultrasonic cleaner; Replace inline filter; Flush circuit with clean oil; Recalibrate valve response",
            "parts": "Servo valve pilot spool (Moog D661), Inline filter (3μm), Flushing oil (50L)",
            "downtime": (6, 14),
        },
        {
            "fault": "Accumulator pre-charge pressure loss",
            "root_cause": "Bladder rupture in nitrogen accumulator due to fatigue cycling",
            "actions": "Depressurise system; Remove accumulator; Replace bladder element; Recharge with nitrogen to specified pressure; Reinstall and test pressure holding over 24 hours",
            "parts": "Accumulator bladder (10L capacity), Nitrogen gas cylinder, Pressure test gauge",
            "downtime": (4, 8),
        },
    ],
    "Electric Arc Furnace": [
        {
            "fault": "Electrode arm vibration above 4.5 mm/s during melting phase",
            "root_cause": "Electrode holder clamp loosening due to thermal cycling fatigue",
            "actions": "Reduce power input; Inspect electrode holder clamps; Retorque clamp bolts to specification; Replace damaged spring washers; Resume power ramp-up gradually",
            "parts": "Electrode clamp bolt set (Grade 10.9), Spring washer pack, Anti-seize compound",
            "downtime": (3, 8),
        },
        {
            "fault": "Roof delta section refractory erosion detected",
            "root_cause": "Excessive slag splashing during oxygen lancing damaging delta refractory",
            "actions": "Delay next heat; Cool furnace to safe temperature; Gunite damaged delta section; Allow curing time; Adjust oxygen lance angle for future heats; Resume melting",
            "parts": "High-MgO gunning mix (500 kg), Delta refractory bricks, Furnace roof gasket",
            "downtime": (8, 24),
        },
        {
            "fault": "Water leak detected in furnace shell cooling panel #7",
            "root_cause": "Thermal fatigue crack in copper cooling panel weld seam",
            "actions": "Emergency power off; Drain panel circuit; Apply temporary weld repair; Pressure test repair; Schedule full panel replacement during next campaign stop",
            "parts": "Copper cooling panel (replacement), Welding consumables, Pressure test kit",
            "downtime": (12, 36),
        },
        {
            "fault": "Transformer overcurrent trip during bore-in phase",
            "root_cause": "Short circuit between electrode tips due to scrap collapse in furnace",
            "actions": "Reset transformer protection relay; Inspect electrode tips for damage; Re-position electrodes; Restart bore-in at reduced power; Gradually increase to full power",
            "parts": "Electrode tip section (UHP grade), Protection relay fuse set",
            "downtime": (2, 6),
        },
        {
            "fault": "Excessive dust emission from furnace roof during charging",
            "root_cause": "Canopy hood extraction fan motor failure reducing suction",
            "actions": "Suspend charging; Inspect extraction fan motor; Replace burned motor winding; Balance fan impeller; Restart extraction system; Verify negative pressure in canopy",
            "parts": "Fan motor (75 kW, 4-pole), V-belt set, Impeller balance weight set",
            "downtime": (6, 16),
        },
    ],
    "Conveyor System": [
        {
            "fault": "Conveyor belt tracking off-centre by 50 mm",
            "root_cause": "Misaligned return idler bracket allowing belt drift under load",
            "actions": "Stop conveyor; Realign return idlers using belt tracking tool; Adjust take-up tension; Run empty for 15 minutes to verify tracking; Resume loaded operation",
            "parts": "Return idler roller (Ø127 mm), Tracking frame bracket, Belt tension gauge",
            "downtime": (2, 6),
        },
        {
            "fault": "Belt splice failure — belt torn at vulcanised joint",
            "root_cause": "Fatigue failure of vulcanised splice after exceeding design life cycles",
            "actions": "Emergency stop; Secure belt ends; Cut damaged section; Prepare new splice with vulcanising press; Cure for specified time; Tension belt and test",
            "parts": "Splice rubber sheet, Vulcanising press consumable kit, Belt clamp set",
            "downtime": (10, 24),
        },
        {
            "fault": "Drive pulley lagging worn — belt slipping under load",
            "root_cause": "Abrasive material carry-back wearing pulley rubber lagging surface",
            "actions": "Stop conveyor; Remove worn lagging; Clean pulley face; Apply new ceramic lagging tiles; Allow adhesive cure time; Restart and verify no slip",
            "parts": "Ceramic lagging tile set, Lagging adhesive (5L), Pulley scraper blade",
            "downtime": (6, 14),
        },
        {
            "fault": "Conveyor motor overheating — thermal protection tripping",
            "root_cause": "Overloaded belt due to upstream crusher producing oversized material",
            "actions": "Reduce crusher feed rate; Allow motor to cool; Inspect motor winding insulation; Clean motor cooling fins; Resume at controlled feed rate; Monitor motor temperature",
            "parts": "Motor cooling fan guard, Temperature relay (replacement), Insulation test probe",
            "downtime": (3, 8),
        },
    ],
    "Compressor": [
        {
            "fault": "Compressor discharge pressure oscillating ±30 bar",
            "root_cause": "Suction valve plate cracked causing intermittent valve leak-back",
            "actions": "Shut down compressor; Remove valve assembly; Inspect valve plate and seat; Replace cracked valve plate; Lap valve seat; Reassemble and test at rated pressure",
            "parts": "Suction valve plate (Inconel 718), Valve seat gasket, Valve spring set",
            "downtime": (8, 18),
        },
        {
            "fault": "Abnormal knocking noise from compressor crankcase",
            "root_cause": "Connecting rod big-end bearing wear exceeding 0.15 mm clearance",
            "actions": "Emergency shutdown; Drain crankcase oil; Remove crankcase cover; Measure bearing clearances; Replace con-rod bearing shells; Refill oil; Run-in at no load for 1 hour",
            "parts": "Con-rod bearing shell set, Crankcase gasket, Compressor oil SAE 30 (40L)",
            "downtime": (16, 36),
        },
        {
            "fault": "Inter-stage cooler outlet temperature above 85°C",
            "root_cause": "Tube fouling in air-cooled inter-stage heat exchanger",
            "actions": "Reduce compressor load to 60%; Clean cooler tubes with compressed air; Inspect fins for damage; Replace damaged fin sections; Resume full load and verify outlet temp",
            "parts": "Cooler fin section (spare), Tube cleaning lance, Temperature gauge",
            "downtime": (4, 10),
        },
        {
            "fault": "Oil carry-over into compressed air system",
            "root_cause": "Piston ring wear allowing excessive oil migration past compression stage",
            "actions": "Shut down compressor; Disassemble compression stage; Measure piston ring gaps; Replace worn rings and cylinder liner; Reassemble and test oil carry-over rate",
            "parts": "Piston ring set (3-ring), Cylinder liner, Coalescing filter element",
            "downtime": (12, 28),
        },
    ],
}


# ═══════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════

def _generate_log_id(year: int, seq: int) -> str:
    """Generate a structured log ID.

    Format: LOG-YYYY-NNNN (zero-padded 4-digit sequence).

    Args:
        year: Calendar year.
        seq: Sequential number.

    Returns:
        Log ID string.
    """
    return f"LOG-{year}-{seq:04d}"


def _pick_outcome(rng: np.random.Generator) -> str:
    """Pick maintenance outcome following the 70/20/10 distribution.

    Args:
        rng: NumPy random generator.

    Returns:
        One of RESOLVED, MONITORING, or ESCALATED.
    """
    return rng.choice(
        ["RESOLVED", "MONITORING", "ESCALATED"],
        p=[0.70, 0.20, 0.10],
    )


def _follow_up_date(
    base_date: pd.Timestamp,
    outcome: str,
    rng: np.random.Generator,
) -> str:
    """Compute a follow-up date based on outcome.

    RESOLVED → 30-90 days, MONITORING → 3-14 days, ESCALATED → 1-3 days.

    Args:
        base_date: Date of the maintenance event.
        outcome: Maintenance outcome.
        rng: NumPy random generator.

    Returns:
        Follow-up date as ISO string, or empty string if not applicable.
    """
    if outcome == "RESOLVED":
        delta = rng.integers(30, 91)
    elif outcome == "MONITORING":
        delta = rng.integers(3, 15)
    else:  # ESCALATED
        delta = rng.integers(1, 4)
    return (base_date + timedelta(days=int(delta))).strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════════════════════════
# Main Generator
# ═══════════════════════════════════════════════════════════════════

def generate_maintenance_logs(
    num_logs: int = NUM_LOGS,
    seed: int = SEED,
) -> pd.DataFrame:
    """Generate synthetic maintenance log entries.

    Draws from per-equipment fault templates to create realistic
    maintenance records with structured fields.

    Args:
        num_logs: Number of log entries to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame of maintenance log records.
    """
    rng = np.random.default_rng(seed)

    # Generate random dates across the range
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
    dates = rng.choice(date_range, size=num_logs, replace=True)
    dates.sort()

    records: list[dict[str, Any]] = []
    year_counters: dict[int, int] = {}

    for i in range(num_logs):
        dt = pd.Timestamp(dates[i])
        year = dt.year

        # Increment year-based sequence counter
        year_counters.setdefault(year, 0)
        year_counters[year] += 1

        # Pick equipment
        eq_id = rng.choice(list(EQUIPMENT.keys()))
        eq_type = EQUIPMENT[eq_id]

        # Pick a fault template
        templates = FAULT_TEMPLATES[eq_type]
        tmpl = templates[rng.integers(0, len(templates))]

        outcome = _pick_outcome(rng)
        downtime = round(
            rng.uniform(tmpl["downtime"][0], tmpl["downtime"][1]), 1
        )

        records.append({
            "log_id": _generate_log_id(year, year_counters[year]),
            "date": dt.strftime("%Y-%m-%d"),
            "equipment_id": eq_id,
            "equipment_type": eq_type,
            "fault_reported": tmpl["fault"],
            "root_cause": tmpl["root_cause"],
            "action_taken": tmpl["actions"],
            "downtime_hours": downtime,
            "spare_parts_used": tmpl["parts"],
            "engineer_id": rng.choice(ENGINEERS),
            "outcome": outcome,
            "follow_up_date": _follow_up_date(dt, outcome, rng),
        })

    return pd.DataFrame(records)


def save_maintenance_logs(
    df: pd.DataFrame,
    output_dir: str = OUTPUT_DIR,
) -> Path:
    """Save the maintenance logs DataFrame to CSV.

    Args:
        df: Maintenance logs DataFrame.
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
    print("  SteelMind AI Wizard — Maintenance Log Generator")
    print("═" * 60)

    df = generate_maintenance_logs()
    path = save_maintenance_logs(df)

    # Summary stats
    total = len(df)
    eq_counts = df["equipment_id"].value_counts()
    outcome_pct = df["outcome"].value_counts(normalize=True) * 100

    print(f"\n  Total logs       : {total}")
    print(f"  Date range       : {df['date'].min()} → {df['date'].max()}")
    print(f"\n  Equipment distribution:")
    for eq_id, count in eq_counts.items():
        print(f"    {eq_id:<10s}  {count:>4d}")
    print(f"\n  Outcome distribution:")
    for outcome, pct in outcome_pct.items():
        print(f"    {outcome:<12s}  {pct:>5.1f}%")
    print(f"\n  Saved to: {path}")
    print("═" * 60)
