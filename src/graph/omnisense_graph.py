"""
OmniSense AI Wizard — LangGraph Pipeline
==========================================
Defines the multi-agent cyclic ReAct graph for continuous chat.

Pipeline Flow:
    User -> Orchestrator <---> Vision Agent
                         <---> RAG Agent
                         <---> Anomaly Agent
                         <---> Diagnostic Agent
                         <---> Risk Scorer
                         <---> Report Generator
"""

import logging
from typing import List, Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.schemas import OmniSenseState
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

def route_orchestrator(state: OmniSenseState) -> List[str]:
    """
    Decide which agent/tool to call based on the Orchestrator's last message.
    If the orchestrator made tool calls, route to all specific agents in parallel.
    Otherwise, we are done with the turn and route to END.
    """
    messages = state.get("messages", [])
    if not messages:
        return [END]
    
    last_message = messages[-1]
    
    # Check if the LLM decided to call any tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        routing_map = {
            "run_vision": "vision_agent",
            "run_rag": "rag_agent",
            "run_anomaly": "anomaly_agent",
            "run_diagnostic": "diagnostic_agent",
            "run_risk_scorer": "risk_scorer",
            "generate_report": "report_generator"
        }
        
        nodes_to_run = []
        for tc in last_message.tool_calls:
            node = routing_map.get(tc["name"])
            if node:
                nodes_to_run.append(node)
                
        if nodes_to_run:
            logger.info(f"🔀 Orchestrator routing to: {nodes_to_run}")
            return nodes_to_run
            
    logger.info("🏁 Orchestrator finished turn. Waiting for user input.")
    return [END]


# ══════════════════════════════════════════════════════════════
# Graph Builder
# ══════════════════════════════════════════════════════════════

def build_omnisense_graph() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent cyclic pipeline.
    """
    graph = StateGraph(OmniSenseState)

    # ── Add all agent nodes ──────────────────────
    graph.add_node("orchestrator", orchestrate)
    graph.add_node("vision_agent", run_vision)
    graph.add_node("rag_agent", run_rag)
    graph.add_node("anomaly_agent", run_anomaly)
    graph.add_node("diagnostic_agent", run_diagnostic)
    graph.add_node("risk_scorer", run_risk_scorer)
    graph.add_node("report_generator", run_report)

    # ── Entry point is always the Orchestrator ───
    graph.set_entry_point("orchestrator")

    # ── Conditional Routing from Orchestrator ────
    # We pass the possible target nodes list so LangGraph knows what to expect
    possible_targets = ["vision_agent", "rag_agent", "anomaly_agent", "diagnostic_agent", "risk_scorer", "report_generator", END]
    graph.add_conditional_edges("orchestrator", route_orchestrator, possible_targets)

    # ── Return edges: All tools report back to Orchestrator ──
    graph.add_edge("vision_agent", "orchestrator")
    graph.add_edge("rag_agent", "orchestrator")
    graph.add_edge("anomaly_agent", "orchestrator")
    graph.add_edge("diagnostic_agent", "orchestrator")
    graph.add_edge("risk_scorer", "orchestrator")
    graph.add_edge("report_generator", "orchestrator")

    # ── Compile ───────────────────────────────────
    compiled = graph.compile()
    logger.info("✅ OmniSense cyclic ReAct graph compiled successfully")

    return compiled


# ══════════════════════════════════════════════════════════════
# Global Pipeline Instance
# ══════════════════════════════════════════════════════════════

omnisense_pipeline = None

def get_pipeline():
    """Lazy initialization of the pipeline."""
    global omnisense_pipeline
    if omnisense_pipeline is None:
        omnisense_pipeline = build_omnisense_graph()
    return omnisense_pipeline


async def run_pipeline(initial_state: dict) -> dict:
    """Async wrapper to run the full pipeline from REST endpoints."""
    pipeline = get_pipeline()
    final_state = await pipeline.ainvoke(initial_state)
    return final_state

