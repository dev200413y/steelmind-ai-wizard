"""
OmniSense AI Wizard â€” FastAPI Backend
======================================
Main entry point for the OmniSense REST API.

Endpoints:
    POST /diagnose  â€” Text + optional image/CSV/PDF upload
    POST /voice     â€” Audio file upload (Whisper â†’ pipeline)
    POST /feedback  â€” Engineer feedback submission
    GET  /health    â€” Health check
    GET  /history   â€” Get session history
    GET  /equipment â€” List available equipment

Run:
    uvicorn main:app --reload --port 8000
"""

import os
import uuid
import shutil
import logging
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("omnisense")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# App Initialization
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

app = FastAPI(
    title="OmniSense AI Wizard",
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

# Mount audio responses for frontend playback
audio_dir = UPLOAD_DIR / "audio_responses"
audio_dir.mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Reports directory
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# Session history storage (in-memory for demo, SQLite for production)
session_history: dict = {}
tickets_store: list[dict] = []


def _search_web_references(query: str, limit: int = 3) -> list[dict]:
    """Fetch lightweight web references for a query using DuckDuckGo HTML results."""
    q = (query or "").strip()
    if not q:
        return []
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": q},
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        html = response.text
        titles = re.findall(r'nofollow" class="result__a"[^>]*>(.*?)</a>', html)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html)
        links = re.findall(r'nofollow" class="result__a" href="(.*?)"', html)
        refs = []
        for index in range(min(limit, len(titles), len(links))):
            refs.append({
                "title": re.sub(r"<.*?>", "", titles[index]),
                "snippet": re.sub(r"<.*?>", "", snippets[index]) if index < len(snippets) else "",
                "url": links[index],
            })
        return refs
    except Exception as exc:
        logger.warning("Web reference search failed: %s", exc)
        return []


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Helper Functions
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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

    logger.info(f"ðŸ“ Saved upload: {filepath}")
    return str(filepath.absolute())


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "OmniSense AI Wizard",
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


@app.get("/predictions")
async def get_predictions():
    """Return risk and RUL predictions for all equipment."""
    from src.schemas import EQUIPMENT_IDS
    import random
    
    # In a full production system, this would query the RUL model for each equipment.
    # For now, we simulate predictions based on random distribution to feed the Risk Page.
    predictions = []
    for eq_id in EQUIPMENT_IDS:
        rul = random.randint(2, 60)
        if rul < 7:
            risk = "CRITICAL"
        elif rul < 14:
            risk = "HIGH"
        elif rul < 30:
            risk = "MEDIUM"
        else:
            risk = "LOW"
            
        predictions.append({
            "equipment_id": eq_id,
            "rul_days": rul,
            "risk_level": risk,
            "last_updated": datetime.now().isoformat()
        })
        
    # Sort by risk (CRITICAL first, i.e. lowest RUL)
    predictions.sort(key=lambda x: x["rul_days"])
        
    return {"predictions": predictions}


