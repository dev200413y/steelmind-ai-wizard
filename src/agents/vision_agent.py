"""
OmniSense AI Wizard — Vision Agent
=====================================
Analyzes uploaded equipment photographs using Mistral vision models
to identify visual faults (corrosion, cracks, overheating, wear, leaks).

Spec: agents/vision_agent.md
"""

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from src.prompts import get_prompt
from src.schemas import OmniSenseState, VisionOutput

logger = logging.getLogger(__name__)

# ── Default fallback when vision fails ───────────────────────
_VISION_FALLBACK: Dict[str, Any] = {
    "fault_detected": False,
    "fault_type": "unknown",
    "affected_component": "unknown",
    "severity": "LOW",
    "visual_observations": [],
    "ocr_text": [],
    "visible_equipment_context": "",
    "immediate_action_required": False,
    "confidence": 0.0,
    "additional_context": "",
    "error": None,
}


# ══════════════════════════════════════════════════════════════
# Public Entry Point
# ══════════════════════════════════════════════════════════════

def run_vision(state: OmniSenseState) -> OmniSenseState:
    """
    Analyze an equipment image using a Mistral vision model.

    Reads the image from ``state["image_paths"]``, sends it to
    Mistral along with the VISION_AGENT_PROMPT, and parses the
    structured JSON response into ``state["vision_output"]``.

    Skips silently (returns state unchanged) when no image is
    provided.  On any error, sets a safe fallback with
    ``fault_detected=False`` so downstream agents can continue.

    Args:
        state: The shared LangGraph pipeline state.

    Returns:
        OmniSenseState: Updated state with ``vision_output`` populated.
    """
    # Extract tool call
    messages = state.get("messages", [])
    if not messages: return {}
    last_msg = messages[-1]
    
    tool_call_id = None
    if hasattr(last_msg, "tool_calls"):
        for tc in last_msg.tool_calls:
            if tc["name"] == "run_vision":
                tool_call_id = tc["id"]
                break
                
    if not tool_call_id:
        return {}

    updates = {}

    # Extract image path (either from state or tool args)
    # The OmniSenseState holds list of image_paths now
    image_paths = state.get("image_paths", [])
    if not image_paths:
        logger.info("Vision Agent skipped — no image provided.")
        updates["messages"] = [ToolMessage(tool_call_id=tool_call_id, name="run_vision", content="No image provided to analyze.")]
        return updates

    # Just take the latest image
    image_path = image_paths[-1]

    try:
        # Validate file exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Read image bytes
        image_data = Path(image_path).read_bytes()
        mime_type = _detect_mime_type(image_path)

        # Build prompt
        prompt = _build_vision_prompt(state)

        # Send image + prompt to Mistral Vision
        logger.info("Sending image to Mistral vision model — %s (%d bytes)", image_path, len(image_data))
        response_text = _call_mistral_vision(prompt, image_data, mime_type)
        updates["vision_output"] = _parse_vision_json(response_text)
        
        # Append ToolMessage
        tool_msg = ToolMessage(
            tool_call_id=tool_call_id,
            name="run_vision",
            content=f"Vision Analysis Result: {json.dumps(updates['vision_output'])}"
        )
        updates["messages"] = [tool_msg]
        
        logger.info(
            "Vision analysis complete — fault=%s, severity=%s, confidence=%.2f",
            updates["vision_output"].get("fault_detected"),
            updates["vision_output"].get("severity"),
            updates["vision_output"].get("confidence", 0.0),
        )

    except Exception as exc:
        logger.error("Vision Agent failed: %s", exc, exc_info=True)
        fallback = dict(_VISION_FALLBACK)
        fallback["error"] = str(exc)
        updates["vision_output"] = fallback
        updates["messages"] = [ToolMessage(tool_call_id=tool_call_id, name="run_vision", content=f"Vision failed: {exc}")]

    return updates


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _build_vision_prompt(state: OmniSenseState) -> str:
    """
    Build the vision analysis prompt with optional equipment context.

    Fetches the base prompt from the prompts library and appends
    equipment type and engineer query when available.

    Args:
        state: Pipeline state with query and equipment info.

    Returns:
        str: Complete prompt for Mistral vision analysis.
    """
    prompt = get_prompt("VISION_AGENT_PROMPT")

    if state.get("equipment_type"):
        prompt += f"\nEquipment Type: {state['equipment_type']}"
    if state.get("query"):
        prompt += f"\nEngineer's description: {state['query']}"

    return prompt


