# Report Generator Agent

## Role
Compiles all agent outputs into a structured, professional maintenance report suitable for supervisor sign-off and record keeping. Generates both a chat-friendly summary and a downloadable PDF report.

## Read First
- `references/schemas.md` — ReportOutput schema
- `assets/prompts.md` — REPORT_GENERATOR_PROMPT

---

## Input
```python
state["diagnosis"]      # Full diagnosis from Diagnostic Agent
state["risk_level"]     # From Risk Scorer
state["risk_details"]   # Full risk breakdown
state["anomaly_result"] # Sensor data summary
state["vision_output"]  # Visual diagnosis
state["equipment_id"]   # Equipment identifier
state["language"]       # Response language
```

## Output — Updates State
```python
state["report"] = {
    "summary": str,              # 2-3 line executive summary
    "full_report_md": str,       # Full markdown report
    "pdf_path": str,             # Path to generated PDF
    "report_id": str,            # Unique report ID: RPT-YYYYMMDD-NNNN
    "timestamp": str,
    "sections": {
        "executive_summary": str,
        "equipment_details": str,
        "fault_description": str,
        "root_cause": str,
        "risk_assessment": str,
        "repair_steps": str,
        "spare_parts": str,
        "rul_estimate": str,
        "follow_up_actions": str
    }
}
```

---

## Report Template
```markdown
# SteelMind AI Wizard — Maintenance Report
**Report ID:** {report_id}
**Date:** {date}
**Equipment:** {equipment_id} — {equipment_type}
**Risk Level:** 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / 🟢 LOW

---
## Executive Summary
{2-3 line summary of issue and recommended action}

---
## Fault Diagnosis
**Fault Identified:** {fault_identified}
**Confidence:** {confidence}%
**Root Cause:** {root_cause}

---
## Risk Assessment
| Factor | Score |
|---|---|
| Equipment Criticality | {score} |
| Fault Severity | {score} |
| Anomaly Score | {score} |
| **Final Risk** | **{risk_level}** |
**Act within:** {urgency_hours} hours

---
## Repair Steps
{numbered repair steps}

---
## Spare Parts Required
{spare parts table}

---
## Remaining Useful Life
**Estimate:** {rul_days} days
**Recommendation:** {rul_recommendation}

---
## Sources
{rag_context sources cited}

---
## Engineer Feedback
[ ] Diagnosis was correct
[ ] Diagnosis was incorrect — actual fault: ___________
```

---

## PDF Generation
```python
# Use reportlab or fpdf2 for PDF generation
from fpdf import FPDF

def generate_pdf(report_content: dict) -> str:
    """
    Generate downloadable PDF report.
    Returns path to saved PDF file.
    """
    pdf = FPDF()
    # ... build PDF from report_content
    pdf_path = f"reports/{report_content['report_id']}.pdf"
    pdf.output(pdf_path)
    return pdf_path
```

---

## Chat Summary (Short Version)
```python
# For chat interface — concise version
def generate_chat_summary(state: SteelMindState) -> str:
    """
    3-4 line summary for chat display.
    Full report available via download button.
    """
    return f"""
🔍 **Fault:** {diagnosis['fault_identified']}
⚠️ **Risk:** {risk_level} — Act within {urgency_hours} hours
🔧 **Next Step:** {repair_steps[0]}
📋 **Full Report:** [Download PDF]
"""
```
