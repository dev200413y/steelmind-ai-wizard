"""
SteelMind AI Wizard — FastAPI Backend
======================================
Main entry point for the SteelMind REST API.

Endpoints:
    POST /diagnose  — Text + optional image/CSV/PDF upload
    POST /voice     — Audio file upload (Whisper → pipeline)
    POST /feedback  — Engineer feedback submission
    GET  /health    — Health check
    GET  /history   — Get session history
    GET  /equipment — List available equipment

Run:
    uvicorn main:app --reload --port 8000
"""

import os
import uuid
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("steelmind")

# ══════════════════════════════════════════════════════════════
# App Initialization
# ══════════════════════════════════════════════════════════════

app = FastAPI(
    title="SteelMind AI Wizard",
    description="Multimodal Multi-Agent AI Maintenance Decision Support System for Steel Plants",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Reports directory
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# Session history storage (in-memory for demo, SQLite for production)
session_history: dict = {}


# ══════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════

async def save_upload(file: UploadFile, subfolder: str) -> str:
    """
    Save an uploaded file to disk and return its path.

    Args:
        file: The uploaded file
        subfolder: Subdirectory within uploads/

    Returns:
        Absolute path to saved file
    """
    save_dir = UPLOAD_DIR / subfolder
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    filepath = save_dir / filename

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    logger.info(f"📁 Saved upload: {filepath}")
    return str(filepath.absolute())


# ══════════════════════════════════════════════════════════════
# API Endpoints
# ══════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SteelMind AI Wizard",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "agents": [
            "orchestrator", "vision_agent", "rag_agent",
            "diagnostic_agent", "anomaly_agent", "risk_scorer",
            "report_generator", "feedback_agent"
        ]
    }


@app.get("/equipment")
async def list_equipment():
    """List all available equipment IDs and types."""
    from src.schemas import EQUIPMENT_IDS, EQUIPMENT_TYPES
    return {
        "equipment_ids": EQUIPMENT_IDS,
        "equipment_types": EQUIPMENT_TYPES,
    }


@app.post("/diagnose")
async def diagnose(
    query: str = Form(...),
    equipment_id: Optional[str] = Form(None),
    equipment_type: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    csv_file: Optional[UploadFile] = File(None),
    documents: Optional[list[UploadFile]] = File(None),
):
    """
    Main diagnosis endpoint — accepts text query + optional multimodal inputs.

    Args:
        query: Engineer's question (text)
        equipment_id: Optional equipment ID (e.g., BF-001)
        equipment_type: Optional equipment type (e.g., Blast Furnace)
        image: Optional equipment photo (JPG/PNG)
        csv_file: Optional sensor data CSV
        documents: Optional knowledge documents (PDF/TXT)

    Returns:
        Complete diagnosis with risk assessment and report
    """
    session_id = uuid.uuid4().hex[:12]
    logger.info(f"🔧 New diagnosis request | Session: {session_id} | Query: {query[:80]}...")

    # Save uploaded files
    image_path = None
    csv_path = None
    doc_paths = None

    if image and image.filename:
        image_path = await save_upload(image, "images")

    if csv_file and csv_file.filename:
        csv_path = await save_upload(csv_file, "csv")

    if documents:
        doc_paths = []
        for doc in documents:
            if doc.filename:
                path = await save_upload(doc, "documents")
                doc_paths.append(path)

    # Build initial state
    initial_state = {
        "query": query,
        "session_id": session_id,
        "equipment_id": equipment_id,
        "equipment_type": equipment_type,
        "image_path": image_path,
        "csv_path": csv_path,
        "doc_paths": doc_paths if doc_paths else None,
    }

    try:
        # Run the LangGraph pipeline
        from src.graph.steelmind_graph import run_pipeline
        result = await run_pipeline(initial_state)

        # Store in session history
        session_history[session_id] = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result": {
                "diagnosis": result.get("diagnosis"),
                "risk_level": result.get("risk_level"),
                "risk_details": result.get("risk_details"),
                "report": result.get("report"),
                "vision_output": result.get("vision_output"),
                "anomaly_result": result.get("anomaly_result"),
            }
        }

        return {
            "session_id": session_id,
            "status": "success",
            "diagnosis": result.get("diagnosis"),
            "risk_level": result.get("risk_level"),
            "risk_details": result.get("risk_details"),
            "report": result.get("report"),
            "vision_output": result.get("vision_output"),
            "anomaly_result": result.get("anomaly_result"),
            "pipeline_errors": result.get("pipeline_errors", []),
        }

    except Exception as e:
        logger.error(f"❌ Diagnosis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/voice")
