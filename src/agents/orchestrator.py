"""
OmniSense AI Wizard — Orchestrator Agent
========================================
Central conversational controller. Routes queries to specialized tools.
"""

import os
import logging
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from src.schemas import OmniSenseState

logger = logging.getLogger(__name__)

DEFAULT_MISTRAL_MODEL = "mistral-small-latest"

# ── Define Agent Tools (Signatures only, logic in agent nodes) ──

@tool
def run_vision(image_path: str = None):
    """Call this tool if the user uploads an image to analyze for physical faults, corrosion, cracks, or leaks."""
    pass

@tool
def run_rag(query: str):
    """Call this tool if you need to search maintenance manuals, SOPs, or historical repair logs for context."""
    pass

@tool
def run_anomaly(equipment_id: str = None):
    """Call this tool if you need to check live sensor data, vibrations, temperature, or predict Remaining Useful Life (RUL)."""
    pass

@tool
def run_diagnostic():
    """Call this tool to synthesize findings from vision/rag/anomaly into a formal root cause analysis and step-by-step repair plan."""
    pass

@tool
def run_risk_scorer():
    """Call this tool to evaluate the safety, operational, and bottleneck risk of a diagnosed fault."""
    pass

@tool
def generate_report():
    """Call this tool ONLY when the user explicitly asks for a formal report or summary to be generated and saved."""
    pass

tools = [run_vision, run_rag, run_anomaly, run_diagnostic, run_risk_scorer, generate_report]


def _build_orchestrator_candidates() -> list[tuple[str, ChatOpenAI]]:
    """Build the Mistral orchestrator candidate."""
    candidates: list[tuple[str, ChatOpenAI]] = []

    mistral_api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if mistral_api_key:
        candidates.append((
            "mistral",
            ChatOpenAI(
                api_key=mistral_api_key,
                base_url="https://api.mistral.ai/v1",
                model=os.getenv("MISTRAL_CHAT_MODEL", DEFAULT_MISTRAL_MODEL),
                temperature=0.1,
            ),
        ))

    return candidates

