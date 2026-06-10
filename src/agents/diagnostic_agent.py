"""
SteelMind AI Wizard — Diagnostic Agent
=========================================
Core reasoning engine that synthesizes outputs from Vision, RAG,
and Anomaly agents into a structured fault diagnosis using
Mistral Small 3.1 via Groq API.

Spec: agents/diagnostic_agent.md
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from src.schemas import SteelMindState, DiagnosisOutput
from src.prompts import get_prompt

logger = logging.getLogger(__name__)

# ── Model Config ─────────────────────────────────────────────
GROQ_MODEL = "mistral-small-3.1-24b-instruct"


# ══════════════════════════════════════════════════════════════
# Public Entry Point
# ══════════════════════════════════════════════════════════════

def run_diagnostic(state: SteelMindState) -> SteelMindState:
    """
    Produce a structured maintenance diagnosis by combining all
    available agent outputs (vision, RAG context, anomaly data).

    Uses Mistral Small 3.1 via Groq API with JSON response mode.
    Automatically responds in the same language as the engineer's
    query (detected via ``state["language"]``).

    Error handling:
        - ``json.JSONDecodeError``: falls back to regex extraction.
        - Any other exception: returns a safe "manual inspection
          required" diagnosis so the pipeline can continue.

    Args:
        state: The shared LangGraph pipeline state.

    Returns:
        SteelMindState: Updated state with ``diagnosis`` populated.
    """
    try:
        from groq import Groq  # type: ignore[import-untyped]

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment variables.")

        client = Groq(api_key=api_key)

        # Build context from all agent outputs
        context = build_diagnostic_context(state)

        # Build system prompt with multilingual instruction
        language = state.get("language", "en")
        system_prompt = get_prompt("DIAGNOSTIC_AGENT_PROMPT")
        system_prompt += f"\nRespond in language: {language}"
        system_prompt += "\nRespond ONLY in valid JSON."

        # Append multilingual instructions
        try:
            ml_instruction = get_prompt(
                "MULTILINGUAL_INSTRUCTION", language_code=language
            )
            system_prompt += f"\n\n{ml_instruction}"
        except (ValueError, KeyError):
            pass

        logger.info(
            "Diagnostic Agent calling Groq — model=%s, context_len=%d chars",
            GROQ_MODEL,
            len(context),
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
            ],
            temperature=0.1,        # Low temp for consistent structured output
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content or ""

        # Parse JSON response
        try:
            diagnosis = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Groq returned non-JSON — attempting regex fallback.")
            diagnosis = _extract_diagnosis_fallback(response_text)

        # Ensure required fields exist
        diagnosis = _normalize_diagnosis(diagnosis, language)
        state["diagnosis"] = diagnosis

        logger.info(
            "Diagnosis complete — fault=%s, confidence=%.2f",
            diagnosis.get("fault_identified", "N/A"),
            diagnosis.get("confidence", 0.0),
        )

    except Exception as exc:
        logger.error("Diagnostic Agent failed: %s", exc, exc_info=True)
        state["diagnosis"] = {
            "fault_identified": "Diagnosis failed — manual inspection required",
            "root_cause": "Diagnostic system encountered an error",
            "confidence": 0.0,
            "repair_steps": ["Contact on-site maintenance engineer for manual inspection"],
            "immediate_actions": ["Isolate equipment if safety risk is suspected"],
            "spare_parts_needed": [],
            "estimated_repair_time": "Unknown",
            "sources_cited": [],
            "long_term_recommendations": "Investigate diagnostic pipeline error and retry",
            "language": state.get("language", "en"),
            "error": str(exc),
        }

    return state


# ══════════════════════════════════════════════════════════════
# Context Builder
# ══════════════════════════════════════════════════════════════

def build_diagnostic_context(state: SteelMindState) -> str:
    """
    Assemble all agent outputs into a single context string for Mistral.

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
    parts: list[str] = [f"ENGINEER QUERY: {state.get('query', 'No query provided')}"]

    # Equipment context
    if state.get("equipment_id"):
        equip = f"EQUIPMENT: {state['equipment_id']}"
        if state.get("equipment_type"):
            equip += f" ({state['equipment_type']})"
        parts.append(equip)

    # Vision output
    vision = state.get("vision_output")
    if vision and vision.get("fault_detected"):
        observations = ", ".join(vision.get("visual_observations", []))
        parts.append(
            f"VISUAL DIAGNOSIS:\n"
            f"- Fault Type: {vision.get('fault_type', 'unknown')}\n"
            f"- Affected Component: {vision.get('affected_component', 'unknown')}\n"
            f"- Severity: {vision.get('severity', 'unknown')}\n"
            f"- Observations: {observations}\n"
            f"- Confidence: {vision.get('confidence', 0.0)}"
        )

    # RAG context (top 3 chunks for prompt length management)
    rag_context = state.get("rag_context")
    if rag_context:
        parts.append("KNOWLEDGE BASE CONTEXT:")
        for i, chunk in enumerate(rag_context[:3]):
            source = chunk.get("source", "unknown")
            page = chunk.get("page", 0)
            content = chunk.get("content", "")
            parts.append(f"[Source: {source}, Page: {page}]\n{content}")

    # Anomaly data
    anomaly = state.get("anomaly_result")
    if anomaly and anomaly.get("anomaly_detected"):
        parts.append(
            f"SENSOR ANOMALY DATA:\n"
            f"- Anomaly Score: {anomaly.get('anomaly_score', 0.0)}\n"
            f"- Affected Sensor: {anomaly.get('anomalous_sensor', 'unknown')}\n"
            f"- Current Value: {anomaly.get('current_value', 'N/A')}\n"
            f"- Normal Range: {anomaly.get('normal_range', 'N/A')}\n"
            f"- RUL Estimate: {anomaly.get('rul_days', 'N/A')} days"
        )

    return "\n\n".join(parts)


