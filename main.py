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