@app.post("/diagnose")
async def diagnose(
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    equipment_id: Optional[str] = Form(None),
    equipment_type: Optional[str] = Form(None),
    language: str = Form("en"),
    web_search: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    csv_file: Optional[UploadFile] = File(None),
    documents: Optional[list[UploadFile]] = File(None),
):
    """
    Main diagnosis endpoint â€” accepts text query + optional multimodal inputs.

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
    if not session_id:
        session_id = uuid.uuid4().hex[:12]
    logger.info(f"ðŸ”§ New diagnosis request | Session: {session_id} | Query: {query[:80]}...")

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
        "language": language or "en",
        "web_search": web_search,
        "session_id": session_id,
        "equipment_id": equipment_id,
        "equipment_type": equipment_type,
        "image_paths": [image_path] if image_path else [],
        "has_image": bool(image_path),
        "csv_paths": [csv_path] if csv_path else [],
        "has_csv": bool(csv_path),
        "doc_paths": doc_paths if doc_paths else [],
        "has_docs": bool(doc_paths),
    }

    from langchain_core.messages import HumanMessage
    messages = []
    if session_id in session_history and "messages" in session_history[session_id]:
        messages = session_history[session_id]["messages"].copy()
    messages.append(HumanMessage(content=query))
    initial_state["messages"] = messages

    try:
        # Run the LangGraph pipeline
        from src.graph.omnisense_graph import run_pipeline
        result = await run_pipeline(initial_state)
        if web_search:
            result["web_references"] = _search_web_references(query or result.get("query", ""))

        # Store in session history
        if session_id not in session_history:
            session_history[session_id] = {"timestamp": datetime.now().isoformat()}

        session_history[session_id].update({
            "query": query,
            "result": {
                "diagnosis": result.get("diagnosis"),
                "risk_level": result.get("risk_level"),
                "risk_details": result.get("risk_details"),
                "report": result.get("report"),
                "vision_output": result.get("vision_output"),
                "anomaly_result": result.get("anomaly_result"),
            },
            "messages": result.get("messages", [])
        })

        # Extract conversational AI response if it exists
        chat_response = None
        if "messages" in result and result["messages"]:
            for msg in reversed(result["messages"]):
                if getattr(msg, "type", "") == "ai" and not getattr(msg, "tool_calls", []):
                    chat_response = msg.content
                    break

        return {
            "session_id": session_id,
            "status": "success",
            "chat_response": chat_response,
            "diagnosis": result.get("diagnosis"),
            "risk_level": result.get("risk_level"),
            "risk_details": result.get("risk_details"),
            "report": result.get("report"),
            "vision_output": result.get("vision_output"),
            "anomaly_result": result.get("anomaly_result"),
            "web_references": result.get("web_references", []),
            "pipeline_errors": result.get("pipeline_errors", []),
        }

    except Exception as e:
        logger.error(f"âŒ Diagnosis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/voice")
async def voice_diagnose(
    audio: UploadFile = File(...),
    query: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    equipment_id: Optional[str] = Form(None),
    equipment_type: Optional[str] = Form(None),
    web_search: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    csv_file: Optional[UploadFile] = File(None),
    documents: Optional[list[UploadFile]] = File(None),
):
    """
    Voice-based diagnosis â€” accepts audio file, transcribes with Whisper,
    then runs through the diagnosis pipeline.

    Args:
        audio: Voice recording (WAV/MP3/WebM)
        equipment_id: Optional equipment ID
        equipment_type: Optional equipment type
        image: Optional equipment photo

    Returns:
        Diagnosis result + audio response path
    """
    if not session_id:
        session_id = uuid.uuid4().hex[:12]
    logger.info(f"ðŸŽ¤ Voice diagnosis request | Session: {session_id}")

    # Save audio file
    audio_path = await save_upload(audio, "audio")

    try:
        # Transcribe with Whisper
        from src.utils.voice import speech_to_text, text_to_speech
        
        stt_result = speech_to_text(audio_path)
        text = stt_result.get("text", "")
        if query:
            text = f"{query}\n\nSpoken input: {text}".strip()
        language = stt_result.get("language", "en")
        
        logger.info(f"ðŸ“ Transcribed: '{text[:80]}...' | Language: {language}")

        # Save image if provided
        image_path = None
        csv_path = None
        doc_paths = []
        if image and image.filename:
            image_path = await save_upload(image, "images")
        if csv_file and csv_file.filename:
            csv_path = await save_upload(csv_file, "csv")
        if documents:
            for doc in documents:
                if doc.filename:
                    doc_paths.append(await save_upload(doc, "documents"))

        # Run diagnosis pipeline
        initial_state = {
            "query": text,
            "language": language,
            "web_search": web_search,
            "session_id": session_id,
            "equipment_id": equipment_id,
            "equipment_type": equipment_type,
            "image_paths": [image_path] if image_path else [],
            "has_image": bool(image_path),
            "csv_paths": [csv_path] if csv_path else [],
            "has_csv": bool(csv_path),
            "doc_paths": doc_paths,
            "has_docs": bool(doc_paths),
        }

        from langchain_core.messages import HumanMessage
        messages = []
        if session_id in session_history and "messages" in session_history[session_id]:
            messages = session_history[session_id]["messages"].copy()
        messages.append(HumanMessage(content=text))
        initial_state["messages"] = messages

        from src.graph.omnisense_graph import run_pipeline
        result = await run_pipeline(initial_state)
        if web_search:
            result["web_references"] = _search_web_references(text)

        # Store in session history
        if session_id not in session_history:
            session_history[session_id] = {"timestamp": datetime.now().isoformat()}

        session_history[session_id].update({
            "query": text,
            "result": {
                "diagnosis": result.get("diagnosis"),
                "risk_level": result.get("risk_level"),
                "report": result.get("report"),
            },
            "messages": result.get("messages", [])
        })

        # Generate voice response
        response_text = ""
        if result.get("report") and result["report"].get("summary"):
            response_text = result["report"]["summary"]
        elif result.get("diagnosis") and result["diagnosis"].get("fault_identified"):
            response_text = result["diagnosis"]["fault_identified"]

        audio_response_path = None
        if response_text:
            audio_path_abs = text_to_speech(response_text, language)
            if audio_path_abs:
                audio_filename = os.path.basename(audio_path_abs)
                audio_response_path = f"http://localhost:8000/audio/{audio_filename}"

        return {
            "session_id": session_id,
            "status": "success",
            "transcribed_text": text,
            "detected_language": language,
            "diagnosis": result.get("diagnosis"),
            "risk_level": result.get("risk_level"),
            "report": result.get("report"),
            "audio_response_path": audio_response_path,
            "web_references": result.get("web_references", []),
        }

    except Exception as e:
        logger.error(f"âŒ Voice diagnosis failed: {str(e)}")
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
            "message": "Thank you! Your feedback helps improve OmniSense."
        }

    except Exception as e:
        logger.error(f"âŒ Feedback submission failed: {str(e)}")
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
    """Download a generated maintenance report (PDF or Markdown)."""
    pdf_path = REPORTS_DIR / f"{report_id}.pdf"
    md_path = REPORTS_DIR / f"{report_id}.md"
    # Try PDF first, then MD
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            filename=f"{report_id}.pdf",
            media_type="application/pdf"
        )
    elif md_path.exists():
        return FileResponse(
            path=str(md_path),
            filename=f"{report_id}.md",
            media_type="text/markdown"
        )
    raise HTTPException(status_code=404, detail="Report not found")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Voice Endpoints
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.post("/api/voice/stt")
async def speech_to_text_endpoint(audio: UploadFile = File(...)):
    """Convert voice audio to text using Whisper STT."""
    from src.utils.voice import speech_to_text
    
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    os.makedirs(f"{upload_dir}/audio_responses", exist_ok=True)
    
    audio_path = f"{upload_dir}/audio_{uuid.uuid4()}.webm"
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)
    
    try:
        result = speech_to_text(audio_path)
        return result
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


@app.post("/api/voice/tts")
async def text_to_speech_endpoint(
    text: str = Form(...),
    language: str = Form("en")
):
    """Convert text to speech audio."""
    from src.utils.voice import text_to_speech
    mp3_path = text_to_speech(text, language)
    return FileResponse(mp3_path, media_type="audio/mpeg")


@app.post("/api/session/upload")
async def upload_session_attachment(
    file: UploadFile = File(...),
    category: str = Form("document"),
):
    """Upload an attachment for WebSocket voice/chat sessions."""
    normalized = (category or "document").lower()
    folder_map = {
        "image": "images",
        "csv": "csv",
        "document": "documents",
        "pdf": "documents",
    }
    if normalized not in folder_map:
        raise HTTPException(status_code=400, detail="Unsupported attachment category")
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    saved_path = await save_upload(file, folder_map[normalized])
    return {
        "filename": file.filename,
        "category": normalized,
        "path": saved_path,
    }


@app.post("/api/tickets")
async def create_ticket(
    title: str = Form(...),
    description: str = Form(...),
    severity: str = Form("MEDIUM"),
    equipment_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    created_by: str = Form("engineer"),
):
    """Create a maintenance ticket from a chat or voice finding."""
    ticket = {
        "id": f"TKT-{len(tickets_store) + 1:04d}",
        "title": title,
        "description": description,
        "severity": severity.upper(),
        "equipment_id": equipment_id,
        "session_id": session_id,
        "created_by": created_by,
        "status": "OPEN",
        "created_at": datetime.now().isoformat(),
    }
    tickets_store.insert(0, ticket)
    return {"status": "success", "ticket": ticket}


@app.get("/api/tickets")
async def list_tickets():
    """List created maintenance tickets."""
    return {"total": len(tickets_store), "tickets": tickets_store}


@app.get("/api/analytics/overview")
async def analytics_overview():
    """Return a lightweight analytics snapshot for the frontend."""
    open_tickets = [t for t in tickets_store if t["status"] == "OPEN"]
    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for session in session_history.values():
        risk = ((session.get("result") or {}).get("risk_level") or "LOW").upper()
        if risk in risk_counts:
            risk_counts[risk] += 1
    return {
        "sessions": len(session_history),
        "tickets": len(tickets_store),
        "open_tickets": len(open_tickets),
        "risk_counts": risk_counts,
        "reports": len(list(REPORTS_DIR.glob("*.md"))) + len(list(REPORTS_DIR.glob("*.pdf"))),
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# WebSocket for Real-time Agent Status & Chat
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from langchain_core.messages import HumanMessage
from src.graph.omnisense_graph import get_pipeline

# Global dictionary to store state for active WebSocket sessions
ws_session_state = {}

@app.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket for continuous OmniSense chat and status streaming.
    Frontend connects here to send messages and get live agent progress.
    """
    await websocket.accept()
    pipeline = get_pipeline()
    
    # Initialize session state if not exists
    if session_id not in ws_session_state:
        ws_session_state[session_id] = {
            "messages": [],
            "session_id": session_id,
            "language": "en",
            "has_image": False,
            "has_csv": False,
            "has_docs": False,
            "image_paths": [],
            "csv_paths": [],
            "doc_paths": [],
            "equipment_id": None,
            "equipment_type": None,
            "agent_status": None,
            "vision_output": None,
            "rag_context": None,
            "anomaly_result": None,
            "diagnosis": None,
            "risk_level": None,
            "report": None,
            "force_critical": None,
            "rag_error": None,
            "pipeline_errors": []
        }
        
    try:
        while True:
            data = await websocket.receive_json()
            
            user_text = data.get("text", "")
            if not user_text:
                continue
                
            # Update state with new user message
            human_msg = HumanMessage(content=user_text)
            ws_session_state[session_id]["messages"].append(human_msg)
            ws_session_state[session_id]["query"] = user_text
            
            # Update context if provided dynamically mid-chat
            if data.get("equipment_id"):
                ws_session_state[session_id]["equipment_id"] = data["equipment_id"]
            if data.get("equipment_type"):
                ws_session_state[session_id]["equipment_type"] = data["equipment_type"]
            if data.get("language"):
                ws_session_state[session_id]["language"] = data["language"]

            image_paths = data.get("image_paths") or ([data["image_path"]] if data.get("image_path") else [])
            csv_paths = data.get("csv_paths") or []
            doc_paths = data.get("doc_paths") or []

            if image_paths:
                ws_session_state[session_id]["image_paths"].extend(image_paths)
                ws_session_state[session_id]["has_image"] = True
            if csv_paths:
                ws_session_state[session_id]["csv_paths"].extend(csv_paths)
                ws_session_state[session_id]["has_csv"] = True
            if doc_paths:
                ws_session_state[session_id]["doc_paths"].extend(doc_paths)
                ws_session_state[session_id]["has_docs"] = True
                
            try:
                # Notify UI that agent started thinking
                await websocket.send_json({"type": "status", "status": "Thinking...", "node": "orchestrator"})
                
                # Stream the pipeline execution (cyclic ReAct)
                async for event in pipeline.astream(ws_session_state[session_id], stream_mode="updates"):
                    for node_name, output in event.items():
                        
                        # Forward any agent_status updates immediately
                        if "agent_status" in output and output["agent_status"]:
                            await websocket.send_json({
                                "type": "status",
                                "status": output["agent_status"],
                                "node": node_name
                            })
                        
                        # Merge output back into our session state
                        for key, val in output.items():
                            if key == "messages" and val:
                                if isinstance(val, list):
                                    ws_session_state[session_id]["messages"].extend(val)
                                    
                                    # Stream final AI responses to frontend
                                    for msg in val:
                                        if getattr(msg, "type", "") == "ai" and not getattr(msg, "tool_calls", []):
                                            await websocket.send_json({
                                                "type": "message",
                                                "content": msg.content
                                            })
                            else:
                                ws_session_state[session_id][key] = val
                
                complete_payload = {
                    "session_id": session_id,
                    "chat_response": None,
                    "diagnosis": ws_session_state[session_id].get("diagnosis"),
                    "risk_level": ws_session_state[session_id].get("risk_level"),
                    "risk_details": ws_session_state[session_id].get("risk_details"),
                    "report": ws_session_state[session_id].get("report"),
                    "vision_output": ws_session_state[session_id].get("vision_output"),
                    "rag_context": ws_session_state[session_id].get("rag_context"),
                    "anomaly_result": ws_session_state[session_id].get("anomaly_result"),
                    "pipeline_errors": ws_session_state[session_id].get("pipeline_errors", []),
                }
                for msg in reversed(ws_session_state[session_id].get("messages", [])):
                    if getattr(msg, "type", "") == "ai" and not getattr(msg, "tool_calls", []):
                        complete_payload["chat_response"] = msg.content
                        break

                await websocket.send_json({"type": "complete", "data": complete_payload})
                await websocket.send_json({"type": "status", "status": "Waiting for input", "node": "idle"})
                
            except Exception as e:
                logger.error(f"Pipeline error in WS: {e}")
                await websocket.send_json({"type": "error", "content": str(e)})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Equipment List Endpoint
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/equipment/list")
async def get_equipment_list():
    """Return list of all tracked equipment for dropdown."""
    return {
        "equipment": [
            {"id": "BF-001", "name": "Blast Furnace 1", "plant": "Jamshedpur", "type": "Blast Furnace", "criticality": "critical"},
            {"id": "BF-002", "name": "Blast Furnace 2", "plant": "Jamshedpur", "type": "Blast Furnace", "criticality": "critical"},
            {"id": "RM-001", "name": "Rolling Mill 1", "plant": "Jamshedpur", "type": "Rolling Mill", "criticality": "high"},
            {"id": "RM-002", "name": "Rolling Mill 2", "plant": "Kalinganagar", "type": "Rolling Mill", "criticality": "high"},
            {"id": "CC-001", "name": "Continuous Caster 1", "plant": "Jamshedpur", "type": "Continuous Caster", "criticality": "high"},
            {"id": "HS-001", "name": "Hydraulic System 1", "plant": "Jamshedpur", "type": "Hydraulic System", "criticality": "medium"},
            {"id": "EAF-001", "name": "Electric Arc Furnace 1", "plant": "Kalinganagar", "type": "Electric Arc Furnace", "criticality": "critical"},
            {"id": "CV-001", "name": "Conveyor System 1", "plant": "IJmuiden", "type": "Conveyor System", "criticality": "low"},
            {"id": "CP-001", "name": "Compressor 1", "plant": "Port Talbot", "type": "Compressor", "criticality": "medium"},
        ]
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Live Sensor Data â€” Dashboard Feed
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# In-memory state for live simulation
import random
import numpy as np

_live_sensor_state = {}
_alert_history = []

# Normal operating ranges per equipment type
SENSOR_RANGES = {
    "Blast Furnace":       {"temp": (1200, 1320), "vib": (0.8, 2.0), "pres": (160, 200), "rpm": (1450, 1550), "cur": (85, 100)},
    "Rolling Mill":        {"temp": (380, 480),   "vib": (1.2, 2.5), "pres": (180, 220), "rpm": (900, 1100),  "cur": (95, 115)},
    "Continuous Caster":   {"temp": (1080, 1180), "vib": (0.7, 1.5), "pres": (115, 140), "rpm": (400, 500),   "cur": (78, 90)},
    "Electric Arc Furnace":{"temp": (1550, 1680), "vib": (1.5, 2.8), "pres": (65, 90),   "rpm": (0, 0),       "cur": (600, 720)},
    "Hydraulic System":    {"temp": (45, 65),     "vib": (0.5, 1.0), "pres": (225, 260),  "rpm": (1450, 1550), "cur": (38, 50)},
    "Conveyor System":     {"temp": (35, 55),     "vib": (0.8, 1.8), "pres": (0, 0),      "rpm": (100, 160),   "cur": (15, 25)},
    "Compressor":          {"temp": (70, 90),     "vib": (1.0, 2.0), "pres": (680, 750),   "rpm": (2950, 3080), "cur": (50, 65)},
}

EQUIPMENT_FLEET = [
    {"id": "BF-001", "name": "Blast Furnace 1",       "plant": "Jamshedpur",   "type": "Blast Furnace",        "criticality": "critical", "area": "Blast Furnace"},
    {"id": "BF-002", "name": "Blast Furnace 2",       "plant": "Jamshedpur",   "type": "Blast Furnace",        "criticality": "critical", "area": "Blast Furnace"},
    {"id": "RM-001", "name": "Rolling Mill 1",        "plant": "Jamshedpur",   "type": "Rolling Mill",         "criticality": "high",     "area": "Rolling Mill"},
    {"id": "RM-002", "name": "Rolling Mill 2",        "plant": "Kalinganagar", "type": "Rolling Mill",         "criticality": "high",     "area": "Rolling Mill"},
    {"id": "CC-001", "name": "Continuous Caster 1",   "plant": "Jamshedpur",   "type": "Continuous Caster",     "criticality": "high",     "area": "Steel Melting Shop"},
    {"id": "HS-001", "name": "Hydraulic System 1",    "plant": "Jamshedpur",   "type": "Hydraulic System",      "criticality": "medium",   "area": "Rolling Mill"},
    {"id": "EAF-001","name": "Electric Arc Furnace 1","plant": "Kalinganagar", "type": "Electric Arc Furnace",  "criticality": "critical", "area": "Steel Melting Shop"},
    {"id": "CV-001", "name": "Conveyor System 1",     "plant": "IJmuiden",     "type": "Conveyor System",       "criticality": "low",      "area": "Raw Materials"},
    {"id": "CP-001", "name": "Compressor 1",          "plant": "Port Talbot",  "type": "Compressor",            "criticality": "medium",   "area": "Utilities"},
]


def _init_live_state():
    """Initialize live sensor state from CSV baselines."""
    global _live_sensor_state
    if _live_sensor_state:
        return
    try:
        import pandas as pd
        df = pd.read_csv("src/data/sensor_data.csv")
        for eq in EQUIPMENT_FLEET:
            eq_data = df[df["equipment_id"] == eq["id"]]
            if len(eq_data) > 0:
                last = eq_data.iloc[-1]
                _live_sensor_state[eq["id"]] = {
                    "temperature": float(last.get("sensor_temperature", 0)),
                    "vibration": float(last.get("sensor_vibration", 0)),
                    "pressure": float(last.get("sensor_pressure", 0)),
                    "rpm": float(last.get("sensor_rpm", 0)),
                    "current": float(last.get("sensor_current", 0)),
                    "history": {"temperature": [], "vibration": [], "pressure": [], "rpm": [], "current": []},
                    "rul_days": random.randint(8, 120),
                }
            else:
                ranges = SENSOR_RANGES.get(eq["type"], SENSOR_RANGES["Compressor"])
                _live_sensor_state[eq["id"]] = {
                    "temperature": np.mean(ranges["temp"]),
                    "vibration": np.mean(ranges["vib"]),
                    "pressure": np.mean(ranges["pres"]),
                    "rpm": np.mean(ranges["rpm"]),
                    "current": np.mean(ranges["cur"]),
                    "history": {"temperature": [], "vibration": [], "pressure": [], "rpm": [], "current": []},
                    "rul_days": random.randint(15, 120),
                }
    except Exception as e:
        logger.warning(f"Could not init live state from CSV: {e}")
        for eq in EQUIPMENT_FLEET:
            ranges = SENSOR_RANGES.get(eq["type"], SENSOR_RANGES["Compressor"])
            _live_sensor_state[eq["id"]] = {
                "temperature": np.mean(ranges["temp"]),
                "vibration": np.mean(ranges["vib"]),
                "pressure": np.mean(ranges["pres"]),
                "rpm": np.mean(ranges["rpm"]),
                "current": np.mean(ranges["cur"]),
                "history": {"temperature": [], "vibration": [], "pressure": [], "rpm": [], "current": []},
                "rul_days": random.randint(15, 120),
            }


def _step_sensor(value, low, high, anomaly=False):
    """Brownian-walk one sensor value within range, with optional anomaly spike."""
    if anomaly:
        # Spike outside range
        overshoot = (high - low) * random.uniform(0.15, 0.4)
        return round(high + overshoot, 2)
    drift = (high - low) * random.uniform(-0.02, 0.02)
    value = value + drift
    # Soft clamp with slight overshoot allowed
    value = max(low - (high - low) * 0.05, min(high + (high - low) * 0.05, value))
    return round(value, 2)


def _classify_severity(eq_type, sensors):
    """Classify equipment health based on sensor thresholds."""
    ranges = SENSOR_RANGES.get(eq_type, {})
    violations = []
    
    for key, rng_key in [("temperature", "temp"), ("vibration", "vib"), ("pressure", "pres"), ("current", "cur")]:
        if rng_key not in ranges:
            continue
        low, high = ranges[rng_key]
        val = sensors.get(key, 0)
        if val == 0 and low == 0 and high == 0:
            continue
        if val > high * 1.15 or (low > 0 and val < low * 0.8):
            violations.append(("CRITICAL", key, val, f"{low}-{high}"))
        elif val > high * 1.05 or (low > 0 and val < low * 0.9):
            violations.append(("HIGH", key, val, f"{low}-{high}"))
        elif val > high or val < low:
            violations.append(("MEDIUM", key, val, f"{low}-{high}"))
    
    if any(v[0] == "CRITICAL" for v in violations):
        return "CRITICAL", violations
    elif any(v[0] == "HIGH" for v in violations):
        return "HIGH", violations
    elif any(v[0] == "MEDIUM" for v in violations):
        return "MEDIUM", violations
    return "NORMAL", []


@app.get("/api/live/sensors")
async def get_live_sensors():
    """
    Serve live sensor readings for all equipment.
    Uses Brownian-walk simulation from real CSV baselines.
    ~5% chance of anomaly injection per equipment per tick.
    """
    _init_live_state()
    
    readings = []
    new_alerts = []
    ts = datetime.now().isoformat()
    
    for eq in EQUIPMENT_FLEET:
        state = _live_sensor_state.get(eq["id"], {})
        ranges = SENSOR_RANGES.get(eq["type"], SENSOR_RANGES["Compressor"])
        
        # Anomaly injection: ~5% chance
        has_anomaly = random.random() < 0.05
        anomaly_sensor = random.choice(["temperature", "vibration", "pressure", "current"]) if has_anomaly else None
        
        # Step each sensor
        for sensor, rng_key in [("temperature", "temp"), ("vibration", "vib"), ("pressure", "pres"), ("rpm", "rpm"), ("current", "cur")]:
            low, high = ranges[rng_key]
            is_anomaly = (anomaly_sensor == sensor)
            state[sensor] = _step_sensor(state.get(sensor, np.mean((low, high))), low, high, anomaly=is_anomaly)
            # Keep last 60 readings for chart history
            hist = state.get("history", {}).get(sensor, [])
            hist.append(state[sensor])
            if len(hist) > 60:
                hist = hist[-60:]
            state.setdefault("history", {})[sensor] = hist
        
        # Slowly decay RUL
        current_rul = state.get("rul_days", random.randint(30, 120))
        if random.random() < 0.05:
            current_rul -= 1
        
        # Simulate maintenance replacement
        if current_rul <= 1:
            current_rul = random.randint(90, 150)
            
        state["rul_days"] = current_rul
        
        severity, violations = _classify_severity(eq["type"], state)
        
        # Generate alerts for violations
        for sev, sensor_name, val, normal_range in violations:
            alert = {
                "id": f"ALT-{eq['id']}-{sensor_name}-{len(_alert_history)}",
                "equipment_id": eq["id"],
                "equipment_name": eq["name"],
                "area": eq["area"],
                "plant": eq["plant"],
                "sensor": sensor_name,
                "value": val,
                "normal_range": normal_range,
                "severity": sev,
                "timestamp": ts,
                "message": f"{sensor_name.title()} ({val}) exceeds normal range ({normal_range})"
            }
            new_alerts.append(alert)
        
        readings.append({
            "equipment_id": eq["id"],
            "equipment_name": eq["name"],
            "equipment_type": eq["type"],
            "plant": eq["plant"],
            "area": eq["area"],
            "criticality": eq["criticality"],
            "severity": severity,
            "rul_days": state.get("rul_days", 30),
            "sensors": {
                "temperature": state.get("temperature", 0),
                "vibration": state.get("vibration", 0),
                "pressure": state.get("pressure", 0),
                "rpm": state.get("rpm", 0),
                "current": state.get("current", 0),
            },
            "history": state.get("history", {}),
            "timestamp": ts,
        })
    
    # Append new alerts to history (keep last 200)
    _alert_history.extend(new_alerts)
    while len(_alert_history) > 200:
        _alert_history.pop(0)
    
    # Count by severity
    all_alerts = _alert_history
    counts = {
        "critical": sum(1 for a in all_alerts if a["severity"] == "CRITICAL"),
        "high": sum(1 for a in all_alerts if a["severity"] == "HIGH"),
        "medium": sum(1 for a in all_alerts if a["severity"] == "MEDIUM"),
        "total": len(all_alerts),
    }
    
    return {
        "readings": readings,
        "alert_counts": counts,
        "new_alerts": new_alerts,
        "timestamp": ts,
    }


@app.get("/api/live/alerts")
async def get_live_alerts(severity: str = None, area: str = None, limit: int = 50):
    """Get alert history with optional severity/area filters."""
    alerts = list(reversed(_alert_history))  # newest first
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity.upper()]
    if area:
        alerts = [a for a in alerts if a["area"] == area]
    return {"alerts": alerts[:limit], "total": len(_alert_history)}


