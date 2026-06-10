"""
SteelMind AI Wizard — Report Generator Agent
============================================
Compiles all agent outputs into a structured maintenance report.
Generates a markdown summary.
"""

import logging
from datetime import datetime
from src.schemas import SteelMindState

logger = logging.getLogger(__name__)

def run_report(state: SteelMindState) -> SteelMindState:
    """Generate markdown report from pipeline state."""
    logger.info("📝 Running Report Generator")
    
    try:
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        
        diagnosis = state.get("diagnosis", {})
        risk_level = state.get("risk_level", "UNKNOWN")
        risk_details = state.get("risk_details", {})
        anomaly_result = state.get("anomaly_result", {})
        
        equipment_id = state.get("equipment_id", "Unknown ID")
        equipment_type = state.get("equipment_type", "Unknown Type")
        
        urgency_hours = risk_details.get("urgency_hours", "N/A")
        fault_identified = diagnosis.get("fault_identified", "No diagnosis available.")
        repair_steps = diagnosis.get("repair_steps", [])
        
        # Formulate quick summary
        if repair_steps:
            first_step = repair_steps[0]
        else:
            first_step = "Consult manual for further instructions."
            
        summary = f"""🔍 **Fault:** {fault_identified}
⚠️ **Risk:** {risk_level} — Act within {urgency_hours} hours
🔧 **Next Step:** {first_step}"""

        # Detailed MD report
        repair_steps_md = "\n".join([f"{i+1}. {step}" for i, step in enumerate(repair_steps)])
        
        spare_parts = diagnosis.get("spare_parts_needed", [])
        if spare_parts:
            spares_md = "\n".join([f"- {p.get('quantity', 1)}x {p.get('name', 'Unknown')} ({p.get('part_number', 'N/A')})" for p in spare_parts])
        else:
            spares_md = "None required."
            
        sources = diagnosis.get("sources_cited", [])
        sources_md = "\n".join([f"- {s}" for s in sources]) if sources else "None cited."
        
        rul_days = anomaly_result.get("rul_days", "N/A") if anomaly_result else "N/A"
        
        risk_emoji = "🔴" if risk_level == "CRITICAL" else "🟠" if risk_level == "HIGH" else "🟡" if risk_level == "MEDIUM" else "🟢"
        
        full_report_md = f"""# SteelMind AI Wizard — Maintenance Report
**Report ID:** {report_id}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Equipment:** {equipment_id} — {equipment_type}
**Risk Level:** {risk_emoji} {risk_level}

---
## Executive Summary
{fault_identified} Recommended to act within {urgency_hours} hours.

---
## Fault Diagnosis
**Fault Identified:** {fault_identified}
**Confidence:** {diagnosis.get('confidence', 0.0)*100:.1f}%
**Root Cause:** {diagnosis.get('root_cause', 'Unknown')}

---
## Risk Assessment
**Final Risk:** **{risk_level}**
**Act within:** {urgency_hours} hours

---
## Repair Steps
{repair_steps_md}

---
## Spare Parts Required
{spares_md}

---
## Remaining Useful Life
**Estimate:** {rul_days} days

---
## Sources
{sources_md}
"""

        state["report"] = {
            "summary": summary,
            "full_report_md": full_report_md,
            "pdf_path": None, # Could add PDF generation here if needed
            "report_id": report_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"   Report generated: {report_id}")
        
    except Exception as e:
        logger.error(f"❌ Report Generator failed: {str(e)}")
        state["report"] = {
            "summary": "Report generation failed.",
            "full_report_md": "Report generation failed due to an error.",
            "error": str(e)
        }
        
    return state
