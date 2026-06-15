"""
OmniSense AI Wizard — Diagnostic Agent
Core reasoning engine using Mistral Small via Groq API (FREE).
Combines vision + RAG + anomaly into structured diagnosis.
Responds in engineer's detected language (8 languages supported).
"""

import json
import logging
import os
import re
from groq import Groq
from langchain_openai import ChatOpenAI
from src.schemas import OmniSenseState
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)

DEFAULT_GROQ_MODELS = [
    "mistral-small-3.1",
    "mixtral-8x7b-32768",
    "llama-3.3-70b-versatile",
    "llama3-8b-8192",
]
DEFAULT_MISTRAL_MODEL = "mistral-small-latest"

SYSTEM_PROMPT = """You are OmniSense AI Wizard — an expert industrial maintenance diagnostic system for Tata Steel manufacturing plants.

You have deep expertise in:
- Blast Furnaces (tuyere, cooling staves, refractory, hot blast system)
- Rolling Mills (bearings, rolls, hydraulic systems, cooling, drive trains)
- Continuous Casters (mold, strand guide, cooling, breakout prediction)
- Electric Arc Furnaces (electrodes, transformers, cooling systems)
- Hydraulic Systems (pumps, valves, seals, accumulators)
- Conveyor Systems (belts, idlers, pulleys, drives)
- Compressors (valves, bearings, seals, cooling)

You support 76,000+ Tata Steel engineers across India, Netherlands, UK, and Thailand.

Synthesize ALL provided information (visual evidence, knowledge base, sensor data) and return ONLY valid JSON:
{
  "fault_identified": "specific fault description — be precise",
  "root_cause": "technical root cause explanation",
  "confidence": 0.0-1.0,
  "repair_steps": [
    "Step 1: First action with specific details",
    "Step 2: Second action",
    "Step 3: Continue..."
  ],
  "immediate_actions": [
    "Action to take RIGHT NOW within next 30 minutes"
  ],
  "spare_parts_needed": [
    {"name": "Part name", "quantity": 1, "part_number": "SKF-XXXX", "urgency": "immediate|scheduled"}
  ],
  "estimated_repair_time": "X-Y hours",
  "safety_precautions": [
    "Safety step 1",
    "Safety step 2"
  ],
  "sources_cited": ["Document name - relevant section"],
  "long_term_recommendations": "Preventive measures to avoid recurrence",
  "maintenance_category": "corrective|preventive|predictive",
  "shutdown_required": true/false
}

RULES:
1. Be specific — vague answers are useless to a field engineer
2. Always include safety precautions for steel plant environment
3. Cite which knowledge base document supports your diagnosis
4. If confidence < 0.5, clearly say manual expert inspection needed
5. ALWAYS respond strictly in English, regardless of the input language
6. Technical part numbers/model names stay in English always
"""

