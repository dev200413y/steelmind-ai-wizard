"""
OmniSense AI Wizard — Report Generator Agent
Builds structured maintenance report directly from pipeline state.
No LLM call needed — all data is already in state.
Saves markdown report to reports/ folder.
"""

import logging
import os
import uuid
from datetime import datetime
from src.schemas import OmniSenseState
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)

RISK_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH": "🟠", 
    "MEDIUM": "🟡",
    "LOW": "🟢"
}

MAINTENANCE_ICONS = {
    "corrective": "🔧",
    "preventive": "🛡️",
    "predictive": "🔮"
}

def run_report(state: OmniSenseState) -> OmniSenseState:
    """
    Generate structured maintenance report from pipeline state.

    Builds a comprehensive 12-section markdown report directly from
    state data — no LLM call needed. Saves to reports/ folder.

    Args:
        state: The shared LangGraph pipeline state.

    Returns:
        OmniSenseState: Updated state with ``report`` populated.
    """
    # Extract tool call
    messages = state.get("messages", [])
    if not messages: return {}
    last_msg = messages[-1]
    
    tool_call_id = None
    if hasattr(last_msg, "tool_calls"):
        for tc in last_msg.tool_calls:
            if tc["name"] == "generate_report":
                tool_call_id = tc["id"]
                break
                
    if not tool_call_id:
        return {}

    updates = {"agent_status": "Generating formal maintenance report..."}
    
    try:
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        diagnosis = state.get("diagnosis") or {}
        risk_level = state.get("risk_level", "UNKNOWN")
        risk_details = state.get("risk_details") or {}
        anomaly = state.get("anomaly_result") or {}
        vision = state.get("vision_output") or {}
        
        risk_icon = RISK_EMOJI.get(risk_level, "⚪")
        maintenance_icon = MAINTENANCE_ICONS.get(diagnosis.get("maintenance_category", "corrective"), "🔧")
        
        # Executive summary
        summary = (
            f"{risk_icon} **{risk_level} Risk** — "
            f"{diagnosis.get('fault_identified', 'Analysis complete')}. "
            f"Act within {risk_details.get('urgency_hours', 'N/A')} hours. "
            f"{'⚠️ IMMEDIATE SHUTDOWN REQUIRED.' if diagnosis.get('shutdown_required') else ''}"
        )

        # Build repair steps section
        repair_steps_md = ""
        for i, step in enumerate(diagnosis.get("repair_steps", []), 1):
            repair_steps_md += f"{i}. {step}\n"
        if not repair_steps_md:
            repair_steps_md = "No specific repair steps generated. Refer to general SOP."

        # Build immediate actions
        immediate_md = ""
        for action in diagnosis.get("immediate_actions", []):
            immediate_md += f"- ⚡ {action}\n"

        # Build safety precautions
        safety_md = ""
        for prec in diagnosis.get("safety_precautions", []):
            safety_md += f"- 🦺 {prec}\n"

        # Build spare parts table
        spare_parts_md = ""
        spare_parts = diagnosis.get("spare_parts_needed", [])
        if spare_parts:
            spare_parts_md = "| Part Name | Quantity | Part Number | Urgency |\n"
            spare_parts_md += "|-----------|----------|-------------|----------|\n"
            for part in spare_parts:
                spare_parts_md += f"| {part.get('name','N/A')} | {part.get('quantity','N/A')} | {part.get('part_number','N/A')} | {part.get('urgency','scheduled')} |\n"
        else:
            spare_parts_md = "No spare parts required at this time."

        # Build sensor section
        sensor_md = "No sensor data provided."
        if anomaly:
            sensor_md = (
                f"- **Anomaly Detected:** {'Yes ⚠️' if anomaly.get('anomaly_detected') else 'No ✅'}\n"
                f"- **Anomaly Score:** {anomaly.get('anomaly_score', 0.0):.3f}\n"
                f"- **Most Affected Sensor:** {anomaly.get('anomalous_sensor', 'N/A')}\n"
                f"- **Current Value:** {anomaly.get('current_value', 'N/A')}\n"
                f"- **Normal Range:** {anomaly.get('normal_range', 'N/A')}\n"
                f"- **Remaining Useful Life:** {anomaly.get('rul_days', 'N/A')} days\n"
                f"- **Alert Status:** {'🚨 CRITICAL ALERT' if anomaly.get('alert_triggered') else '✅ Normal'}"
            )

        # Build visual section
        visual_md = "No image provided."
        if vision and vision.get("fault_detected"):
            ocr_text = vision.get("ocr_text", [])
            visible_context = vision.get("visible_equipment_context", "")
            visual_md = (
                f"- **Fault Type:** {vision.get('fault_type', 'N/A')}\n"
                f"- **Affected Component:** {vision.get('affected_component', 'N/A')}\n"
                f"- **Severity:** {vision.get('severity', 'N/A')}\n"
                f"- **Confidence:** {vision.get('confidence', 0.0):.0%}\n"
                f"- **Observations:** {', '.join(vision.get('visual_observations', []))}\n"
                f"- **OCR Text:** {', '.join(ocr_text) if ocr_text else 'None'}\n"
                f"- **Visible Context:** {visible_context or 'None'}"
            )

        # Build risk table
        risk_factors = risk_details.get("factors", {})
        risk_table_md = "| Risk Factor | Score |\n|-------------|-------|\n"
        factor_names = {
            "equipment_criticality": "Equipment Criticality",
            "fault_severity": "Fault Severity",
            "anomaly_score": "Sensor Anomaly",
            "spare_availability": "Spare Availability",
            "maintenance_overdue": "Maintenance Overdue"
        }
        for k, v in risk_factors.items():
            risk_table_md += f"| {factor_names.get(k, k)} | {v:.3f} |\n"

        # Sources cited
        sources_md = ""
        for src in diagnosis.get("sources_cited", []):
            sources_md += f"- 📄 {src}\n"
        if not sources_md:
            sources_md = "- General engineering knowledge base"

        full_report_md = f"""# OmniSense AI Wizard — Maintenance Report

**Report ID:** `{report_id}`  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Equipment:** {state.get('equipment_id', 'Not specified')} — {state.get('equipment_type', 'Not specified')}  
**Risk Level:** {risk_icon} **{risk_level}**  
**Maintenance Type:** {maintenance_icon} {diagnosis.get('maintenance_category', 'corrective').title()}  

---

## 1. Executive Summary

{summary}

---

## 2. Fault Diagnosis

| Parameter | Details |
|-----------|---------|
| **Fault Identified** | {diagnosis.get('fault_identified', 'N/A')} |
| **Root Cause** | {diagnosis.get('root_cause', 'N/A')} |
| **Confidence Level** | {diagnosis.get('confidence', 0.0):.0%} |
| **Estimated Repair Time** | {diagnosis.get('estimated_repair_time', 'N/A')} |
| **Shutdown Required** | {'⚠️ YES' if diagnosis.get('shutdown_required') else '✅ NO'} |

---

## 3. Risk Assessment

| Risk Factor | Value |
|-------------|-------|
| **Final Risk Level** | {risk_icon} {risk_level} |
| **Risk Score** | {risk_details.get('risk_score', 'N/A')} |
| **Act Within** | {risk_details.get('urgency_hours', 'N/A')} hours |
| **Production Bottleneck** | {'Yes ⚠️' if risk_details.get('bottleneck_risk') else 'No'} |
| **Supervisor Escalation** | {'Required ⚠️' if risk_details.get('escalate_to_supervisor') else 'Not Required'} |

{risk_table_md}

---

## 4. Immediate Actions Required

{immediate_md or "No immediate actions required."}

---

## 5. Safety Precautions

{safety_md if safety_md else "- Follow standard steel plant safety procedures"}
{"" if safety_md else "- Wear appropriate PPE"}

---

## 6. Step-by-Step Repair Plan

{repair_steps_md}

---

## 7. Spare Parts Required

{spare_parts_md}

---

## 8. Sensor & Anomaly Analysis

{sensor_md}

---

## 9. Visual Inspection Results

{visual_md}

---

## 10. Long-term Recommendations

{diagnosis.get('long_term_recommendations', 'No specific long-term recommendations.')}

---

## 11. Knowledge Sources

{sources_md}

---

## 12. Engineer Feedback

*Complete after repair to improve future AI recommendations:*

- [ ] Diagnosis was **correct** — resolved successfully  
- [ ] Diagnosis was **partially correct**  
- [ ] Diagnosis was **incorrect** — actual fault: _______________  
- Actual downtime: _____ hours  
- Additional notes: _______________________________________

---

*Generated by OmniSense AI Wizard | Tata Steel AI Hackathon 2026*  
*Session: {state.get('session_id', 'N/A')}*
"""

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/{report_id}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_report_md)

        updates["report"] = {
            "report_id": report_id,
            "summary": summary,
            "full_report_md": full_report_md,
            "report_path": report_path,
            "timestamp": datetime.now().isoformat(),
            "risk_level": risk_level,
            "equipment_id": state.get("equipment_id"),
        }

        logger.info(f"Report generated: {report_id}")
        
        # Append ToolMessage
        import json
        updates["messages"] = [ToolMessage(
            tool_call_id=tool_call_id, 
            name="generate_report", 
            content=f"Report generated successfully and saved to {report_path}. Summary: {summary}"
        )]

    except Exception as exc:
        logger.error("Report Generator failed: %s", exc, exc_info=True)
        updates["report"] = {
            "report_id": "RPT-ERROR",
            "summary": "Report generation failed",
            "full_report_md": f"# Report Generation Failed\n\nError: {str(exc)}",
            "report_path": None,
            "timestamp": datetime.now().isoformat(),
            "error": str(exc)
        }
        updates["messages"] = [ToolMessage(tool_call_id=tool_call_id, name="generate_report", content=f"Report generation failed: {exc}")]

    updates["agent_status"] = "Report generation complete."
    return updates
