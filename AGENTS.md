# OmniSense AI Wizard — AGENTS.md
> Antigravity Project Instructions | Tata Steel AI Hackathon 2026

## Project Overview
OmniSense AI Wizard is a **Multimodal Multi-Agent AI Maintenance Decision Support System** for steel plant industrial equipment. It accepts Voice + Image + Text + CSV + PDF as inputs and delivers fault diagnosis, root cause analysis, risk scoring, RUL prediction, and structured maintenance reports as outputs.

**GitHub:** `omnisense-ai-wizard`  
**Tagline:** *"See it. Say it. Solve it."*

---

## Tech Stack — Complete
| Layer | Tool | Version |
|---|---|---|
| Agent Framework | LangGraph | 0.2.x |
| Core LLM | Mistral Small 3.1 | latest |
| Vision LLM | Gemini 1.5 Flash | Google AI |
| STT | OpenAI Whisper | large-v3 (local) |
| TTS | gTTS | Python lib |
| Vector DB | FAISS | 1.7.x |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | local |
| Anomaly Detection | Isolation Forest | scikit-learn |
| RUL Prediction | XGBoost | latest |
| Backend | FastAPI | 0.110.x |
| Frontend | React 18 + Tailwind CSS | latest |
| Database | SQLite | built-in |
| Container | Docker | latest |

---

## Project Structure
```
omnisense-ai-wizard/
├── AGENTS.md                    ← You are here
├── README.md
├── requirements.txt
├── Dockerfile
├── .env.example
├── main.py                      ← FastAPI entry point
├── agents/
│   ├── orchestrator.md          ← Read when building orchestrator.py
│   ├── vision_agent.md          ← Read when building vision_agent.py
│   ├── rag_agent.md             ← Read when building rag_agent.py
│   ├── diagnostic_agent.md      ← Read when building diagnostic_agent.py
│   ├── anomaly_agent.md         ← Read when building anomaly_agent.py
│   ├── risk_scorer.md           ← Read when building risk_scorer.py
│   ├── report_generator.md      ← Read when building report_generator.py
│   └── feedback_agent.md        ← Read when building feedback_agent.py
├── references/
│   ├── schemas.md               ← ALWAYS read first — all TypedDict schemas
│   ├── api_guide.md             ← API keys setup guide
│   └── data_guide.md            ← Dataset descriptions
├── assets/
│   └── prompts.md               ← All LLM system prompts library
├── src/
│   ├── agents/                  ← Agent Python files go here
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
│   │   └── omnisense_graph.py   ← LangGraph DAG definition
│   ├── models/
│   │   ├── isolation_forest.pkl ← Trained anomaly model
│   │   └── rul_model.pkl        ← Trained RUL model
│   ├── knowledge_base/
│   │   ├── documents/           ← PDF/TXT knowledge docs
│   │   └── faiss_index/         ← FAISS vector index
│   ├── data/
│   │   ├── sensor_data.csv      ← Kaggle AI4I dataset
│   │   └── maintenance_logs.csv ← Synthetic maintenance logs
│   └── utils/
│       ├── embeddings.py
│       ├── voice.py
│       └── vision.py
└── frontend/
    └── src/                     ← React frontend
```

---

## Environment Variables (.env)
```bash
GROQ_API_KEY=your_groq_api_key          # https://console.groq.com (free)
GOOGLE_API_KEY=your_google_api_key      # https://aistudio.google.com (free)
MISTRAL_API_KEY=your_mistral_api_key    # https://console.mistral.ai (free)
```

---

## LangGraph Shared State Schema
**ALWAYS import from references/schemas.md before writing any agent code.**
```python
class OmniSenseState(TypedDict):
    # Input
    query: str
    language: str                    # detected language code: hi/or/bn/en/nl/th
    has_image: bool
    has_csv: bool
    has_docs: bool
    image_path: Optional[str]
    csv_path: Optional[str]
    
    # Agent Outputs
    vision_output: Optional[dict]
    rag_context: Optional[list]
    anomaly_result: Optional[dict]
    diagnosis: Optional[dict]
    risk_level: Optional[str]        # LOW/MEDIUM/HIGH/CRITICAL
    report: Optional[str]
    
    # Meta
    equipment_id: Optional[str]
    equipment_type: Optional[str]
    session_id: str
    feedback: Optional[dict]
```

---

## Agent Roster — 8 Agents
| Agent | File | When to Call |
|---|---|---|
| Orchestrator | orchestrator.py | Always — entry point |
| Vision Agent | vision_agent.py | has_image == True |
| RAG Agent | rag_agent.py | Always |
| Diagnostic Agent | diagnostic_agent.py | Always — after Vision+RAG |
| Anomaly Agent | anomaly_agent.py | has_csv == True |
| Risk Scorer | risk_scorer.py | After Diagnostic |
| Report Generator | report_generator.py | After Risk Scorer |
| Feedback Agent | feedback_agent.py | After engineer confirms |

---

## Build Order
1. `references/schemas.md` — Read FIRST always
2. `src/agents/rag_agent.py` — Foundation
3. `src/agents/diagnostic_agent.py` — Core brain
4. `src/agents/vision_agent.py` — Image input
5. `src/utils/voice.py` — STT + TTS
6. `src/agents/anomaly_agent.py` — Sensor analysis
7. `src/agents/risk_scorer.py` — Risk classification
8. `src/graph/omnisense_graph.py` — Wire all agents
9. `src/agents/report_generator.py` — Output
10. `src/agents/feedback_agent.py` — Learning loop
11. `main.py` — FastAPI layer
12. `frontend/` — React UI last

---

## Coding Conventions
- Python 3.11+ only
- Type hints mandatory on all functions
- Every agent function returns updated `OmniSenseState`
- No hardcoded API keys — always use `os.getenv()`
- Every function must have a docstring
- Error handling in every agent — never let one agent crash the pipeline
- Agents communicate ONLY through shared state — never direct calls
- Each agent file must be independently testable with `pytest`

---

## Key Rules for Antigravity
1. **Always read `references/schemas.md` before writing any agent**
2. **Always read the relevant `agents/*.md` before writing that agent's .py file**
3. **Never hardcode API keys**
4. **Parallel agents:** Vision + RAG + Anomaly run simultaneously via LangGraph
5. **Language detection:** Whisper auto-detects — pass `language` in state
6. **All LLM prompts:** Get from `assets/prompts.md` — do not write inline
7. **Frontend is LAST** — complete all backend agents first

---

## Quick Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Train ML models
python src/models/train_models.py

# Index knowledge base
python src/knowledge_base/index_docs.py

# Run backend
uvicorn main:app --reload --port 8000

# Run frontend
cd frontend && npm install && npm run dev
```