def _get_groq_client():
    """Get Groq API client using environment variable."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables.")
    return Groq(api_key=api_key)


def _get_mistral_llm() -> ChatOpenAI:
    """Get Mistral chat client using environment variable."""
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set in environment variables.")
    return ChatOpenAI(
        api_key=api_key,
        base_url="https://api.mistral.ai/v1",
        model=os.getenv("MISTRAL_CHAT_MODEL", DEFAULT_MISTRAL_MODEL),
        temperature=0.1,
    )


def _get_diagnostic_models() -> list[str]:
    """Return the configured diagnostic model fallback list."""
    configured = os.getenv("DIAGNOSTIC_MODELS", "").strip()
    if configured:
        models = [model.strip() for model in configured.split(",") if model.strip()]
        if models:
            return models

    single_model = os.getenv("DIAGNOSTIC_MODEL", "").strip()
    if single_model:
        return [single_model]

    return DEFAULT_GROQ_MODELS

def _try_groq_models(client, messages):
    """Try Groq models in fallback order."""
    last_error = None
    for model in _get_diagnostic_models():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=2500,
            )
            logger.info(f"Diagnostic Agent using model: {model}")
            return response.choices[0].message.content or ""
        except Exception as e:
            last_error = e
            logger.warning(f"Model {model} failed: {e}, trying next...")
            continue
    raise RuntimeError(f"All Groq models failed. Last error: {last_error}")


def _try_mistral_model(messages: list[dict]) -> str:
    """Call Mistral chat as fallback for diagnosis generation."""
    import time
    llm = _get_mistral_llm()
    try:
        response = llm.invoke(messages)
    except Exception as e:
        if "429" in str(e) or "rate" in str(e).lower():
            logger.info("Rate limit hit in diagnostic, sleeping for 2 seconds and retrying...")
            time.sleep(2)
            response = llm.invoke(messages)
        else:
            raise
    
    if isinstance(response.content, str):
        return response.content
    return json.dumps(response.content)


def _generate_diagnostic_response(messages: list[dict]) -> str:
    """Try Groq first, then fall back to Mistral chat."""
    last_error = None

    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_api_key:
        try:
            client = _get_groq_client()
            return _try_groq_models(client, messages)
        except Exception as exc:
            last_error = exc
            logger.warning("Diagnostic Groq provider failed: %s", exc)

    mistral_api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if mistral_api_key:
        try:
            return _try_mistral_model(messages)
        except Exception as exc:
            last_error = exc
            logger.warning("Diagnostic Mistral provider failed: %s", exc)

    if last_error:
        raise RuntimeError(f"All diagnostic providers failed. Last error: {last_error}")
    raise RuntimeError("No valid diagnostic provider configured. Set GROQ_API_KEY or MISTRAL_API_KEY.")

def build_diagnostic_context(state: OmniSenseState) -> str:
    """
    Assemble all agent outputs into a single context string for the LLM.

    Combines:
      - Engineer's original query
      - Equipment identification
      - Vision Agent results (if image was provided)
      - RAG knowledge base chunks (top 3)
      - Anomaly Agent sensor data (if CSV was provided)

    Args:
        state: The pipeline state containing all agent outputs.

    Returns:
        str: Formatted multi-section context string.
    """
    parts = [f"ENGINEER QUERY: {state.get('query', 'No query provided')}"]
    
    if state.get("equipment_id"):
        equip = f"EQUIPMENT ID: {state['equipment_id']}"
        if state.get("equipment_type"):
            equip += f" | TYPE: {state['equipment_type']}"
        parts.append(equip)

    vision = state.get("vision_output")
    if vision and vision.get("fault_detected"):
        observations = ", ".join(vision.get("visual_observations", []))
        parts.append(
            f"VISUAL INSPECTION RESULTS:\n"
            f"- Fault Type: {vision.get('fault_type', 'unknown')}\n"
            f"- Affected Component: {vision.get('affected_component', 'unknown')}\n"
            f"- Severity: {vision.get('severity', 'unknown')}\n"
            f"- Observations: {observations}\n"
            f"- Confidence: {vision.get('confidence', 0.0):.0%}"
        )

    rag_context = state.get("rag_context")
    if rag_context:
        parts.append("KNOWLEDGE BASE (Equipment Manuals & SOPs):")
        for chunk in rag_context[:3]:
            source = chunk.get("source", "unknown")
            page = chunk.get("page", 0)
            content = chunk.get("content", "")[:600]
            parts.append(f"[{source} | Page {page}]\n{content}")

    anomaly = state.get("anomaly_result")
    if anomaly and anomaly.get("anomaly_detected"):
        parts.append(
            f"SENSOR ANOMALY DETECTED:\n"
            f"- Anomaly Score: {anomaly.get('anomaly_score', 0.0):.3f} (threshold: 0.6)\n"
            f"- Most Affected Sensor: {anomaly.get('anomalous_sensor', 'unknown')}\n"
            f"- Current Value: {anomaly.get('current_value', 'N/A')}\n"
            f"- Normal Range: {anomaly.get('normal_range', 'N/A')}\n"
            f"- Remaining Useful Life: {anomaly.get('rul_days', 'N/A')} days\n"
            f"- Alert Triggered: {anomaly.get('alert_triggered', False)}"
        )

    return "\n\n---\n\n".join(parts)

def _parse_response(text: str) -> dict:
    """
    Parse JSON from LLM response, with fallback regex extraction.

    Args:
        text: Raw text from the LLM API.

    Returns:
        dict: Parsed diagnosis dictionary.
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return {
        "fault_identified": "Could not parse AI response",
        "root_cause": "Response parsing failed",
        "confidence": 0.0,
        "repair_steps": ["Contact senior maintenance engineer"],
        "immediate_actions": ["Manual inspection required"],
        "spare_parts_needed": [],
        "safety_precautions": ["Follow standard safety procedures"],
        "estimated_repair_time": "Unknown",
        "sources_cited": [],
        "long_term_recommendations": "",
        "maintenance_category": "corrective",
        "shutdown_required": False,
        "error": "JSON parse failed"
    }

