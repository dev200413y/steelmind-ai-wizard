"""
OmniSense AI Wizard — Risk Scorer Agent
========================================
Assigns a final risk level based on weighted multi-factor analysis.
"""

import logging
from src.schemas import OmniSenseState
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)

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

def check_spare_availability(state: OmniSenseState) -> float:
    """Mock spare part availability score."""
    # In a real system, this would query an inventory DB.
    # For now, return 0.5 (medium risk)
    return 0.5

def check_maintenance_overdue(state: OmniSenseState) -> float:
    """Mock maintenance overdue score."""
    # In a real system, this would query a maintenance log DB.
    # For now, return 0.5
    return 0.5

def run_risk_scorer(state: OmniSenseState) -> OmniSenseState:
    """Calculate weighted risk score from all available signals."""
    # Extract tool call
    messages = state.get("messages", [])
    if not messages: return {}
    last_msg = messages[-1]
    
    tool_call_id = None
    if hasattr(last_msg, "tool_calls"):
        for tc in last_msg.tool_calls:
            if tc["name"] == "run_risk_scorer":
                tool_call_id = tc["id"]
                break
                
    if not tool_call_id:
        return {}

    updates = {"agent_status": "Evaluating operational risk..."}
    
    # Immediate override
    if state.get("force_critical"):
        logger.warning("   Forcing CRITICAL risk level due to anomaly alert")
        updates["risk_level"] = "CRITICAL"
        updates["risk_details"] = {
            "final_risk": "CRITICAL", 
            "forced_by": "anomaly_alert",
            "urgency_hours": 2,
            "escalate_to_supervisor": True
        }
        
        import json
        updates["messages"] = [ToolMessage(tool_call_id=tool_call_id, name="run_risk_scorer", content=f"Risk Score: {json.dumps(updates['risk_details'])}")]
        updates["agent_status"] = "Risk evaluation complete."
        return updates
    
    try:
        factors = {}
        factors["equipment_criticality"] = EQUIPMENT_CRITICALITY.get(
            state.get("equipment_type"), 0.5
        )
        
        # Fault severity from diagnosis
        diagnosis = state.get("diagnosis") or {}
        diagnosis_severity = diagnosis.get("confidence", 0.5)
        
        vision_output = state.get("vision_output") or {}
        vision_severity = SEVERITY_SCORES.get(vision_output.get("severity", "LOW"), 0.25)
        
        factors["fault_severity"] = max(diagnosis_severity, vision_severity)
        
        # Anomaly score
        anomaly_result = state.get("anomaly_result") or {}
        factors["anomaly_score"] = anomaly_result.get("anomaly_score", 0.0)
        
        # Mock values for spares and maintenance
        factors["spare_availability"] = check_spare_availability(state)
        factors["maintenance_overdue"] = check_maintenance_overdue(state)
        
        # Weighted final score
        final_score = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
        
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
            
        updates["risk_level"] = risk_level
        updates["risk_details"] = {
            "final_risk": risk_level,
            "risk_score": round(final_score, 3),
            "factors": {k: round(v, 3) for k, v in factors.items()},
            "urgency_hours": urgency_hours,
            "bottleneck_risk": factors["equipment_criticality"] > 0.85,
            "escalate_to_supervisor": risk_level in ["HIGH", "CRITICAL"]
        }
        
        import json
        updates["messages"] = [ToolMessage(tool_call_id=tool_call_id, name="run_risk_scorer", content=f"Risk Score: {json.dumps(updates['risk_details'])}")]
        
        logger.info(f"   Risk scoring complete. Final Risk: {risk_level} (Score: {final_score:.3f})")
        
    except Exception as e:
        logger.error(f"❌ Risk Scorer failed: {str(e)}")
        updates["risk_level"] = "MEDIUM" # Fallback
        updates["risk_details"] = {"final_risk": "MEDIUM", "error": str(e)}
        updates["messages"] = [ToolMessage(tool_call_id=tool_call_id, name="run_risk_scorer", content=f"Risk Scorer failed: {e}")]
        
    updates["agent_status"] = "Risk evaluation complete."
    return updates