@app.get("/api/equipment/fleet")
async def get_equipment_fleet():
    """Get full equipment fleet with latest health status."""
    _init_live_state()
    fleet = []
    for eq in EQUIPMENT_FLEET:
        state = _live_sensor_state.get(eq["id"], {})
        severity, _ = _classify_severity(eq["type"], state)
        fleet.append({
            **eq,
            "severity": severity,
            "rul_days": state.get("rul_days", 30),
            "sensors": {
                "temperature": state.get("temperature", 0),
                "vibration": state.get("vibration", 0),
                "pressure": state.get("pressure", 0),
                "rpm": state.get("rpm", 0),
                "current": state.get("current", 0),
            }
        })
    return {"fleet": fleet}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Maintenance Records â€” History, Team, Faults, Downtime
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

MAINTENANCE_DATA = {
    "BF-001": {
        "equipment_id": "BF-001", "equipment_name": "Blast Furnace 1",
        "equipment_type": "Blast Furnace", "plant": "Jamshedpur", "area": "Blast Furnace",
        "commissioned_date": "2008-03-15", "age_years": 18,
        "last_maintenance": "2026-05-28", "next_maintenance_due": "2026-06-28",
        "maintenance_interval_days": 30, "maintenance_type": "Preventive",
        "total_maintenance_count": 87,
        "common_faults": [
            {"fault": "Tuyere burn-through", "frequency": 12, "severity": "CRITICAL", "avg_downtime_hrs": 48},
            {"fault": "Refractory lining erosion", "frequency": 8, "severity": "HIGH", "avg_downtime_hrs": 72},
            {"fault": "Cooling system leak", "frequency": 15, "severity": "MEDIUM", "avg_downtime_hrs": 8},
            {"fault": "Hot blast stove malfunction", "frequency": 5, "severity": "HIGH", "avg_downtime_hrs": 24},
            {"fault": "Charging bell jam", "frequency": 9, "severity": "MEDIUM", "avg_downtime_hrs": 6},
        ],
        "downtime_history": [
            {"date": "2026-05-15", "duration_hrs": 12, "reason": "Cooling system leak â€” pipe replacement", "type": "Corrective"},
            {"date": "2026-04-22", "duration_hrs": 48, "reason": "Tuyere #7 burn-through â€” emergency replacement", "type": "Emergency"},
            {"date": "2026-03-10", "duration_hrs": 4, "reason": "Routine inspection â€” slag notch cleaning", "type": "Preventive"},
            {"date": "2026-02-08", "duration_hrs": 8, "reason": "Cooling water pump bearing failure", "type": "Corrective"},
            {"date": "2026-01-05", "duration_hrs": 72, "reason": "Refractory relining â€” Zone 3", "type": "Planned Shutdown"},
            {"date": "2025-11-18", "duration_hrs": 6, "reason": "Gas cleaning system filter blockage", "type": "Corrective"},
        ],
        "total_downtime_hrs_ytd": 150,
        "mtbf_days": 28, "mttr_hrs": 18,
        "team": {
            "manager": "Rajesh Kumar Singh", "designation": "Senior Maintenance Engineer",
            "team_size": 12,
            "members": [
                {"name": "Amit Sharma", "role": "Lead Technician", "specialization": "Refractory"},
                {"name": "Priya Verma", "role": "Instrumentation Engineer", "specialization": "Sensors & PLC"},
                {"name": "Suresh Patel", "role": "Mechanical Fitter", "specialization": "Hydraulics"},
                {"name": "Deepak Tiwari", "role": "Electrical Technician", "specialization": "HV Systems"},
            ],
            "shift_pattern": "3-shift rotation (8hrs each)",
            "contact": "+91 98765 43210",
        },
    },
    "BF-002": {
        "equipment_id": "BF-002", "equipment_name": "Blast Furnace 2",
        "equipment_type": "Blast Furnace", "plant": "Jamshedpur", "area": "Blast Furnace",
        "commissioned_date": "2012-07-20", "age_years": 14,
        "last_maintenance": "2026-06-01", "next_maintenance_due": "2026-07-01",
        "maintenance_interval_days": 30, "maintenance_type": "Preventive",
        "total_maintenance_count": 64,
        "common_faults": [
            {"fault": "Slag buildup in hearth", "frequency": 10, "severity": "MEDIUM", "avg_downtime_hrs": 12},
            {"fault": "Tuyere overheating", "frequency": 7, "severity": "HIGH", "avg_downtime_hrs": 36},
            {"fault": "Burden distribution uneven", "frequency": 6, "severity": "MEDIUM", "avg_downtime_hrs": 4},
        ],
        "downtime_history": [
            {"date": "2026-05-20", "duration_hrs": 6, "reason": "Thermocouple replacement â€” Zone 5", "type": "Corrective"},
            {"date": "2026-04-12", "duration_hrs": 36, "reason": "Tuyere #3 overheating â€” coolant line repair", "type": "Emergency"},
            {"date": "2026-03-01", "duration_hrs": 4, "reason": "Routine inspection", "type": "Preventive"},
        ],
        "total_downtime_hrs_ytd": 82,
        "mtbf_days": 35, "mttr_hrs": 14,
        "team": {
            "manager": "Anand Mishra", "designation": "Maintenance Supervisor",
            "team_size": 10,
            "members": [
                {"name": "Vikram Joshi", "role": "Lead Technician", "specialization": "Furnace Operations"},
                {"name": "Sunita Devi", "role": "Instrumentation Tech", "specialization": "Temperature Sensors"},
                {"name": "Ravi Kumar", "role": "Welder", "specialization": "High-temp welding"},
            ],
            "shift_pattern": "3-shift rotation (8hrs each)",
            "contact": "+91 98765 43211",
        },
    },
    "RM-001": {
        "equipment_id": "RM-001", "equipment_name": "Rolling Mill 1",
        "equipment_type": "Rolling Mill", "plant": "Jamshedpur", "area": "Rolling Mill",
        "commissioned_date": "2005-11-10", "age_years": 21,
        "last_maintenance": "2026-06-05", "next_maintenance_due": "2026-06-19",
        "maintenance_interval_days": 14, "maintenance_type": "Predictive",
        "total_maintenance_count": 156,
        "common_faults": [
            {"fault": "Roll bearing failure", "frequency": 18, "severity": "CRITICAL", "avg_downtime_hrs": 24},
            {"fault": "Roll surface crack", "frequency": 11, "severity": "HIGH", "avg_downtime_hrs": 16},
            {"fault": "Gearbox oil leak", "frequency": 14, "severity": "MEDIUM", "avg_downtime_hrs": 6},
            {"fault": "Motor overheating", "frequency": 8, "severity": "HIGH", "avg_downtime_hrs": 10},
            {"fault": "Guide misalignment", "frequency": 20, "severity": "LOW", "avg_downtime_hrs": 2},
        ],
        "downtime_history": [
            {"date": "2026-06-02", "duration_hrs": 24, "reason": "Work roll bearing replacement â€” Stand 3", "type": "Corrective"},
            {"date": "2026-05-10", "duration_hrs": 4, "reason": "Roll grinding & cambering", "type": "Preventive"},
            {"date": "2026-04-18", "duration_hrs": 10, "reason": "Main motor winding overheating", "type": "Emergency"},
            {"date": "2026-03-25", "duration_hrs": 6, "reason": "Gearbox oil seal replacement", "type": "Corrective"},
            {"date": "2026-02-15", "duration_hrs": 2, "reason": "Guide alignment check", "type": "Preventive"},
        ],
        "total_downtime_hrs_ytd": 98,
        "mtbf_days": 18, "mttr_hrs": 8,
        "team": {
            "manager": "Manoj Kumar Dubey", "designation": "Rolling Mill Maintenance Head",
            "team_size": 15,
            "members": [
                {"name": "Sanjay Yadav", "role": "Lead Mechanic", "specialization": "Roll Bearings"},
                {"name": "Neha Gupta", "role": "Vibration Analyst", "specialization": "Predictive Maintenance"},
                {"name": "Ashok Verma", "role": "Electrician", "specialization": "VFD & Motors"},
                {"name": "Pooja Kumari", "role": "Lubrication Tech", "specialization": "Oil Analysis"},
            ],
            "shift_pattern": "2-shift (12hrs each)",
            "contact": "+91 98765 43212",
        },
    },
    "RM-002": {
        "equipment_id": "RM-002", "equipment_name": "Rolling Mill 2",
        "equipment_type": "Rolling Mill", "plant": "Kalinganagar", "area": "Rolling Mill",
        "commissioned_date": "2015-04-01", "age_years": 11,
        "last_maintenance": "2026-06-08", "next_maintenance_due": "2026-06-22",
        "maintenance_interval_days": 14, "maintenance_type": "Predictive",
        "total_maintenance_count": 82,
        "common_faults": [
            {"fault": "Spindle coupling wear", "frequency": 9, "severity": "MEDIUM", "avg_downtime_hrs": 8},
            {"fault": "Hydraulic AGC failure", "frequency": 5, "severity": "HIGH", "avg_downtime_hrs": 12},
            {"fault": "Roll chock bearing fatigue", "frequency": 7, "severity": "HIGH", "avg_downtime_hrs": 18},
        ],
        "downtime_history": [
            {"date": "2026-05-30", "duration_hrs": 8, "reason": "Spindle coupling replacement", "type": "Corrective"},
            {"date": "2026-04-28", "duration_hrs": 4, "reason": "Hydraulic AGC calibration", "type": "Preventive"},
            {"date": "2026-03-15", "duration_hrs": 18, "reason": "Roll chock bearing swap", "type": "Corrective"},
        ],
        "total_downtime_hrs_ytd": 54,
        "mtbf_days": 25, "mttr_hrs": 10,
        "team": {
            "manager": "Prakash Mohapatra", "designation": "Maintenance Engineer",
            "team_size": 11,
            "members": [
                {"name": "Bikash Panda", "role": "Lead Technician", "specialization": "Hydraulics"},
                {"name": "Sarita Das", "role": "Instrumentation", "specialization": "PLC & SCADA"},
            ],
            "shift_pattern": "3-shift rotation",
            "contact": "+91 98765 43213",
        },
    },
    "CC-001": {
        "equipment_id": "CC-001", "equipment_name": "Continuous Caster 1",
        "equipment_type": "Continuous Caster", "plant": "Jamshedpur", "area": "Steel Melting Shop",
        "commissioned_date": "2010-09-05", "age_years": 16,
        "last_maintenance": "2026-05-25", "next_maintenance_due": "2026-06-15",
        "maintenance_interval_days": 21, "maintenance_type": "Condition-Based",
        "total_maintenance_count": 110,
        "common_faults": [
            {"fault": "Mould oscillation failure", "frequency": 6, "severity": "CRITICAL", "avg_downtime_hrs": 36},
            {"fault": "Segment misalignment", "frequency": 12, "severity": "HIGH", "avg_downtime_hrs": 12},
            {"fault": "Spray nozzle clogging", "frequency": 22, "severity": "LOW", "avg_downtime_hrs": 2},
            {"fault": "Breakout warning", "frequency": 3, "severity": "CRITICAL", "avg_downtime_hrs": 48},
        ],
        "downtime_history": [
            {"date": "2026-05-20", "duration_hrs": 12, "reason": "Segment roller bearing replacement", "type": "Corrective"},
            {"date": "2026-04-15", "duration_hrs": 2, "reason": "Spray nozzle cleaning & replacement", "type": "Preventive"},
            {"date": "2026-03-08", "duration_hrs": 36, "reason": "Mould oscillation cylinder failure", "type": "Emergency"},
            {"date": "2026-01-22", "duration_hrs": 48, "reason": "Near-breakout event â€” full strand inspection", "type": "Emergency"},
        ],
        "total_downtime_hrs_ytd": 118,
        "mtbf_days": 22, "mttr_hrs": 16,
        "team": {
            "manager": "Saurabh Chatterjee", "designation": "Caster Maintenance Lead",
            "team_size": 9,
            "members": [
                {"name": "Arjun Ghosh", "role": "Mould Specialist", "specialization": "Oscillation Systems"},
                {"name": "Kavita Roy", "role": "Strand Technician", "specialization": "Segment Alignment"},
            ],
            "shift_pattern": "3-shift rotation",
            "contact": "+91 98765 43214",
        },
    },
    "HS-001": {
        "equipment_id": "HS-001", "equipment_name": "Hydraulic System 1",
        "equipment_type": "Hydraulic System", "plant": "Jamshedpur", "area": "Rolling Mill",
        "commissioned_date": "2014-02-18", "age_years": 12,
        "last_maintenance": "2026-06-10", "next_maintenance_due": "2026-07-10",
        "maintenance_interval_days": 30, "maintenance_type": "Preventive",
        "total_maintenance_count": 48,
        "common_faults": [
            {"fault": "Hydraulic oil contamination", "frequency": 14, "severity": "MEDIUM", "avg_downtime_hrs": 4},
            {"fault": "Seal/gasket leak", "frequency": 18, "severity": "LOW", "avg_downtime_hrs": 3},
            {"fault": "Pump cavitation", "frequency": 4, "severity": "HIGH", "avg_downtime_hrs": 16},
            {"fault": "Accumulator nitrogen loss", "frequency": 6, "severity": "MEDIUM", "avg_downtime_hrs": 4},
        ],
        "downtime_history": [
            {"date": "2026-05-28", "duration_hrs": 3, "reason": "Cylinder seal replacement", "type": "Corrective"},
            {"date": "2026-04-20", "duration_hrs": 4, "reason": "Oil filtration system flush", "type": "Preventive"},
            {"date": "2026-03-12", "duration_hrs": 16, "reason": "Main pump cavitation â€” bearing replaced", "type": "Emergency"},
        ],
        "total_downtime_hrs_ytd": 35,
        "mtbf_days": 40, "mttr_hrs": 6,
        "team": {
            "manager": "Ramesh Babu", "designation": "Hydraulics Supervisor",
            "team_size": 6,
            "members": [
                {"name": "Santosh Kumar", "role": "Hydraulics Technician", "specialization": "Pumps & Valves"},
                {"name": "Meena Devi", "role": "Oil Analysis Tech", "specialization": "Fluid Power"},
            ],
            "shift_pattern": "Day shift + on-call",
            "contact": "+91 98765 43215",
        },
    },
    "EAF-001": {
        "equipment_id": "EAF-001", "equipment_name": "Electric Arc Furnace 1",
        "equipment_type": "Electric Arc Furnace", "plant": "Kalinganagar", "area": "Steel Melting Shop",
        "commissioned_date": "2016-01-12", "age_years": 10,
        "last_maintenance": "2026-06-03", "next_maintenance_due": "2026-06-17",
        "maintenance_interval_days": 14, "maintenance_type": "Predictive",
        "total_maintenance_count": 95,
        "common_faults": [
            {"fault": "Electrode breakage", "frequency": 14, "severity": "CRITICAL", "avg_downtime_hrs": 8},
            {"fault": "Refractory wear (hearth)", "frequency": 6, "severity": "HIGH", "avg_downtime_hrs": 96},
            {"fault": "Transformer overheating", "frequency": 4, "severity": "CRITICAL", "avg_downtime_hrs": 24},
            {"fault": "Water-cooled panel leak", "frequency": 10, "severity": "HIGH", "avg_downtime_hrs": 12},
            {"fault": "EBT slide gate stuck", "frequency": 8, "severity": "MEDIUM", "avg_downtime_hrs": 6},
        ],
        "downtime_history": [
            {"date": "2026-06-01", "duration_hrs": 8, "reason": "Electrode column #2 replaced", "type": "Corrective"},
            {"date": "2026-05-12", "duration_hrs": 12, "reason": "Water-cooled panel patch welding", "type": "Emergency"},
            {"date": "2026-04-05", "duration_hrs": 6, "reason": "EBT slide gate cleaning", "type": "Preventive"},
            {"date": "2026-02-20", "duration_hrs": 96, "reason": "Full hearth reline â€” planned shutdown", "type": "Planned Shutdown"},
            {"date": "2026-01-10", "duration_hrs": 24, "reason": "Transformer cooling fan failure", "type": "Emergency"},
        ],
        "total_downtime_hrs_ytd": 170,
        "mtbf_days": 15, "mttr_hrs": 20,
        "team": {
            "manager": "Debashis Nayak", "designation": "EAF Maintenance Manager",
            "team_size": 14,
            "members": [
                {"name": "Tapan Sahoo", "role": "Electrode Specialist", "specialization": "Graphite Electrode"},
                {"name": "Smita Behera", "role": "Electrical Engineer", "specialization": "HV Transformer"},
                {"name": "Gopal Mohanty", "role": "Refractory Mason", "specialization": "Hearth Lining"},
                {"name": "Kiran Sethi", "role": "Water Systems Tech", "specialization": "Cooling Circuits"},
            ],
            "shift_pattern": "3-shift rotation",
            "contact": "+91 98765 43216",
        },
    },
    "CV-001": {
        "equipment_id": "CV-001", "equipment_name": "Conveyor System 1",
        "equipment_type": "Conveyor System", "plant": "IJmuiden", "area": "Raw Materials",
        "commissioned_date": "2018-06-25", "age_years": 8,
        "last_maintenance": "2026-06-09", "next_maintenance_due": "2026-07-09",
        "maintenance_interval_days": 30, "maintenance_type": "Preventive",
        "total_maintenance_count": 32,
        "common_faults": [
            {"fault": "Belt misalignment/tracking", "frequency": 16, "severity": "LOW", "avg_downtime_hrs": 2},
            {"fault": "Idler roller seizure", "frequency": 10, "severity": "MEDIUM", "avg_downtime_hrs": 3},
            {"fault": "Belt splice failure", "frequency": 3, "severity": "HIGH", "avg_downtime_hrs": 18},
            {"fault": "Drive motor overload", "frequency": 5, "severity": "MEDIUM", "avg_downtime_hrs": 6},
        ],
        "downtime_history": [
            {"date": "2026-05-22", "duration_hrs": 2, "reason": "Belt tracking adjustment", "type": "Preventive"},
            {"date": "2026-04-10", "duration_hrs": 3, "reason": "Idler roller swap â€” bay 14", "type": "Corrective"},
            {"date": "2026-02-28", "duration_hrs": 18, "reason": "Belt splice vulcanization", "type": "Corrective"},
        ],
        "total_downtime_hrs_ytd": 28,
        "mtbf_days": 55, "mttr_hrs": 4,
        "team": {
            "manager": "Hans van der Berg", "designation": "Conveyor Maintenance Lead",
            "team_size": 5,
            "members": [
                {"name": "Pieter de Vries", "role": "Belt Technician", "specialization": "Belt Splicing"},
                {"name": "Johan Bakker", "role": "Mechanic", "specialization": "Drive Systems"},
            ],
            "shift_pattern": "Day shift",
            "contact": "+31 20 555 1234",
        },
    },
    "CP-001": {
        "equipment_id": "CP-001", "equipment_name": "Compressor 1",
        "equipment_type": "Compressor", "plant": "Port Talbot", "area": "Utilities",
        "commissioned_date": "2011-08-30", "age_years": 15,
        "last_maintenance": "2026-06-06", "next_maintenance_due": "2026-06-20",
        "maintenance_interval_days": 14, "maintenance_type": "Condition-Based",
        "total_maintenance_count": 72,
        "common_faults": [
            {"fault": "Intake filter clogging", "frequency": 20, "severity": "LOW", "avg_downtime_hrs": 1},
            {"fault": "Valve plate crack", "frequency": 4, "severity": "CRITICAL", "avg_downtime_hrs": 24},
            {"fault": "Intercooler fouling", "frequency": 8, "severity": "MEDIUM", "avg_downtime_hrs": 6},
            {"fault": "Bearing wear/vibration", "frequency": 6, "severity": "HIGH", "avg_downtime_hrs": 12},
            {"fault": "Oil separator malfunction", "frequency": 5, "severity": "MEDIUM", "avg_downtime_hrs": 4},
        ],
        "downtime_history": [
            {"date": "2026-05-25", "duration_hrs": 1, "reason": "Intake filter replacement", "type": "Preventive"},
            {"date": "2026-04-30", "duration_hrs": 6, "reason": "Intercooler chemical cleaning", "type": "Preventive"},
            {"date": "2026-03-18", "duration_hrs": 12, "reason": "Drive-end bearing replacement", "type": "Corrective"},
            {"date": "2026-02-05", "duration_hrs": 24, "reason": "Valve plate crack â€” Stage 2 head rebuild", "type": "Emergency"},
        ],
        "total_downtime_hrs_ytd": 55,
        "mtbf_days": 30, "mttr_hrs": 8,
        "team": {
            "manager": "David Evans", "designation": "Utilities Maintenance Supervisor",
            "team_size": 7,
            "members": [
                {"name": "Gareth Williams", "role": "Compressor Technician", "specialization": "Reciprocating Compressors"},
                {"name": "Owen Davies", "role": "Vibration Analyst", "specialization": "Rotating Equipment"},
            ],
            "shift_pattern": "Day shift + on-call weekends",
            "contact": "+44 1639 882 100",
        },
    },
}