def orchestrate(state: OmniSenseState) -> OmniSenseState:
    """
    Central orchestrator node — routes user queries through sub-agent tools.

    Uses Mistral (or Groq fallback) with tool-calling to decide which
    agents to invoke based on the user's query and available context.

    Args:
        state: The shared LangGraph pipeline state.

    Returns:
        OmniSenseState: Updated state with orchestrator's response appended.
    """
    logger.info("🧠 Orchestrator thinking...")
    
    messages = state.get("messages", [])
    language = state.get("language", "en")

    # ── Build context-aware flags ────────────────────────────
    has_image = state.get("has_image", False)
    has_csv = state.get("has_csv", False)
    has_docs = state.get("has_docs", False)
    equipment_id = state.get("equipment_id") or "Not specified"
    equipment_type = state.get("equipment_type") or "Not specified"

    context_block = f"""
CURRENT SESSION CONTEXT:
- Equipment ID: {equipment_id}
- Equipment Type: {equipment_type}
- Image uploaded: {"YES — you MUST call run_vision to analyze it" if has_image else "No"}
- Sensor CSV uploaded: {"YES — you MUST call run_anomaly to analyze sensor data" if has_csv else "No"}
- Documents/PDFs uploaded: {"YES — you MUST call run_rag to search them" if has_docs else "No"}
- User language: {language}
"""

    # ── System prompt — strong identity + rules ──────────────
    system_prompt = SystemMessage(content=f'''You are **OmniSense AI Wizard**, an AI-powered maintenance decision support assistant built for Tata Steel's 76,000+ engineers across India, Netherlands, UK, and Thailand.

YOUR IDENTITY:
- You are an AI ASSISTANT, NOT a human engineer. Never say "I am a maintenance engineer" or role-play as the user.
- You help engineers diagnose faults, predict failures, and recommend repairs.
- Your name is "OmniSense AI Wizard" or simply "OmniSense".

{context_block}

AVAILABLE TOOLS (sub-agents):
1. `run_vision(image_path)` — Analyze uploaded equipment photos for corrosion, cracks, overheating, wear, leaks.
2. `run_rag(query)` — Search maintenance manuals, SOPs, historical repair logs, and uploaded PDFs.
3. `run_anomaly(equipment_id)` — Analyze uploaded sensor CSV data, detect anomalies, predict Remaining Useful Life (RUL).
4. `run_diagnostic()` — Synthesize all gathered evidence (vision + RAG + anomaly) into structured root cause analysis and repair plan.
5. `run_risk_scorer()` — Calculate weighted risk score after diagnosis is complete.
6. `generate_report()` — Generate formal maintenance report (only when user explicitly requests it).

DECISION RULES:
1. **Greeting / casual chat**: If the user says "hi", "hello", or similar, greet them warmly as OmniSense and ask what equipment issue they need help with. Do NOT invent or assume any fault.
2. **Image provided**: ALWAYS call `run_vision` first to analyze the image.
3. **CSV provided**: ALWAYS call `run_anomaly` to check sensor data.
4. **Documents provided**: ALWAYS call `run_rag` to search the uploaded documents.
5. **Equipment issue described**: Call `run_rag` to search manuals, then call `run_diagnostic` for diagnosis. If the user describes symptoms (vibration, noise, temperature, pressure), also call `run_anomaly` if CSV is available.
6. **After diagnosis**: Call `run_risk_scorer` to assess risk level.
7. **Report request**: Only call `generate_report` when the user explicitly asks for a formal report.

RESPONSE RULES:
- **Language Constraint:** ALWAYS reply strictly in English. Ignore background system language flags. NEVER use other languages like 'nl'.
- **Formatting Constraint:** Structure your answers cleanly like Gemini. Use clean Markdown formatting, use bold text for emphasis, bullet points for lists, and avoid dense, heavy paragraphs. Keep it highly readable for an engineer on the shop floor.
- Be specific and actionable — vague answers are useless to field engineers.
- NEVER hallucinate data, sensor readings, or part numbers. If you don't have information, call the appropriate tool.
- NEVER invent equipment faults that the user has not mentioned.
- NEVER ask the user to upload images, sensor CSV data, or documents. If you have enough info to diagnose, simply say: "Do you have anything else to tell, or shall I generate the whole report?"
''')

    try:
        candidates = _build_orchestrator_candidates()
        if not candidates:
            return {"messages": [AIMessage(content=_fallback_response(state, "No valid Mistral API key configured."))]}

        provider_name, llm = candidates[0]
        logger.info("Orchestrator using provider: %s", provider_name)
        llm_with_tools = llm.bind_tools(tools)
        response = llm_with_tools.invoke([system_prompt] + messages)
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Orchestrator LLM failed: {e}")
        return {"messages": [AIMessage(content=_fallback_response(state, "Mistral request failed."))]}

    return {}


def _fallback_response(state: OmniSenseState, reason: str) -> str:
    """Return a safe maintenance assistant reply when the LLM is unavailable."""
    query = (state.get("query") or "").strip().lower()
    has_image = state.get("has_image", False)
    has_csv = state.get("has_csv", False)
    has_docs = state.get("has_docs", False)
    equipment_id = state.get("equipment_id") or "the equipment"

    if any(word in query for word in ("hi", "hello", "hey")):
        return "Hello, I’m OmniSense. Tell me the equipment ID and symptoms, and I’ll help diagnose it."

    response_parts = [f"I can help with {equipment_id}."]
    if has_image:
        response_parts.append("I have an image to inspect, but I need one more clue to be precise: what exact symptom should I look for, like leak, crack, noise, heat, vibration, or misalignment?")
    if has_csv:
        response_parts.append("I have sensor CSV data to analyze.")
    if has_docs:
        response_parts.append("I have uploaded documents to search.")

    if query:
        response_parts.append("Please share the strongest symptom, error code, or fault clue so I can narrow the diagnosis. If you want, I can also generate a report after that.")
    else:
        response_parts.append("Please describe the issue or upload an image, CSV, or PDF/manual. I can then ask the next best question and build the report.")

    if reason:
        logger.debug("Orchestrator fallback reason: %s", reason)
    return " ".join(response_parts)
