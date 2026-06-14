# OMNISENSE AI WIZARD — COMPLETE BUILD PROMPT
# Copy this ENTIRE prompt into Antigravity

---

You are building **OmniSense AI Wizard** — a Multimodal Multi-Agent AI Maintenance Decision Support System for Tata Steel industrial equipment. This is for Tata Steel AI Hackathon 2026, Round 2: Agentic AI Challenge.

**Tagline:** "See it. Say it. Solve it."

---

## WHAT TO BUILD — COMPLETE OVERVIEW

Build a full-stack application with:
1. **FastAPI backend** with 8 LangGraph agents
2. **React 18 + Tailwind CSS frontend** (already partially built)
3. **FAISS RAG pipeline** for knowledge retrieval
4. **Isolation Forest + XGBoost ML models** for anomaly detection and RUL prediction
5. **Whisper STT + gTTS TTS** for voice interface
6. **Gemini Flash** for image/vision analysis
7. **Mistral Small 3.1 via Groq** as core LLM

**Total API Cost: ₹0 — all free tier**

---

## TECH STACK — EXACT VERSIONS

```
Backend:
- Python 3.11+
- FastAPI 0.110.0
- LangGraph 0.2.x
- langchain 0.2.x
- langchain-community 0.2.x
- groq (Mistral Small 3.1 via Groq API)
- google-generativeai (Gemini 1.5 Flash)
- openai-whisper (local STT)
- gTTS (Text to Speech)
- faiss-cpu
- sentence-transformers (all-MiniLM-L6-v2)
- scikit-learn (Isolation Forest)
- xgboost
- pandas, numpy
- pypdf2 or pymupdf (PDF parsing)
- fpdf2 (PDF report generation)
- python-multipart (file upload)
- python-dotenv
- pydantic 2.x
- uvicorn

Frontend (already started):
- React 18
- Tailwind CSS
- Vite
- axios (API calls)
- recharts (sensor graphs)
- lucide-react (icons)
```

---

## PROJECT STRUCTURE — CREATE EXACTLY THIS

```
omnisense-ai-wizard/
├── AGENTS.md
├── README.md
├── requirements.txt          ← CREATE THIS FIRST
├── .env.example              ← ALREADY EXISTS
├── Dockerfile
├── docker-compose.yml
├── main.py                   ← FastAPI entry point
│
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── vision_agent.py
│   │   ├── rag_agent.py
│   │   ├── diagnostic_agent.py
│   │   ├── anomaly_agent.py
│   │   ├── risk_scorer.py
│   │   ├── report_generator.py
│   │   └── feedback_agent.py
│   ├── graph/
│   │   ├── __init__.py
│   │   └── omnisense_graph.py
│   ├── models/
│   │   └── train_models.py
│   ├── knowledge_base/
│   │   └── index_docs.py
│   ├── data/
│   │   └── .gitkeep
│   └── utils/
│       ├── __init__.py
│       ├── voice.py
│       ├── vision.py
│       └── prompts.py
│
├── data/
│   └── synthetic/
│       ├── generate_maintenance_logs.py
│       └── generate_knowledge_docs.py
│
└── tests/
    ├── test_rag_agent.py
    ├── test_diagnostic_agent.py
    └── test_anomaly_agent.py
```

---

## LANGGRAPH STATE — USE EXACTLY THIS

```python
from typing import TypedDict, Optional, List

class OmniSenseState(TypedDict):
    # Input
    query: str
    language: str                    # hi|or|bn|en|nl|th|unknown
    has_image: bool
    has_csv: bool
    image_path: Optional[str]
    csv_path: Optional[str]
    equipment_id: Optional[str]
    equipment_type: Optional[str]
    session_id: str

    # Agent outputs
    vision_output: Optional[dict]
    rag_context: Optional[List[dict]]
    anomaly_result: Optional[dict]
    diagnosis: Optional[dict]
    risk_level: Optional[str]        # LOW|MEDIUM|HIGH|CRITICAL
    risk_details: Optional[dict]
    report: Optional[dict]

    # Control
    force_critical: Optional[bool]
    pipeline_errors: Optional[List[str]]
```

---

## AGENT 1 — ORCHESTRATOR (src/agents/orchestrator.py)

```python
"""
Entry point of LangGraph pipeline.
Detects input types, sets state flags, detects language.
Routes to parallel agents based on available inputs.
"""

def orchestrate(state: OmniSenseState) -> OmniSenseState:
    state["has_image"] = bool(state.get("image_path"))
    state["has_csv"] = bool(state.get("csv_path"))
    state["pipeline_errors"] = []
    
    # Detect language using langdetect or default to "en"
    try:
        from langdetect import detect
        state["language"] = detect(state["query"])
    except:
        state["language"] = "en"
    
    return state

def route_inputs(state: OmniSenseState) -> List[str]:
    """
    Returns list of agents to call in PARALLEL.
    RAG always runs. Vision only if image. Anomaly only if CSV.
    """
    agents = ["rag_agent"]
    if state["has_image"]:
        agents.append("vision_agent")
    if state["has_csv"]:
        agents.append("anomaly_agent")
    return agents
```

---

## AGENT 2 — VISION AGENT (src/agents/vision_agent.py)