@app.get("/api/maintenance/records")
async def get_maintenance_records(equipment_id: str = None):
    """Get maintenance history, team, faults, and downtime for equipment."""
    if equipment_id and equipment_id in MAINTENANCE_DATA:
        return {"records": [MAINTENANCE_DATA[equipment_id]]}
    return {"records": list(MAINTENANCE_DATA.values())}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# New Endpoints â€” Predictions, Service Overdue, Summary
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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
        "plant_name": "Tata Steel â€” Jamshedpur Works",
        "system": "OmniSense AI Wizard v1.0",
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
# NEW ENDPOINTS FOR UI
# ══════════════════════════════════════════════════════════════

# In-memory database for tickets
tickets_db = []

@app.post("/api/tickets")
async def create_ticket(
    title: str = Form(...),
    description: str = Form(...),
    severity: str = Form("MEDIUM"),
    equipment_id: str = Form(""),
    session_id: str = Form(""),
    created_by: str = Form("engineer")
):
    """Create a new maintenance ticket."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "severity": severity,
        "status": "OPEN",
        "equipment_id": equipment_id,
        "created_at": datetime.now().isoformat(),
        "session_id": session_id,
        "created_by": created_by
    }
    tickets_db.append(ticket)
    return {"status": "success", "ticket": ticket}

@app.get("/api/tickets")
async def list_tickets():
    """List all tickets."""
    # Reverse so newest are first
    return {"tickets": tickets_db[::-1]}

@app.get("/api/analytics/overview")
async def get_analytics_overview():
    """Get system analytics."""
    reports = 0
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    for sid, session in session_history.items():
        if session.get("result"):
            r = session["result"]
            if r.get("report"):
                reports += 1
            if r.get("risk_level"):
                risk = r["risk_level"]
                if risk in risk_counts:
                    risk_counts[risk] += 1
                    
    return {
        "sessions": len(session_history),
        "tickets": len(tickets_db),
        "open_tickets": len([t for t in tickets_db if t["status"] == "OPEN"]),
        "reports": reports,
        "risk_counts": risk_counts
    }
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Startup Event
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.on_event("startup")
async def startup_event():
    """Initialize resources on server startup."""
    logger.info("ðŸ­ OmniSense AI Wizard starting up...")
    logger.info(f"ðŸ“‚ Upload directory: {UPLOAD_DIR.absolute()}")
    logger.info(f"ðŸ“‚ Reports directory: {REPORTS_DIR.absolute()}")

    # Check API keys
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("âš ï¸  GROQ_API_KEY not set â€” Diagnostic Agent will fail")
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("âš ï¸  GOOGLE_API_KEY not set â€” Vision Agent will fail")

    logger.info("âœ… OmniSense AI Wizard ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
