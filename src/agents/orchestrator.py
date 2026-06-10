"""
SteelMind AI Wizard — Orchestrator Agent
========================================
Central controller and router. Initializes state.
"""

import logging
from src.schemas import SteelMindState
from src.utils.voice import detect_language

logger = logging.getLogger(__name__)

def route_inputs(state: SteelMindState) -> list[str]:
    """
    Decide which agents to call based on available inputs.
    Returns list of agent names to run IN PARALLEL.
    """
    agents = ["rag_agent"]  # Always call RAG
    
    if state.get("has_image"):
        agents.append("vision_agent")
    
    if state.get("has_csv"):
        agents.append("anomaly_agent")
        
    return agents

def orchestrate(state: SteelMindState) -> SteelMindState:
    """Initialize state flags and detect input types."""
    logger.info("🧠 Orchestrator initializing state")
    
    state["has_image"] = bool(state.get("image_path"))
    state["has_csv"] = bool(state.get("csv_path"))
    state["has_docs"] = bool(state.get("doc_paths"))
    
    query = state.get("query", "")
    if query and not state.get("language"):
        state["language"] = detect_language(query)
    elif not state.get("language"):
        state["language"] = "en"
        
    return state