def _normalize(diagnosis: dict, language: str) -> dict:
    """
    Ensure all required DiagnosisOutput fields exist with valid types.

    Args:
        diagnosis: Raw parsed diagnosis from LLM.
        language: ISO 639-1 language code for the response.

    Returns:
        dict: Normalized, schema-compliant diagnosis dictionary.
    """
    defaults = {
        "fault_identified": "Unknown fault",
        "root_cause": "Unknown",
        "confidence": 0.5,
        "repair_steps": [],
        "immediate_actions": [],
        "spare_parts_needed": [],
        "safety_precautions": [],
        "estimated_repair_time": "Unknown",
        "sources_cited": [],
        "long_term_recommendations": "",
        "maintenance_category": "corrective",
        "shutdown_required": False,
        "language": language,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in diagnosis:
            diagnosis[k] = v
    diagnosis["language"] = language
    try:
        diagnosis["confidence"] = max(0.0, min(1.0, float(diagnosis["confidence"])))
    except:
        diagnosis["confidence"] = 0.0
    for f in ("repair_steps", "immediate_actions", "spare_parts_needed", 
              "safety_precautions", "sources_cited"):
        if not isinstance(diagnosis.get(f), list):
            diagnosis[f] = []
    return diagnosis

def run_diagnostic(state: OmniSenseState) -> OmniSenseState:
    """
    Core diagnostic reasoning using Mistral via Groq API.

    Produces a structured maintenance diagnosis by combining all
    available agent outputs (vision, RAG context, anomaly data).

    Error handling:
        - ``json.JSONDecodeError``: falls back to regex extraction.
        - Any other exception: returns a safe "manual inspection
          required" diagnosis so the pipeline can continue.

    Args:
        state: The shared LangGraph pipeline state.

    Returns:
        OmniSenseState: Updated state with ``diagnosis`` populated.
    """
    # Extract tool call
    messages = state.get("messages", [])
    if not messages: return {}
    last_msg = messages[-1]
    
    tool_call_id = None
    if hasattr(last_msg, "tool_calls"):
        for tc in last_msg.tool_calls:
            if tc["name"] == "run_diagnostic":
                tool_call_id = tc["id"]
                break
                
    if not tool_call_id:
        return {}

    updates = {"agent_status": "Synthesizing findings for root cause analysis..."}

    try:
        language = state.get("language", "en")
        context = build_diagnostic_context(state)
        
        system = SYSTEM_PROMPT + f"\n\nRESPOND IN THIS LANGUAGE: {language}\nTechnical terms may stay in English."

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": context}
        ]

        response_text = _generate_diagnostic_response(messages)
        diagnosis = _parse_response(response_text)
        diagnosis = _normalize(diagnosis, language)
        updates["diagnosis"] = diagnosis
        
        # Append ToolMessage
        tool_msg = ToolMessage(
            tool_call_id=tool_call_id,
            name="run_diagnostic",
            content=f"Diagnosis Complete: {json.dumps(diagnosis)}"
        )
        updates["messages"] = [tool_msg]

        logger.info(
            "Diagnosis complete — fault='%s' confidence=%.2f shutdown_required=%s",
            diagnosis.get("fault_identified", "N/A"),
            diagnosis.get("confidence", 0.0),
            diagnosis.get("shutdown_required", False)
        )

    except Exception as exc:
        logger.error("Diagnostic Agent failed: %s", exc, exc_info=True)
        updates["diagnosis"] = {
            "fault_identified": "Diagnosis failed — manual inspection required",
            "root_cause": f"System error: {str(exc)}",
            "confidence": 0.0,
            "repair_steps": ["Contact on-site senior maintenance engineer"],
            "immediate_actions": ["Isolate equipment if safety risk suspected"],
            "spare_parts_needed": [],
            "safety_precautions": ["Follow LOTO procedures"],
            "estimated_repair_time": "Unknown",
            "sources_cited": [],
            "long_term_recommendations": "",
            "maintenance_category": "corrective",
            "shutdown_required": False,
            "language": state.get("language", "en"),
            "error": str(exc),
        }
        updates["messages"] = [ToolMessage(tool_call_id=tool_call_id, name="run_diagnostic", content=f"Diagnostic Agent failed: {exc}")]
        
    updates["agent_status"] = "Diagnosis ready."
    return updates