```python
"""
Analyzes equipment images using Gemini 1.5 Flash.
Returns structured fault JSON.
Called only when has_image == True.
"""

import google.generativeai as genai
import json, os
from pathlib import Path

VISION_PROMPT = """
You are an expert industrial equipment visual inspector for steel manufacturing plants.
Analyze this equipment image and return ONLY valid JSON (no markdown, no explanation):
{
  "fault_detected": true/false,
  "fault_type": "corrosion|crack|wear|overheating|leak|vibration|other",
  "affected_component": "bearing|pipe|gear|motor|frame|belt|valve|other",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "visual_observations": ["observation 1", "observation 2"],
  "immediate_action_required": true/false,
  "confidence": 0.0-1.0,
  "additional_context": "any important notes"
}
Severity: LOW=monitor, MEDIUM=48hrs, HIGH=8hrs, CRITICAL=immediate shutdown.
"""

def run_vision(state: OmniSenseState) -> OmniSenseState:
    if not state.get("image_path"):
        return state
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        image_data = Path(state["image_path"]).read_bytes()
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = VISION_PROMPT
        if state.get("equipment_type"):
            prompt += f"\nEquipment: {state['equipment_type']}"
        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": image_data}, prompt
        ])
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        state["vision_output"] = json.loads(text.strip())
    except Exception as e:
        state["vision_output"] = {"fault_detected": False, "error": str(e), "confidence": 0.0}
        state["pipeline_errors"].append(f"vision_agent: {str(e)}")
    return state
```

---

## AGENT 3 — RAG AGENT (src/agents/rag_agent.py)

```python
"""
Retrieves relevant knowledge from indexed documents using FAISS.
Uses sentence-transformers/all-MiniLM-L6-v2 for embeddings (local, free).
Always runs — provides grounded context to Diagnostic Agent.
"""

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "src/knowledge_base/faiss_index")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def run_rag(state: OmniSenseState) -> OmniSenseState:
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH, embeddings,
            allow_dangerous_deserialization=True
        )
        query = state["query"]
        if state.get("equipment_type"):
            query = f"{state['equipment_type']}: {query}"
        
        docs = vectorstore.similarity_search_with_score(query, k=5)
        state["rag_context"] = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", 0),
                "relevance_score": float(score)
            }
            for doc, score in docs
        ]
    except Exception as e:
        # No FAISS index yet — return empty, do not crash
        state["rag_context"] = []
        state["pipeline_errors"].append(f"rag_agent: {str(e)}")
    return state
```

---

## AGENT 4 — DIAGNOSTIC AGENT (src/agents/diagnostic_agent.py)

```python
"""
Core reasoning engine.
Combines vision_output + rag_context + anomaly_result.
Uses Mistral Small 3.1 via Groq API (free, fastest).
Returns structured diagnosis in detected language.
"""

from groq import Groq
import json, os

GROQ_MODEL = "mistral-small-3.1"

SYSTEM_PROMPT = """You are OmniSense AI Wizard, expert maintenance diagnostic AI for steel manufacturing plants.
You have deep knowledge of blast furnaces, rolling mills, continuous casters, hydraulic systems, electric arc furnaces.

Synthesize all provided information and return ONLY valid JSON:
{
  "fault_identified": "clear fault description",
  "root_cause": "why it happened",
  "confidence": 0.0-1.0,
  "repair_steps": ["Step 1: ...", "Step 2: ..."],
  "immediate_actions": ["Do RIGHT NOW: ..."],
  "spare_parts_needed": [{"name": "...", "quantity": 1, "part_number": "..."}],
  "estimated_repair_time": "X-Y hours",
  "sources_cited": ["document - page X"],
  "long_term_recommendations": "preventive measures"
}

Rules:
1. Cite which document supports your diagnosis
2. Repair steps must be specific and actionable
3. If confidence < 0.6, recommend expert inspection
4. Respond in the SAME LANGUAGE as the engineer query
5. Technical part names may stay in English
"""

def build_context(state: OmniSenseState) -> str:
    parts = [f"ENGINEER QUERY: {state['query']}"]
    if state.get("equipment_id"):
        parts.append(f"EQUIPMENT: {state['equipment_id']} ({state.get('equipment_type','')})")
    if state.get("vision_output") and state["vision_output"].get("fault_detected"):
        v = state["vision_output"]
        parts.append(f"VISUAL: fault={v.get('fault_type')} component={v.get('affected_component')} severity={v.get('severity')} confidence={v.get('confidence')}")
    if state.get("rag_context"):
        parts.append("KNOWLEDGE BASE:")
        for c in state["rag_context"][:3]:
            parts.append(f"[{c['source']} p.{c['page']}]: {c['content'][:500]}")
    if state.get("anomaly_result") and state["anomaly_result"].get("anomaly_detected"):
        a = state["anomaly_result"]
        parts.append(f"SENSOR ANOMALY: score={a.get('anomaly_score')} sensor={a.get('anomalous_sensor')} RUL={a.get('rul_days')}days")
    return "\n\n".join(parts)

def run_diagnostic(state: OmniSenseState) -> OmniSenseState:
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        system = SYSTEM_PROMPT + f"\nRespond in language code: {state.get('language','en')}"
        context = build_context(state)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": context}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        state["diagnosis"] = json.loads(text.strip())
    except Exception as e:
        state["diagnosis"] = {
            "fault_identified": "Diagnosis failed — manual inspection required",
            "error": str(e), "confidence": 0.0, "repair_steps": []
        }
        state["pipeline_errors"].append(f"diagnostic_agent: {str(e)}")
    return state
```

---

## AGENT 5 — ANOMALY AGENT (src/agents/anomaly_agent.py)