# ══════════════════════════════════════════════════════════════
# Fallback & Normalization
# ══════════════════════════════════════════════════════════════

def _extract_diagnosis_fallback(response_text: str) -> Dict[str, Any]:
    """
    Extract diagnosis data from non-JSON Groq response using regex.

    Attempts to find a JSON block within the response text.
    If that fails, returns a minimal error diagnosis.

    Args:
        response_text: Raw text from the Groq API.

    Returns:
        dict: Best-effort parsed diagnosis dictionary.
    """
    # Try to find JSON within the text
    brace_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    # Return minimal fallback
    return {
        "fault_identified": "Could not parse LLM response — manual inspection required",
        "root_cause": "LLM returned non-structured response",
        "confidence": 0.0,
        "repair_steps": ["Contact maintenance engineer for manual assessment"],
        "immediate_actions": [],
        "spare_parts_needed": [],
        "estimated_repair_time": "Unknown",
        "sources_cited": [],
        "long_term_recommendations": response_text[:500],
        "error": "JSON parse failed",
    }


def _normalize_diagnosis(
    diagnosis: Dict[str, Any], language: str
) -> Dict[str, Any]:
    """
    Ensure all required DiagnosisOutput fields exist with valid types.

    Fills in missing fields with safe defaults so downstream agents
    always receive a consistent dictionary shape.

    Args:
        diagnosis: Raw parsed diagnosis from LLM.
        language: ISO 639-1 language code for the response.

    Returns:
        dict: Normalized, schema-compliant diagnosis dictionary.
    """
    defaults: Dict[str, Any] = {
        "fault_identified": "Unknown fault",
        "root_cause": "Unknown",
        "confidence": 0.5,
        "repair_steps": [],
        "immediate_actions": [],
        "spare_parts_needed": [],
        "estimated_repair_time": "Unknown",
        "sources_cited": [],
        "long_term_recommendations": "",
        "language": language,
        "error": None,
    }

    for key, default in defaults.items():
        if key not in diagnosis:
            diagnosis[key] = default

    # Ensure language is always set
    diagnosis["language"] = language

    # Clamp confidence
    try:
        conf = float(diagnosis["confidence"])
        diagnosis["confidence"] = max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        diagnosis["confidence"] = 0.0

    # Ensure list types
    for list_field in ("repair_steps", "immediate_actions", "spare_parts_needed", "sources_cited"):
        if not isinstance(diagnosis.get(list_field), list):
            diagnosis[list_field] = []

    return diagnosis
