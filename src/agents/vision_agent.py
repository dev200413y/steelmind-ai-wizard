"""
SteelMind AI Wizard — Vision Agent
=====================================
Analyzes uploaded equipment photographs using Gemini 1.5 Flash
to identify visual faults (corrosion, cracks, overheating, wear, leaks).

Spec: agents/vision_agent.md
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.schemas import SteelMindState, VisionOutput
from src.prompts import get_prompt

logger = logging.getLogger(__name__)

# ── Default fallback when vision fails ───────────────────────
_VISION_FALLBACK: Dict[str, Any] = {
    "fault_detected": False,
    "fault_type": "unknown",
    "affected_component": "unknown",
    "severity": "LOW",
    "visual_observations": [],
    "immediate_action_required": False,
    "confidence": 0.0,
    "additional_context": "",
    "error": None,
}


# ══════════════════════════════════════════════════════════════
# Public Entry Point
# ══════════════════════════════════════════════════════════════

def run_vision(state: SteelMindState) -> SteelMindState:
    """
    Analyze an equipment image using Gemini 1.5 Flash vision model.

    Reads the image from ``state["image_path"]``, sends it to
    Gemini along with the VISION_AGENT_PROMPT, and parses the
    structured JSON response into ``state["vision_output"]``.

    Skips silently (returns state unchanged) when no image is
    provided.  On any error, sets a safe fallback with
    ``fault_detected=False`` so downstream agents can continue.

    Args:
        state: The shared LangGraph pipeline state.

    Returns:
        SteelMindState: Updated state with ``vision_output`` populated.
    """
    # Skip if no image
    if not state.get("has_image") or not state.get("image_path"):
        logger.info("Vision Agent skipped — no image provided.")
        return state

    image_path = state["image_path"]

    try:
        # Validate file exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Read image bytes
        image_data = Path(image_path).read_bytes()
        mime_type = _detect_mime_type(image_path)

        # Build prompt
        prompt = _build_vision_prompt(state)

        # Configure Gemini
        import google.generativeai as genai  # type: ignore[import-untyped]

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment variables.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Send image + prompt to Gemini
        logger.info("Sending image to Gemini 1.5 Flash — %s (%d bytes)", image_path, len(image_data))
        response = model.generate_content([
            {"mime_type": mime_type, "data": image_data},
            prompt,
        ])

        # Parse structured JSON from response
        state["vision_output"] = _parse_vision_json(response.text)
        logger.info(
            "Vision analysis complete — fault=%s, severity=%s, confidence=%.2f",
            state["vision_output"].get("fault_detected"),
            state["vision_output"].get("severity"),
            state["vision_output"].get("confidence", 0.0),
        )

    except Exception as exc:
        logger.error("Vision Agent failed: %s", exc, exc_info=True)
        fallback = dict(_VISION_FALLBACK)
        fallback["error"] = str(exc)
        state["vision_output"] = fallback

    return state


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _build_vision_prompt(state: SteelMindState) -> str:
    """
    Build the vision analysis prompt with optional equipment context.

    Fetches the base prompt from the prompts library and appends
    equipment type and engineer query when available.

    Args:
        state: Pipeline state with query and equipment info.

    Returns:
        str: Complete prompt for Gemini vision analysis.
    """
    prompt = get_prompt("VISION_AGENT_PROMPT")

    if state.get("equipment_type"):
        prompt += f"\nEquipment Type: {state['equipment_type']}"
    if state.get("query"):
        prompt += f"\nEngineer's description: {state['query']}"

    return prompt


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
    Parse Gemini's response text into a structured VisionOutput dict.

    Handles three common response formats:
      1. Clean JSON.
      2. JSON wrapped in markdown code fences.
      3. Malformed text — extract what we can with regex.

    Args:
        response_text: Raw text response from Gemini.

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
    logger.warning("Could not parse Gemini vision response: %s", text[:200])
    fallback = dict(_VISION_FALLBACK)
    fallback["error"] = "Failed to parse Gemini response"
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