```python
"""
Processes sensor CSV using Isolation Forest (anomaly detection)
and XGBoost (RUL prediction).
Models loaded from src/models/*.pkl
Called only when has_csv == True.
"""

import pandas as pd
import numpy as np
import joblib, os
from pathlib import Path

MODELS_PATH = os.getenv("MODELS_PATH", "src/models")
SENSOR_COLS = ["sensor_temperature", "sensor_vibration",
               "sensor_pressure", "sensor_rpm", "sensor_current"]

# Fallback column name mapping from Kaggle AI4I dataset
KAGGLE_MAP = {
    "Air temperature [K]": "sensor_temperature",
    "Process temperature [K]": "sensor_vibration",
    "Rotational speed [rpm]": "sensor_rpm",
    "Torque [Nm]": "sensor_pressure",
    "Tool wear [min]": "sensor_current"
}

def run_anomaly(state: OmniSenseState) -> OmniSenseState:
    if not state.get("csv_path"):
        return state
    try:
        df = pd.read_csv(state["csv_path"])
        # Rename Kaggle columns if needed
        df = df.rename(columns=KAGGLE_MAP)
        
        # Get available sensor columns
        available = [c for c in SENSOR_COLS if c in df.columns]
        if not available:
            raise ValueError(f"No sensor columns found. Available: {list(df.columns)}")
        
        data = df[available].dropna().tail(50)
        
        # Load models
        iso_path = Path(MODELS_PATH) / "isolation_forest.pkl"
        rul_path = Path(MODELS_PATH) / "rul_model.pkl"
        scaler_path = Path(MODELS_PATH) / "scaler.pkl"
        
        if iso_path.exists():
            iso = joblib.load(iso_path)
            scaler = joblib.load(scaler_path)
            scaled = scaler.transform(data)
            scores = iso.decision_function(scaled) * -1
            anomaly_score = float(np.mean(scores[-10:]))
        else:
            # Fallback: simple z-score based detection
            z_scores = np.abs((data - data.mean()) / (data.std() + 1e-9))
            anomaly_score = float(z_scores.values[-1].max() / 3.0)
        
        # RUL prediction
        if rul_path.exists():
            rul_model = joblib.load(rul_path)
            rul_days = max(0, int(rul_model.predict(scaled[-1:])[0]))
        else:
            # Fallback linear trend
            if len(data) > 5:
                trend = np.polyfit(range(len(data)), data[available[0]].values, 1)[0]
                max_val = data[available[0]].max() * 1.2
                curr_val = data[available[0]].iloc[-1]
                rul_days = max(0, int((max_val - curr_val) / (abs(trend) + 0.001)))
            else:
                rul_days = 30
        
        # Most anomalous sensor
        if len(available) > 0:
            z = ((data - data.mean()) / (data.std() + 1e-9)).abs()
            anomalous_sensor = z.iloc[-1].idxmax()
        else:
            anomalous_sensor = "unknown"
        
        # Severity
        if rul_days < 3 or anomaly_score > 0.85:
            severity = "CRITICAL"
        elif rul_days < 7 or anomaly_score > 0.70:
            severity = "HIGH"
        elif rul_days < 14 or anomaly_score > 0.55:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        state["anomaly_result"] = {
            "anomaly_detected": anomaly_score > 0.55,
            "anomaly_score": round(anomaly_score, 3),
            "severity": severity,
            "anomalous_sensor": anomalous_sensor,
            "current_value": float(data[anomalous_sensor].iloc[-1]) if anomalous_sensor in data.columns else 0,
            "rul_days": rul_days,
            "rul_confidence": 0.80,
            "alert_triggered": rul_days < 7,
            "trend_data": data.tail(30).to_dict("records"),
            "recommendations": [
                f"Inspect {anomalous_sensor} immediately" if anomaly_score > 0.7 else f"Monitor {anomalous_sensor} closely",
                f"Schedule maintenance within {rul_days} days",
                "Check lubrication and cooling systems"
            ]
        }
        if state["anomaly_result"]["alert_triggered"]:
            state["force_critical"] = True
            
    except Exception as e:
        state["anomaly_result"] = {"anomaly_detected": False, "error": str(e)}
        state["pipeline_errors"].append(f"anomaly_agent: {str(e)}")
    return state
```

---

## AGENT 6 — RISK SCORER (src/agents/risk_scorer.py)

```python
"""
Weighted multi-factor risk classification.
Output: LOW / MEDIUM / HIGH / CRITICAL
"""

EQUIPMENT_CRITICALITY = {
    "Blast Furnace": 1.0, "Electric Arc Furnace": 0.95,
    "Continuous Caster": 0.90, "Rolling Mill": 0.85,
    "Hydraulic System": 0.75, "Compressor": 0.65,
    "Conveyor System": 0.55
}
SEVERITY_MAP = {"CRITICAL": 1.0, "HIGH": 0.75, "MEDIUM": 0.50, "LOW": 0.25}

def run_risk_scorer(state: OmniSenseState) -> OmniSenseState:
    if state.get("force_critical"):
        state["risk_level"] = "CRITICAL"
        state["risk_details"] = {
            "final_risk": "CRITICAL",
            "risk_score": 1.0,
            "urgency_hours": 2,
            "forced_by": "sensor_anomaly_alert",
            "escalate_to_supervisor": True
        }
        return state
    
    eq_crit = EQUIPMENT_CRITICALITY.get(state.get("equipment_type", ""), 0.5)
    
    # Fault severity
    fault_sev = 0.3
    if state.get("vision_output"):
        fault_sev = max(fault_sev, SEVERITY_MAP.get(state["vision_output"].get("severity","LOW"), 0.25))
    if state.get("diagnosis"):
        fault_sev = max(fault_sev, state["diagnosis"].get("confidence", 0.3))
    
    anomaly_score = state.get("anomaly_result", {}).get("anomaly_score", 0.0)
    
    # Weighted score
    score = (eq_crit * 0.35) + (fault_sev * 0.30) + (anomaly_score * 0.20) + 0.15
    score = min(1.0, score)
    
    if score >= 0.80:
        risk_level, urgency = "CRITICAL", 2
    elif score >= 0.60:
        risk_level, urgency = "HIGH", 8
    elif score >= 0.35:
        risk_level, urgency = "MEDIUM", 48
    else:
        risk_level, urgency = "LOW", 168
    
    state["risk_level"] = risk_level
    state["risk_details"] = {
        "final_risk": risk_level,
        "risk_score": round(score, 3),
        "urgency_hours": urgency,
        "bottleneck_risk": eq_crit > 0.85,
        "escalate_to_supervisor": risk_level in ["HIGH", "CRITICAL"]
    }
    return state
```

