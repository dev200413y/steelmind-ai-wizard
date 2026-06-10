"""
SteelMind AI Wizard — LangGraph Pipeline
==========================================
Defines the multi-agent DAG with parallel execution.

Pipeline Flow:
    Orchestrator
        ├──→ Vision Agent    ─┐
        ├──→ RAG Agent       ─┼──→ Diagnostic Agent → Risk Scorer → Report Generator → END
        └──→ Anomaly Agent   ─┘
"""

import logging
from typing import List, Literal

from langgraph.graph import StateGraph, END

from src.schemas import SteelMindState
from src.agents.orchestrator import orchestrate
from src.agents.vision_agent import run_vision
from src.agents.rag_agent import run_rag
from src.agents.anomaly_agent import run_anomaly
from src.agents.diagnostic_agent import run_diagnostic
from src.agents.risk_scorer import run_risk_scorer
from src.agents.report_generator import run_report

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# Routing Logic
# ══════════════════════════════════════════════════════════════

def route_inputs(state: SteelMindState) -> List[str]:
    """
    Decide which agents to call based on available inputs.
    Returns list of agent node names to run IN PARALLEL.

    Rules:
    - RAG Agent is ALWAYS called (knowledge retrieval)
    - Vision Agent only if image is uploaded
    - Anomaly Agent only if CSV sensor data is uploaded
    """
    agents = ["rag_agent"]  # Always call RAG

    if state.get("has_image"):
        agents.append("vision_agent")
        logger.info("📸 Image detected — Vision Agent will be called")

    if state.get("has_csv"):
        agents.append("anomaly_agent")
        logger.info("📊 CSV detected — Anomaly Agent will be called")

    logger.info(f"🔀 Routing to parallel agents: {agents}")
    return agents


# ══════════════════════════════════════════════════════════════
# Graph Builder
# ══════════════════════════════════════════════════════════════

def build_steelmind_graph() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent pipeline.

    Architecture:
    - Fan-out: Orchestrator dispatches Vision + RAG + Anomaly in PARALLEL
    - Fan-in: All parallel agents feed into Diagnostic Agent
    - Sequential: Diagnostic → Risk Scorer → Report Generator → END

    Returns:
        Compiled LangGraph runnable
    """
    graph = StateGraph(SteelMindState)

    # ── Add all agent nodes ──────────────────────
    graph.add_node("orchestrator", orchestrate)
    graph.add_node("vision_agent", run_vision)
    graph.add_node("rag_agent", run_rag)
    graph.add_node("anomaly_agent", run_anomaly)
    graph.add_node("diagnostic_agent", run_diagnostic)
    graph.add_node("risk_scorer", run_risk_scorer)
    graph.add_node("report_generator", run_report)

    # ── Entry point ──────────────────────────────
    graph.set_entry_point("orchestrator")

    # ── Fan-out: Orchestrator → Parallel Agents ──
    graph.add_conditional_edges(
        "orchestrator",
        route_inputs,
        {
            "vision_agent": "vision_agent",
            "rag_agent": "rag_agent",
            "anomaly_agent": "anomaly_agent",
        }
    )

    # ── Fan-in: Parallel Agents → Diagnostic ─────
    graph.add_edge("vision_agent", "diagnostic_agent")
    graph.add_edge("rag_agent", "diagnostic_agent")
    graph.add_edge("anomaly_agent", "diagnostic_agent")

    # ── Sequential Pipeline ───────────────────────
    graph.add_edge("diagnostic_agent", "risk_scorer")
    graph.add_edge("risk_scorer", "report_generator")
    graph.add_edge("report_generator", END)

    # ── Compile ───────────────────────────────────
    compiled = graph.compile()
    logger.info("✅ SteelMind LangGraph pipeline compiled successfully")

    return compiled


# ══════════════════════════════════════════════════════════════
# Global Pipeline Instance
# ══════════════════════════════════════════════════════════════

steelmind_pipeline = None


def get_pipeline():
    """
    Get or create the SteelMind pipeline singleton.
    Lazy initialization to avoid import-time side effects.
    """
    global steelmind_pipeline
    if steelmind_pipeline is None:
        steelmind_pipeline = build_steelmind_graph()
    return steelmind_pipeline


async def run_pipeline(initial_state: dict) -> SteelMindState:
    """
    Execute the full SteelMind pipeline with given inputs.

    Args:
        initial_state: Dict with user inputs (query, image_path, csv_path, etc.)

    Returns:
        Final SteelMindState with all agent outputs populated
    """
    pipeline = get_pipeline()

    # Set defaults for missing fields
    state = {
        "query": initial_state.get("query", ""),
        "language": initial_state.get("language", "en"),
        "has_image": False,
        "has_csv": False,
        "has_docs": False,
        "image_path": initial_state.get("image_path"),
        "csv_path": initial_state.get("csv_path"),
        "doc_paths": initial_state.get("doc_paths"),
        "equipment_id": initial_state.get("equipment_id"),
        "equipment_type": initial_state.get("equipment_type"),
        "session_id": initial_state.get("session_id", "default"),
        "vision_output": None,
        "rag_context": None,
        "anomaly_result": None,
        "diagnosis": None,
        "risk_level": None,
        "risk_details": None,
        "report": None,
        "force_critical": None,
        "rag_error": None,
        "pipeline_errors": [],
    }

    logger.info(f"🚀 Starting SteelMind pipeline for session: {state['session_id']}")

    try:
        result = await pipeline.ainvoke(state)
        logger.info(f"✅ Pipeline completed successfully for session: {state['session_id']}")
        return result
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")
        state["pipeline_errors"] = [str(e)]
        return state