async def voice_diagnose(
    audio: UploadFile = File(...),
    equipment_id: Optional[str] = Form(None),
    equipment_type: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Voice-based diagnosis — accepts audio file, transcribes with Whisper,
    then runs through the diagnosis pipeline.

    Args:
        audio: Voice recording (WAV/MP3/WebM)
        equipment_id: Optional equipment ID
        equipment_type: Optional equipment type
        image: Optional equipment photo

    Returns:
        Diagnosis result + audio response path
    """
    session_id = uuid.uuid4().hex[:12]
    logger.info(f"🎤 Voice diagnosis request | Session: {session_id}")

    # Save audio file
    audio_path = await save_upload(audio, "audio")

    try:
        # Transcribe with Whisper
        from src.utils.voice import transcribe_audio, text_to_speech
        text, language = transcribe_audio(audio_path)
        logger.info(f"📝 Transcribed: '{text[:80]}...' | Language: {language}")

        # Save image if provided
        image_path = None
        if image and image.filename:
            image_path = await save_upload(image, "images")

        # Run diagnosis pipeline
        initial_state = {
            "query": text,
            "language": language,
            "session_id": session_id,
            "equipment_id": equipment_id,
            "equipment_type": equipment_type,
            "image_path": image_path,
        }

        from src.graph.steelmind_graph import run_pipeline
        result = await run_pipeline(initial_state)

        # Generate voice response
        response_text = ""
        if result.get("report") and result["report"].get("summary"):
            response_text = result["report"]["summary"]
        elif result.get("diagnosis") and result["diagnosis"].get("fault_identified"):
            response_text = result["diagnosis"]["fault_identified"]

        audio_response_path = None
        if response_text:
            audio_response_path = text_to_speech(response_text, language)

        return {
            "session_id": session_id,
            "status": "success",
            "transcribed_text": text,
            "detected_language": language,
            "diagnosis": result.get("diagnosis"),
            "risk_level": result.get("risk_level"),
            "report": result.get("report"),
            "audio_response_path": audio_response_path,
        }

    except Exception as e:
        logger.error(f"❌ Voice diagnosis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice pipeline error: {str(e)}")


@app.post("/feedback")
async def submit_feedback(
    report_id: str = Form(...),
    diagnosis_correct: bool = Form(...),
    actual_fault: Optional[str] = Form(None),
    repair_steps_followed: bool = Form(True),
    actual_steps_taken: Optional[str] = Form(None),
    outcome: str = Form("RESOLVED"),
    downtime_hours: float = Form(0.0),
    engineer_notes: Optional[str] = Form(None),
    equipment_id: Optional[str] = Form(None),
):
    """
    Submit engineer feedback after repair execution.
    Used to improve future recommendations.

    Args:
        report_id: The report ID being reviewed
        diagnosis_correct: Was the AI diagnosis correct?
        actual_fault: What was the real fault (if AI was wrong)
        outcome: RESOLVED / ESCALATED / MONITORING
        downtime_hours: Total unplanned downtime
        engineer_notes: Free-text notes from engineer
    """
    try:
        from src.agents.feedback_agent import run_feedback

        feedback_input = {
            "report_id": report_id,
            "diagnosis_correct": diagnosis_correct,
            "actual_fault": actual_fault,
            "repair_steps_followed": repair_steps_followed,
            "actual_steps_taken": actual_steps_taken,
            "outcome": outcome,
            "downtime_hours": downtime_hours,
            "engineer_notes": engineer_notes,
            "equipment_id": equipment_id,
        }

        result = run_feedback(feedback_input)

        return {
            "status": "success",
            "feedback_id": result.get("feedback_id"),
            "saved": result.get("saved"),
            "knowledge_updated": result.get("knowledge_updated"),
            "message": "Thank you! Your feedback helps improve SteelMind."
        }

    except Exception as e:
        logger.error(f"❌ Feedback submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")


@app.get("/history/{session_id}")
async def get_session_history(session_id: str):
    """Get diagnosis history for a specific session."""
    if session_id not in session_history:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_history[session_id]


@app.get("/history")
async def get_all_history():
    """Get all session history (for dashboard)."""
    return {
        "total_sessions": len(session_history),
        "sessions": session_history,
    }


@app.get("/report/{report_id}")
async def download_report(report_id: str):
    """Download a generated maintenance report PDF."""
    pdf_path = REPORTS_DIR / f"{report_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path=str(pdf_path),
        filename=f"{report_id}.pdf",
        media_type="application/pdf"
    )


# ══════════════════════════════════════════════════════════════
# New Endpoints — Predictions, Service Overdue, Summary
# ══════════════════════════════════════════════════════════════

@app.get("/predictions")
async def get_predictions():
    """
    Get RUL predictions and failure risk for all equipment.
    Uses sensor data + trained ML models.
    """
    import pandas as pd
    import numpy as np
    from pathlib import Path

    sensor_path = Path("src/data/sensor_data.csv")
    if not sensor_path.exists():
        return {"predictions": [], "error": "Sensor data not found. Run data generation first."}

    df = pd.read_csv(str(sensor_path))

    predictions = []
    for eq_id in df["equipment_id"].unique():
        eq_data = df[df["equipment_id"] == eq_id]
        latest = eq_data.iloc[-1]
        eq_type = latest.get("equipment_type", "Unknown")

        # Calculate RUL from data
        rul = int(latest.get("rul_days", 180))
        anomaly_flag = int(latest.get("anomaly_flag", 0))

        # Recent trend: average of last 10 readings
        last_10 = eq_data.tail(10)
        temp_trend = float(last_10["sensor_temperature"].mean())
        vib_trend = float(last_10["sensor_vibration"].mean())

        # Failure probability (rough estimate)
        if rul < 7:
            failure_prob = 0.92
            risk = "CRITICAL"
            action = "Immediate replacement required"
        elif rul < 14:
            failure_prob = 0.70
            risk = "HIGH"
            action = "Schedule urgent maintenance"
        elif rul < 30:
            failure_prob = 0.45
            risk = "MEDIUM"
            action = "Plan maintenance in next shutdown"
        else:
            failure_prob = max(0.05, 0.3 - (rul / 500))
            risk = "LOW"
            action = "Continue monitoring"

        predictions.append({
            "equipment_id": eq_id,
            "equipment_type": eq_type,
            "rul_days": rul,
            "failure_probability": round(failure_prob, 2),
            "risk_level": risk,
            "recommended_action": action,
            "avg_temperature": round(temp_trend, 1),
            "avg_vibration": round(vib_trend, 2),
            "anomaly_detected": bool(anomaly_flag),
            "last_reading": latest.get("timestamp", "N/A"),
        })

    # Sort by RUL ascending (most urgent first)
    predictions.sort(key=lambda x: x["rul_days"])

    return {
        "predictions": predictions,
        "total_equipment": len(predictions),
        "critical_count": len([p for p in predictions if p["risk_level"] == "CRITICAL"]),
        "high_count": len([p for p in predictions if p["risk_level"] == "HIGH"]),
        "generated_at": datetime.now().isoformat(),
    }


@app.get("/service-overdue")
async def get_service_overdue():
    """
    Find equipment where maintenance is overdue or hasn't been done recently.
    """
    import pandas as pd
    from pathlib import Path

    logs_path = Path("src/data/maintenance_logs.csv")
    if not logs_path.exists():
        return {"overdue": [], "error": "Maintenance logs not found."}

    logs = pd.read_csv(str(logs_path))

    # Equipment list
    all_equipment = [
        {"id": "BF-001", "type": "Blast Furnace", "interval_days": 30},
        {"id": "BF-002", "type": "Blast Furnace", "interval_days": 30},
        {"id": "RM-001", "type": "Rolling Mill", "interval_days": 45},
        {"id": "RM-002", "type": "Rolling Mill", "interval_days": 45},
        {"id": "CC-001", "type": "Continuous Caster", "interval_days": 60},
        {"id": "EAF-001", "type": "Electric Arc Furnace", "interval_days": 30},
        {"id": "HS-001", "type": "Hydraulic System", "interval_days": 90},
        {"id": "CV-001", "type": "Conveyor System", "interval_days": 60},
        {"id": "CP-001", "type": "Compressor", "interval_days": 90},
    ]

    overdue_list = []
    today = datetime.now()

    for eq in all_equipment:
        eq_logs = logs[logs["equipment_id"] == eq["id"]]
        if eq_logs.empty:
            last_service = "Never"
            days_since = 999
        else:
            try:
                last_date = pd.to_datetime(eq_logs["date"]).max()
                last_service = last_date.strftime("%Y-%m-%d")
                days_since = (today - last_date).days
            except Exception:
                last_service = "Unknown"
                days_since = 999

        is_overdue = days_since > eq["interval_days"]
        overdue_by = max(0, days_since - eq["interval_days"]) if is_overdue else 0

        total_logs = len(eq_logs)
        resolved = len(eq_logs[eq_logs["outcome"] == "RESOLVED"]) if "outcome" in eq_logs.columns else 0
        escalated = len(eq_logs[eq_logs["outcome"] == "ESCALATED"]) if "outcome" in eq_logs.columns else 0

        overdue_list.append({
            "equipment_id": eq["id"],
            "equipment_type": eq["type"],
            "last_service_date": last_service,
            "days_since_service": days_since,
            "service_interval_days": eq["interval_days"],
            "is_overdue": is_overdue,
            "overdue_by_days": overdue_by,
            "total_maintenance_records": total_logs,
            "resolved_count": resolved,
            "escalated_count": escalated,
            "urgency": "CRITICAL" if overdue_by > 60 else "HIGH" if overdue_by > 30 else "MEDIUM" if is_overdue else "OK",
        })

    overdue_list.sort(key=lambda x: x["overdue_by_days"], reverse=True)

    return {
        "overdue": overdue_list,
        "total_overdue": len([o for o in overdue_list if o["is_overdue"]]),
        "total_ok": len([o for o in overdue_list if not o["is_overdue"]]),
        "generated_at": datetime.now().isoformat(),
    }


@app.get("/summary")
async def get_plant_summary():
    """
    Get a comprehensive plant-wide summary for the dashboard.
    Includes equipment health, predictions, maintenance status.
    """
    import pandas as pd
    from pathlib import Path

    sensor_path = Path("src/data/sensor_data.csv")
    logs_path = Path("src/data/maintenance_logs.csv")

    summary = {
        "plant_name": "Tata Steel — Jamshedpur Works",
        "system": "SteelMind AI Wizard v1.0",
        "generated_at": datetime.now().isoformat(),
        "total_equipment": 9,
        "sensor_data_available": sensor_path.exists(),
        "maintenance_logs_available": logs_path.exists(),
    }

    if sensor_path.exists():
        df = pd.read_csv(str(sensor_path))
        total_readings = len(df)
        anomaly_count = int(df["anomaly_flag"].sum()) if "anomaly_flag" in df.columns else 0
        equipment_ids = df["equipment_id"].unique().tolist()

        # Per-equipment latest status
        equipment_status = []
        for eq_id in equipment_ids:
            eq_data = df[df["equipment_id"] == eq_id].iloc[-1]
            rul = int(eq_data.get("rul_days", 180))
            status = "CRITICAL" if rul < 7 else "WARNING" if rul < 30 else "HEALTHY"
            equipment_status.append({
                "id": eq_id,
                "type": eq_data.get("equipment_type", "Unknown"),
                "status": status,
                "rul_days": rul,
                "temperature": round(float(eq_data.get("sensor_temperature", 0)), 1),
                "vibration": round(float(eq_data.get("sensor_vibration", 0)), 2),
                "pressure": round(float(eq_data.get("sensor_pressure", 0)), 1),
            })

        summary["total_sensor_readings"] = total_readings
        summary["total_anomalies_detected"] = anomaly_count
        summary["anomaly_rate"] = round(anomaly_count / total_readings * 100, 2) if total_readings > 0 else 0
        summary["equipment_status"] = equipment_status
        summary["critical_count"] = len([e for e in equipment_status if e["status"] == "CRITICAL"])
        summary["warning_count"] = len([e for e in equipment_status if e["status"] == "WARNING"])
        summary["healthy_count"] = len([e for e in equipment_status if e["status"] == "HEALTHY"])

    if logs_path.exists():
        logs = pd.read_csv(str(logs_path))
        summary["total_maintenance_logs"] = len(logs)
        if "outcome" in logs.columns:
            summary["resolved_count"] = int((logs["outcome"] == "RESOLVED").sum())
            summary["escalated_count"] = int((logs["outcome"] == "ESCALATED").sum())
            summary["monitoring_count"] = int((logs["outcome"] == "MONITORING").sum())
        if "downtime_hours" in logs.columns:
            summary["total_downtime_hours"] = round(float(logs["downtime_hours"].sum()), 1)
            summary["avg_downtime_hours"] = round(float(logs["downtime_hours"].mean()), 1)

    return summary


# ══════════════════════════════════════════════════════════════
# Startup Event
# ══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize resources on server startup."""
    logger.info("🏭 SteelMind AI Wizard starting up...")
    logger.info(f"📂 Upload directory: {UPLOAD_DIR.absolute()}")
    logger.info(f"📂 Reports directory: {REPORTS_DIR.absolute()}")

    # Check API keys
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("⚠️  GROQ_API_KEY not set — Diagnostic Agent will fail")
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("⚠️  GOOGLE_API_KEY not set — Vision Agent will fail")

    logger.info("✅ SteelMind AI Wizard ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