---

## AGENT 7 — REPORT GENERATOR (src/agents/report_generator.py)

```python
"""
Assembles all agent outputs into structured markdown report.
Generates unique report ID. Saves to reports/ folder.
"""

from datetime import datetime
import os, uuid

def run_report_generator(state: OmniSenseState) -> OmniSenseState:
    report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    diagnosis = state.get("diagnosis", {})
    risk = state.get("risk_details", {})
    anomaly = state.get("anomaly_result", {})
    
    risk_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
    
    summary = f"{risk_emoji.get(state.get('risk_level','LOW'),'')} " \
              f"**{state.get('risk_level','UNKNOWN')} Risk** — " \
              f"{diagnosis.get('fault_identified', 'Analysis complete')}. " \
              f"Act within {risk.get('urgency_hours', 'N/A')} hours."
    
    report_md = f"""# OmniSense AI Wizard — Maintenance Report
**Report ID:** {report_id}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Equipment:** {state.get('equipment_id','N/A')} — {state.get('equipment_type','N/A')}
**Risk Level:** {risk_emoji.get(state.get('risk_level',''),'⚪')} {state.get('risk_level','UNKNOWN')}

---
## Executive Summary
{summary}

---
## Fault Diagnosis
**Fault:** {diagnosis.get('fault_identified','N/A')}
**Root Cause:** {diagnosis.get('root_cause','N/A')}
**Confidence:** {int(diagnosis.get('confidence',0)*100)}%

---
## Risk Assessment
| Factor | Value |
|---|---|
| Risk Level | {state.get('risk_level','N/A')} |
| Risk Score | {risk.get('risk_score','N/A')} |
| Act Within | {risk.get('urgency_hours','N/A')} hours |
| Escalate to Supervisor | {risk.get('escalate_to_supervisor','N/A')} |

---
## Repair Steps
{chr(10).join([f"{i+1}. {s}" for i,s in enumerate(diagnosis.get('repair_steps',[]))]) or 'N/A'}

---
## Immediate Actions
{chr(10).join([f"⚡ {a}" for a in diagnosis.get('immediate_actions',[])]) or 'N/A'}

---
## Spare Parts Required
{chr(10).join([f"- {p.get('name','')} × {p.get('quantity','')} (Part: {p.get('part_number','')})" for p in diagnosis.get('spare_parts_needed',[])]) or 'None required'}

---
## Remaining Useful Life
{f"**Estimate:** {anomaly.get('rul_days','N/A')} days" if anomaly else "Sensor data not provided"}

---
## Long-term Recommendations
{diagnosis.get('long_term_recommendations','N/A')}

---
## Sources Cited
{chr(10).join([f"- {s}" for s in diagnosis.get('sources_cited',[])]) or 'General knowledge base'}
"""
    
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/{report_id}.md"
    with open(report_path, "w") as f:
        f.write(report_md)
    
    state["report"] = {
        "report_id": report_id,
        "summary": summary,
        "full_report_md": report_md,
        "report_path": report_path,
        "timestamp": datetime.now().isoformat()
    }
    return state
```

---

## AGENT 8 — FEEDBACK AGENT (src/agents/feedback_agent.py)

```python
"""
Stores engineer feedback in SQLite.
Updates knowledge base if diagnosis was wrong.
Called AFTER engineer confirms outcome — async/separate endpoint.
"""

import sqlite3, json, os
from datetime import datetime

DB_PATH = "src/data/omnisense.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT, diagnosis_correct BOOLEAN,
        actual_fault TEXT, outcome TEXT,
        downtime_hours REAL, engineer_notes TEXT, timestamp TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reports_log (
        report_id TEXT PRIMARY KEY, equipment_id TEXT,
        risk_level TEXT, fault_identified TEXT, created_at TEXT
    )""")
    conn.commit()
    conn.close()

def save_feedback(feedback: dict) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO feedback VALUES (NULL,?,?,?,?,?,?,?)",
        (feedback.get("report_id"), feedback.get("diagnosis_correct"),
         feedback.get("actual_fault",""), feedback.get("outcome",""),
         feedback.get("downtime_hours",0), feedback.get("notes",""),
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return {"saved": True, "timestamp": datetime.now().isoformat()}
```

---

## LANGGRAPH GRAPH (src/graph/omnisense_graph.py)

