# Risk Scorer Agent

## Role
Assigns a final risk level (LOW / MEDIUM / HIGH / CRITICAL) based on weighted multi-factor analysis. Considers equipment criticality, fault severity, anomaly score, spare parts availability, and maintenance history.

## Read First
- `references/schemas.md` — RiskOutput schema

---

## Input
```python
state["diagnosis"]       # From Diagnostic Agent
state["anomaly_result"]  # From Anomaly Agent (may be None)
state["vision_output"]   # From Vision Agent (may be None)
state["equipment_type"]  # For criticality lookup
state["force_critical"]  # Override flag from Anomaly Agent
```

## Output — Updates State
```python
state["risk_level"] = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
state["risk_details"] = {
    "final_risk": str,
    "risk_score": float,           # 0.0 to 1.0
    "factors": {
        "equipment_criticality": float,   # 35% weight
        "fault_severity": float,          # 30% weight
        "anomaly_score": float,           # 20% weight
        "spare_availability": float,      # 10% weight
        "maintenance_overdue": float      # 5% weight
    },
    "urgency_hours": int,          # Act within X hours
    "bottleneck_risk": bool,       # Is this a production bottleneck?
    "escalate_to_supervisor": bool
}
```

---

## Scoring Logic
```python
EQUIPMENT_CRITICALITY = {
    "Blast Furnace": 1.0,
    "Electric Arc Furnace": 0.95,
    "Continuous Caster": 0.90,
    "Rolling Mill": 0.85,
    "Hydraulic System": 0.75,
    "Compressor": 0.65,
    "Conveyor System": 0.55,
}

SEVERITY_SCORES = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.50,
    "LOW": 0.25
}

WEIGHTS = {
    "equipment_criticality": 0.35,
    "fault_severity": 0.30,
    "anomaly_score": 0.20,
    "spare_availability": 0.10,
    "maintenance_overdue": 0.05
}

def run_risk_scorer(state: SteelMindState) -> SteelMindState:
    """
    Calculate weighted risk score from all available signals.
    Override to CRITICAL if force_critical flag is set.
    """
    # Immediate override
    if state.get("force_critical"):
        state["risk_level"] = "CRITICAL"
        state["risk_details"] = {"final_risk": "CRITICAL", "forced_by": "anomaly_alert"}
        return state
    
    # Calculate weighted score
    factors = {}
    factors["equipment_criticality"] = EQUIPMENT_CRITICALITY.get(
        state.get("equipment_type"), 0.5
    )
    
    # Fault severity from diagnosis
    diagnosis_severity = state.get("diagnosis", {}).get("confidence", 0.5)
    vision_severity = SEVERITY_SCORES.get(
        state.get("vision_output", {}).get("severity", "LOW"), 0.25
    )
    factors["fault_severity"] = max(diagnosis_severity, vision_severity)
    
    # Anomaly score
    factors["anomaly_score"] = state.get("anomaly_result", {}).get("anomaly_score", 0.0)
    
    # Spare availability (check knowledge base / CSV)
    factors["spare_availability"] = check_spare_availability(state)
    
    # Maintenance overdue (check maintenance logs)
    factors["maintenance_overdue"] = check_maintenance_overdue(state)
    
    # Weighted final score
    final_score = sum(
        factors[k] * WEIGHTS[k] for k in WEIGHTS
    )
    
    # Map score to risk level
    if final_score >= 0.80:
        risk_level = "CRITICAL"
        urgency_hours = 2
    elif final_score >= 0.60:
        risk_level = "HIGH"
        urgency_hours = 8
    elif final_score >= 0.35:
        risk_level = "MEDIUM"
        urgency_hours = 48
    else:
        risk_level = "LOW"
        urgency_hours = 168  # 1 week
    
    state["risk_level"] = risk_level
    state["risk_details"] = {
        "final_risk": risk_level,
        "risk_score": round(final_score, 3),
        "factors": {k: round(v, 3) for k, v in factors.items()},
        "urgency_hours": urgency_hours,
        "bottleneck_risk": factors["equipment_criticality"] > 0.85,
        "escalate_to_supervisor": risk_level in ["HIGH", "CRITICAL"]
    }
    return state
```

---

## Frontend Badge Colors
```
LOW      → Green  (#1E6B3C)
MEDIUM   → Yellow (#7D5A00)
HIGH     → Orange (#C55A11)
CRITICAL → Red    (#C0392B) + pulsing animation
```