def _call_mistral_vision(prompt: str, image_data: bytes, mime_type: str) -> str:
    """Call Mistral's vision-capable model with the image encoded as a data URL."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set in environment variables.")

    model = os.getenv("MISTRAL_VISION_MODEL", "pixtral-12b-2409")
    image_b64 = base64.b64encode(image_data).decode("ascii")
    data_url = f"data:{mime_type};base64,{image_b64}"

    llm = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.mistral.ai/v1",
        model=model,
        temperature=0.1,
    )

    response = llm.invoke([
        HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]
        )
    ])
    return response.content if isinstance(response.content, str) else json.dumps(response.content)


def _detect_mime_type(image_path: str) -> str:
    """
    Detect MIME type from file extension.

    Args:
        image_path: Path to the image file.

    Returns:
        str: MIME type string (e.g. "image/jpeg").
    """
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return mime_map.get(ext, "image/jpeg")


def _parse_vision_json(response_text: str) -> Dict[str, Any]:
    """
    Parse Mistral's response text into a structured VisionOutput dict.

    Handles three common response formats:
      1. Clean JSON.
      2. JSON wrapped in markdown code fences.
      3. Malformed text — extract what we can with regex.

    Args:
        response_text: Raw text response from Mistral.

    Returns:
        dict: Parsed VisionOutput-compatible dictionary.

    Raises:
        ValueError: If JSON cannot be extracted at all.
    """
    text = response_text.strip()

    # Attempt 1: Strip markdown code fences
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    # Attempt 2: Direct JSON parse
    try:
        parsed = json.loads(text)
        return _validate_vision_output(parsed)
    except json.JSONDecodeError:
        pass

    # Attempt 3: Find first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            parsed = json.loads(brace_match.group())
            return _validate_vision_output(parsed)
        except json.JSONDecodeError:
            pass

    # All parsing failed — return fallback
    logger.warning("Could not parse Mistral vision response: %s", text[:200])
    fallback = dict(_VISION_FALLBACK)
    fallback["error"] = "Failed to parse Mistral vision response"
    fallback["additional_context"] = text[:500]
    return fallback


def _validate_vision_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize parsed vision output to match VisionOutput schema.

    Fills in missing fields with sensible defaults so downstream
    agents always receive a consistent shape.

    Args:
        data: Raw parsed dictionary from Gemini.

    Returns:
        dict: Normalized VisionOutput-compatible dictionary.
    """
    defaults = dict(_VISION_FALLBACK)
    defaults.update(data)

    # Ensure list types
    if not isinstance(defaults.get("visual_observations"), list):
        defaults["visual_observations"] = []
    if not isinstance(defaults.get("ocr_text"), list):
        defaults["ocr_text"] = []
    if not defaults.get("visible_equipment_context"):
        defaults["visible_equipment_context"] = _derive_image_context(defaults)

    # Clamp confidence to [0.0, 1.0]
    try:
        conf = float(defaults.get("confidence", 0.0))
        defaults["confidence"] = max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        defaults["confidence"] = 0.0

    # Normalize severity
    valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    if str(defaults.get("severity", "")).upper() not in valid_severities:
        defaults["severity"] = "LOW"
    else:
        defaults["severity"] = str(defaults["severity"]).upper()

    return defaults


def _derive_image_context(data: Dict[str, Any]) -> str:
    """Create a short human-readable context string from image findings."""
    observations = data.get("visual_observations") or []
    ocr_text = data.get("ocr_text") or []
    parts: List[str] = []
    if observations:
        parts.append("; ".join(observations[:3]))
    if ocr_text:
        parts.append("OCR: " + "; ".join(ocr_text[:3]))
    return " | ".join(parts)