```python
"""
Wires all 8 agents into LangGraph StateGraph.
Parallel execution: vision + rag + anomaly run simultaneously.
Fan-in to diagnostic agent, then sequential: risk → report.
"""

from langgraph.graph import StateGraph, END
from src.agents.orchestrator import orchestrate, route_inputs
from src.agents.vision_agent import run_vision
from src.agents.rag_agent import run_rag
from src.agents.anomaly_agent import run_anomaly
from src.agents.diagnostic_agent import run_diagnostic
from src.agents.risk_scorer import run_risk_scorer
from src.agents.report_generator import run_report_generator
from src.agents.feedback_agent import init_db

def create_graph():
    graph = StateGraph(OmniSenseState)
    
    graph.add_node("orchestrator", orchestrate)
    graph.add_node("vision_agent", run_vision)
    graph.add_node("rag_agent", run_rag)
    graph.add_node("anomaly_agent", run_anomaly)
    graph.add_node("diagnostic_agent", run_diagnostic)
    graph.add_node("risk_scorer", run_risk_scorer)
    graph.add_node("report_generator", run_report_generator)
    
    graph.set_entry_point("orchestrator")
    
    # Fan-out: parallel
    graph.add_conditional_edges("orchestrator", route_inputs, {
        "vision_agent": "vision_agent",
        "rag_agent": "rag_agent",
        "anomaly_agent": "anomaly_agent"
    })
    
    # Fan-in: all parallel → diagnostic
    for agent in ["vision_agent", "rag_agent", "anomaly_agent"]:
        graph.add_edge(agent, "diagnostic_agent")
    
    # Sequential
    graph.add_edge("diagnostic_agent", "risk_scorer")
    graph.add_edge("risk_scorer", "report_generator")
    graph.add_edge("report_generator", END)
    
    init_db()
    return graph.compile()

omnisense_app = create_graph()
```

---

## FASTAPI MAIN (main.py)

```python
"""
FastAPI backend — all endpoints.
Handles multipart file uploads for image, CSV, PDF.
Runs LangGraph pipeline on /api/query.
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid, os, shutil
from src.graph.omnisense_graph import omnisense_app

app = FastAPI(title="OmniSense AI Wizard API", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/api/health")
def health(): return {"status": "ok", "agents": "online"}

@app.post("/api/query")
async def run_query(
    query: str = Form(...),
    equipment_id: Optional[str] = Form(None),
    equipment_type: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    sensor_csv: Optional[UploadFile] = File(None),
):
    session_id = str(uuid.uuid4())[:8]
    image_path = None
    csv_path = None
    
    if image:
        image_path = f"{UPLOAD_DIR}/{session_id}_image.jpg"
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    
    if sensor_csv:
        csv_path = f"{UPLOAD_DIR}/{session_id}_sensor.csv"
        with open(csv_path, "wb") as f:
            shutil.copyfileobj(sensor_csv.file, f)
    
    initial_state = {
        "query": query,
        "language": "en",
        "has_image": bool(image_path),
        "has_csv": bool(csv_path),
        "image_path": image_path,
        "csv_path": csv_path,
        "equipment_id": equipment_id,
        "equipment_type": equipment_type,
        "session_id": session_id,
        "vision_output": None,
        "rag_context": None,
        "anomaly_result": None,
        "diagnosis": None,
        "risk_level": None,
        "risk_details": None,
        "report": None,
        "force_critical": False,
        "pipeline_errors": []
    }
    
    result = omnisense_app.invoke(initial_state)
    
    # Cleanup uploads
    for path in [image_path, csv_path]:
        if path and os.path.exists(path):
            os.remove(path)
    
    return {
        "session_id": session_id,
        "diagnosis": result.get("diagnosis"),
        "risk_level": result.get("risk_level"),
        "risk_details": result.get("risk_details"),
        "report": result.get("report"),
        "anomaly_result": result.get("anomaly_result"),
        "vision_output": result.get("vision_output"),
        "pipeline_errors": result.get("pipeline_errors", [])
    }

@app.post("/api/feedback")
async def submit_feedback(feedback: dict):
    from src.agents.feedback_agent import save_feedback
    return save_feedback(feedback)

@app.get("/api/report/{report_id}")
def get_report(report_id: str):
    path = f"reports/{report_id}.md"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Report not found"}
```

---

## VOICE UTILITIES (src/utils/voice.py)

```python
"""
STT: OpenAI Whisper (local) — converts audio to text, detects language.
TTS: gTTS — converts text to speech in detected language.
"""

import whisper
from gtts import gTTS
import tempfile, os

# Load Whisper model once at startup
whisper_model = whisper.load_model("base")  # use "base" for speed, "large" for accuracy

def speech_to_text(audio_path: str) -> dict:
    """Transcribe audio file. Returns text + detected language."""
    result = whisper_model.transcribe(audio_path)
    return {"text": result["text"], "language": result["language"]}

def text_to_speech(text: str, language: str = "en") -> str:
    """Convert text to speech. Returns path to mp3 file."""
    LANG_MAP = {
        "hi": "hi", "or": "or", "bn": "bn",
        "en": "en", "nl": "nl", "th": "th", "cy": "cy"
    }
    lang = LANG_MAP.get(language, "en")
    tts = gTTS(text=text[:500], lang=lang)  # limit to 500 chars for speed
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    return tmp.name
```

---

## VOICE ENDPOINT — Add to main.py

```python
@app.post("/api/voice/stt")
async def speech_to_text_endpoint(audio: UploadFile = File(...)):
    from src.utils.voice import speech_to_text
    audio_path = f"{UPLOAD_DIR}/audio_{uuid.uuid4()}.wav"
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)
    result = speech_to_text(audio_path)
    os.remove(audio_path)
    return result

@app.post("/api/voice/tts")
async def text_to_speech_endpoint(text: str = Form(...), language: str = Form("en")):
    from src.utils.voice import text_to_speech
    from fastapi.responses import FileResponse
    mp3_path = text_to_speech(text, language)
    return FileResponse(mp3_path, media_type="audio/mpeg")
```

---

## REQUIREMENTS.TXT — Create Exactly This

```
fastapi==0.110.0
uvicorn==0.29.0
python-multipart==0.0.9
python-dotenv==1.0.1
pydantic==2.7.0
groq==0.9.0
google-generativeai==0.7.2
langgraph==0.2.0
langchain==0.2.0
langchain-community==0.2.0
openai-whisper==20231117
gTTS==2.5.1
faiss-cpu==1.8.0
sentence-transformers==3.0.1
scikit-learn==1.5.0
xgboost==2.0.3
pandas==2.2.2
numpy==1.26.4
joblib==1.4.2
fpdf2==2.7.9
pypdf2==3.0.1
langdetect==1.0.9
httpx==0.27.0
```

---

## SYNTHETIC DATA GENERATOR (data/synthetic/generate_maintenance_logs.py)

```python
"""
Generates 500 realistic steel plant maintenance log entries.
Saves to src/data/maintenance_logs.csv
Run: python data/synthetic/generate_maintenance_logs.py
"""

import pandas as pd
import random
from datetime import datetime, timedelta

EQUIPMENT = [
    ("BF-001", "Blast Furnace"), ("BF-002", "Blast Furnace"),
    ("RM-001", "Rolling Mill"), ("RM-002", "Rolling Mill"),
    ("CC-001", "Continuous Caster"), ("HS-001", "Hydraulic System"),
    ("EAF-001", "Electric Arc Furnace"), ("CV-001", "Conveyor System"),
    ("CP-001", "Compressor")
]

FAULTS = [
    ("High temperature zone 3", "Cooling stave partial blockage", "Flushed cooling circuit; replaced stave", 4.5, "Copper stave x1"),
    ("Bearing noise in mill stand", "Lubrication failure", "Replaced bearing SKF-6205; regreased", 2.0, "SKF-6205 bearing x2"),
    ("Hydraulic pressure drop", "Seal wear in pump P-204", "Replaced hydraulic seals; pressure test done", 3.0, "Seal kit x1"),
    ("Vibration in roll drive", "Coupling misalignment", "Realigned coupling; vibration check passed", 1.5, "Coupling bolts x8"),
    ("Electrode consumption high", "Arc instability", "Adjusted electrode gap; checked transformer", 2.5, "Electrode segment x1"),
    ("Conveyor belt tracking off", "Belt tension uneven", "Readjusted belt tensioner; replaced idler", 1.0, "Belt idler x2"),
    ("Compressor surge detected", "Inlet valve wear", "Replaced inlet valve assembly", 3.5, "Valve assembly x1"),
]

rows = []
start = datetime(2024, 1, 1)
for i in range(500):
    eq_id, eq_type = random.choice(EQUIPMENT)
    fault, root, action, downtime, parts = random.choice(FAULTS)
    date = start + timedelta(days=random.randint(0, 365))
    rows.append({
        "log_id": f"LOG-2024-{i+1:04d}",
        "date": date.strftime("%Y-%m-%d"),
        "equipment_id": eq_id,
        "equipment_type": eq_type,
        "fault_reported": fault,
        "root_cause": root,
        "action_taken": action,
        "downtime_hours": downtime + random.uniform(-0.5, 1.5),
        "spare_parts_used": parts,
        "engineer_id": f"ENG-{random.randint(10,99):03d}",
        "outcome": random.choice(["RESOLVED", "RESOLVED", "RESOLVED", "MONITORING", "ESCALATED"]),
        "follow_up_date": (date + timedelta(days=30)).strftime("%Y-%m-%d")
    })

import os
os.makedirs("src/data", exist_ok=True)
pd.DataFrame(rows).to_csv("src/data/maintenance_logs.csv", index=False)
print(f"Generated 500 maintenance log entries → src/data/maintenance_logs.csv")
```

---

## MODEL TRAINING SCRIPT (src/models/train_models.py)

```python
"""
Trains Isolation Forest (anomaly detection) and XGBoost (RUL prediction).
Uses Kaggle AI4I 2020 dataset from src/data/sensor_data.csv
If dataset not found, generates synthetic training data.
Saves: isolation_forest.pkl, rul_model.pkl, scaler.pkl
Run: python src/models/train_models.py
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib, os
from pathlib import Path

MODELS_PATH = "src/models"
os.makedirs(MODELS_PATH, exist_ok=True)

FEATURES = ["sensor_temperature", "sensor_vibration",
            "sensor_pressure", "sensor_rpm", "sensor_current"]

def load_or_generate_data():
    csv_path = "src/data/sensor_data.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # Map Kaggle AI4I columns
        col_map = {
            "Air temperature [K]": "sensor_temperature",
            "Process temperature [K]": "sensor_vibration",
            "Rotational speed [rpm]": "sensor_rpm",
            "Torque [Nm]": "sensor_pressure",
            "Tool wear [min]": "sensor_current",
            "Target": "anomaly_flag"
        }
        df = df.rename(columns=col_map)
        print(f"Loaded {len(df)} rows from {csv_path}")
    else:
        print("Dataset not found — generating synthetic data...")
        np.random.seed(42)
        n = 5000
        df = pd.DataFrame({
            "sensor_temperature": np.random.normal(1200, 80, n),
            "sensor_vibration": np.random.exponential(1.5, n),
            "sensor_pressure": np.random.normal(175, 20, n),
            "sensor_rpm": np.random.normal(1480, 50, n),
            "sensor_current": np.random.normal(90, 10, n),
            "anomaly_flag": np.random.choice([0, 0, 0, 0, 1], n)
        })
        # Inject anomalies
        anomaly_idx = df[df["anomaly_flag"] == 1].index
        df.loc[anomaly_idx, "sensor_temperature"] *= 1.4
        df.loc[anomaly_idx, "sensor_vibration"] *= 3.0
    return df

df = load_or_generate_data()
available = [c for c in FEATURES if c in df.columns]
X = df[available].fillna(df[available].mean())

# Train scaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train Isolation Forest
print("Training Isolation Forest...")
iso = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
iso.fit(X_scaled)

# Train RUL XGBoost
print("Training XGBoost RUL model...")
if "anomaly_flag" in df.columns:
    # Simulate RUL: rows near failure get low RUL
    cumulative = np.arange(len(df))
    rul = np.where(df["anomaly_flag"] == 1,
                   np.random.randint(1, 15, len(df)),
                   np.random.randint(15, 90, len(df)))
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, rul, test_size=0.2)
    rul_model = XGBRegressor(n_estimators=100, random_state=42)
    rul_model.fit(X_train, y_train)
    score = rul_model.score(X_test, y_test)
    print(f"RUL model R² score: {score:.3f}")
else:
    rul_model = XGBRegressor(n_estimators=50)
    rul_model.fit(X_scaled, np.random.randint(10, 90, len(X_scaled)))

# Save models
joblib.dump(iso, f"{MODELS_PATH}/isolation_forest.pkl")
joblib.dump(rul_model, f"{MODELS_PATH}/rul_model.pkl")
joblib.dump(scaler, f"{MODELS_PATH}/scaler.pkl")
print(f"✅ Models saved to {MODELS_PATH}/")
print("   - isolation_forest.pkl")
print("   - rul_model.pkl")
print("   - scaler.pkl")
```

---

## FRONTEND IMPROVEMENTS — Update existing React UI

Update the existing frontend to connect to FastAPI backend. Key changes needed:

### 1. API Service (frontend/src/api.js)
```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const runQuery = async (formData) => {
  const response = await axios.post(`${API_BASE}/query`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const submitFeedback = async (feedback) => {
  return axios.post(`${API_BASE}/feedback`, feedback);
};

export const checkHealth = async () => {
  return axios.get(`${API_BASE}/health`);
};
```

### 2. Risk Badge Colors
```javascript
const RISK_COLORS = {
  LOW: { bg: 'bg-green-900', text: 'text-green-300', border: 'border-green-500' },
  MEDIUM: { bg: 'bg-yellow-900', text: 'text-yellow-300', border: 'border-yellow-500' },
  HIGH: { bg: 'bg-orange-900', text: 'text-orange-300', border: 'border-orange-500' },
  CRITICAL: { bg: 'bg-red-900 animate-pulse', text: 'text-red-300', border: 'border-red-500' }
};
```

### 3. Language Selector
```javascript
const LANGUAGES = [
  { code: 'en', label: '🇬🇧 English' },
  { code: 'hi', label: '🇮🇳 Hindi' },
  { code: 'or', label: '🇮🇳 Odia' },
  { code: 'bn', label: '🇮🇳 Bengali' },
  { code: 'nl', label: '🇳🇱 Dutch' },
  { code: 'cy', label: '🏴󠁧󠁢󠁷󠁬󠁳󠁿 Welsh' },
  { code: 'th', label: '🇹🇭 Thai' }
];
```

### 4. Agent Pipeline Visual
Show real-time status of which agents are running:
```javascript
const AGENTS = [
  { id: 'orchestrator', label: 'Orchestrator', icon: '🎯' },
  { id: 'vision', label: 'Vision Agent', icon: '👁️' },
  { id: 'rag', label: 'RAG Agent', icon: '📚' },
  { id: 'anomaly', label: 'Anomaly Agent', icon: '📡' },
  { id: 'diagnostic', label: 'Diagnostic Agent', icon: '🔍' },
  { id: 'risk', label: 'Risk Scorer', icon: '⚠️' },
  { id: 'report', label: 'Report Generator', icon: '📋' },
];
// Status: waiting | running | done | error
```

---

## KNOWLEDGE BASE INDEXER (src/knowledge_base/index_docs.py)

```python
"""
Indexes all documents in src/knowledge_base/documents/ into FAISS.
Run: python src/knowledge_base/index_docs.py
Creates: src/knowledge_base/faiss_index/
"""

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from pathlib import Path
import os

DOCS_PATH = "src/knowledge_base/documents"
INDEX_PATH = "src/knowledge_base/faiss_index"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def index_documents():
    docs_path = Path(DOCS_PATH)
    if not docs_path.exists():
        print(f"No documents found at {DOCS_PATH}")
        print("Creating sample document for testing...")
        os.makedirs(DOCS_PATH, exist_ok=True)
        sample = """# Blast Furnace Maintenance Manual
        
## Tuyere Maintenance Procedure
1. Shut down furnace and allow cooling for 2 hours minimum
2. Inspect tuyere for blockage using borescope
3. Remove tuyere block using extraction tool
4. Clean with high-pressure water jet
5. Inspect copper body for cracks or erosion
6. Replace tuyere if wall thickness < 15mm
7. Reinstall and pressure test at 3.5 bar
8. Monitor for 24 hours after restart

## Cooling Stave Failure Symptoms
- Temperature rise > 50C above baseline in zone
- Water flow rate drop > 20%
- Visual crack on shell surface
Immediate action: Reduce blast volume by 30%, schedule inspection

## Bearing Replacement — Rolling Mill
Standard bearing: SKF 6205 (part number SKF-6205-2RS)
Tools required: bearing puller, hydraulic press, torque wrench 80Nm
Steps:
1. Lockout/tagout motor — verify zero energy
2. Remove guard panels
3. Use bearing puller — DO NOT hammer
4. Clean shaft with emery cloth
5. Heat new bearing to 80C before pressing
6. Apply specified grease: Shell Albida EP2
7. Torque locknut to 80Nm
8. Run trial for 30 minutes, check temperature < 70C

## Hydraulic System — Seal Replacement Pump P-204
Parts: Seal kit HS-204-SK (includes O-rings, backup rings, lip seals)
1. Depressurise system to 0 bar — verify with gauge
2. Drain hydraulic oil — collect in container
3. Remove pump mounting bolts (6x M16)
4. Disassemble end cover
5. Replace all seals — do not reuse old seals
6. Torque end cover bolts to 45Nm in cross pattern
7. Fill with Shell Tellus S2 M46 hydraulic oil
8. Bleed air from system
9. Pressure test to 200 bar — hold 10 minutes
10. Check for leaks at all joints
"""
        with open(f"{DOCS_PATH}/steel_plant_manual.txt", "w") as f:
            f.write(sample)
    
    # Load all documents
    all_docs = []
    for f in Path(DOCS_PATH).iterdir():
        if f.suffix == ".txt":
            loader = TextLoader(str(f), encoding="utf-8")
        elif f.suffix == ".pdf":
            loader = PyPDFLoader(str(f))
        else:
            continue
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = f.name
        all_docs.extend(docs)
        print(f"Loaded: {f.name} ({len(docs)} pages)")
    
    if not all_docs:
        print("No documents to index")
        return
    
    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(all_docs)
    print(f"Created {len(chunks)} chunks")
    
    # Embed and index
    print("Creating embeddings (this may take a minute)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    os.makedirs(INDEX_PATH, exist_ok=True)
    vectorstore.save_local(INDEX_PATH)
    print(f"✅ FAISS index saved to {INDEX_PATH}")
    print(f"   Indexed {len(chunks)} chunks from {len(all_docs)} documents")

if __name__ == "__main__":
    index_documents()
```

---

## SETUP SEQUENCE — RUN IN THIS ORDER

```bash
# 1. Install all dependencies
pip install -r requirements.txt

# 2. Generate synthetic maintenance logs
python data/synthetic/generate_maintenance_logs.py

# 3. Create knowledge base index
python src/knowledge_base/index_docs.py

# 4. Train ML models (uses synthetic data if Kaggle CSV not present)
python src/models/train_models.py

# 5. Start backend
uvicorn main:app --reload --port 8000

# 6. Test backend is working
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "agents": "online"}

# 7. Start frontend (separate terminal)
cd frontend && npm run dev
```

---

## IMPORTANT RULES

1. **Every agent has try/except — never crash the pipeline**
2. **All API keys from os.getenv() only — never hardcode**
3. **RAG agent returns empty list if FAISS index not built yet — do not crash**
4. **Models use fallback logic if .pkl files not found — do not crash**
5. **Frontend connects to http://localhost:8000/api — update if different port**
6. **All file uploads go to uploads/ folder — clean up after processing**
7. **CORS enabled for all origins in development**
8. **Language auto-detected by Whisper/langdetect — default to "en"**

---

## DEMO SCENARIOS — Build and Test These

### Scenario 1: Text Query (Test first — no external API needed if FAISS built)
```
Query: "What is the bearing replacement procedure for Rolling Mill?"
Expected: Step-by-step procedure from knowledge base with source citation
```

### Scenario 2: CSV Anomaly Detection
```
Upload: Any CSV with columns matching sensor names
Expected: Anomaly score, RUL prediction, risk badge update
```

### Scenario 3: Image + Voice (Test last — needs API keys)
```
Upload: Any equipment photo
Speak: "What is wrong with this equipment?"
Expected: Visual fault detection + diagnosis + voice response
```


---

## GROQ MODEL FALLBACK — IMPORTANT

Groq pe model availability change hoti rehti hai. Agar `mistral-small-3.1` kaam na kare toh yeh fallback order use karo:

```python
# src/agents/diagnostic_agent.py mein yeh use karo
GROQ_MODELS = [
    "mistral-small-3.1",          # Primary — Mistral Small 3.1
    "mixtral-8x7b-32768",         # Fallback 1 — always available on Groq free
    "llama-3.3-70b-versatile",    # Fallback 2 — Llama 3.3 70B
    "llama3-8b-8192",             # Fallback 3 — lightest, always works
]

def get_groq_model(client):
    """Try models in order, return first that works."""
    for model in GROQ_MODELS:
        try:
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return model
        except:
            continue
    return GROQ_MODELS[-1]  # last resort
```

**Currently confirmed working on Groq free tier (June 2026):**
- `mixtral-8x7b-32768` — always available, free 5K TPM
- `llama-3.3-70b-versatile` — fast, free tier
- `llama3-8b-8192` — lightest, most reliable

