# Orchestrator Agent

## Role
Central controller and router of the SteelMind AI Wizard pipeline. Receives all user inputs, decides which agents to call, manages parallel execution, and maintains shared state across the entire pipeline.

## IMPORTANT — Read First
Before writing orchestrator.py, read:
- `references/schemas.md` — SteelMindState schema
- `assets/prompts.md` — No prompts needed here, but understand state

---

## Inputs (from user/API)
```python
{
    "query": str,           # Text or voice-transcribed query
    "image_path": str,      # Optional — path to uploaded image
    "csv_path": str,        # Optional — path to uploaded sensor CSV
    "doc_paths": list,      # Optional — list of uploaded PDF paths
    "equipment_id": str,    # Optional — selected equipment
    "equipment_type": str,  # Optional — equipment category
    "session_id": str       # Required — conversation session ID
}
```

---

## Routing Logic — Conditional Edges
```python
def route_inputs(state: SteelMindState) -> list[str]:
    """
    Decide which agents to call based on available inputs.
    Returns list of agent names to run IN PARALLEL.
    """
    agents = ["rag_agent"]  # Always call RAG
    
    if state["has_image"]:
        agents.append("vision_agent")
    
    if state["has_csv"]:
        agents.append("anomaly_agent")
    
    return agents
    # These run in PARALLEL via LangGraph fan-out
```

---

## Parallel Execution Pattern
```
Orchestrator
    │
    ├──→ vision_agent    ─┐
    ├──→ rag_agent       ─┼──→ diagnostic_agent
    └──→ anomaly_agent   ─┘         │
                               risk_scorer
                                    │
                            report_generator
                                    │
                            feedback_agent (async)
```

---

## LangGraph Graph Definition
```python
# src/graph/steelmind_graph.py

from langgraph.graph import StateGraph, END
from src.agents.orchestrator import route_inputs
from src.agents.vision_agent import run_vision
from src.agents.rag_agent import run_rag
from src.agents.anomaly_agent import run_anomaly
from src.agents.diagnostic_agent import run_diagnostic
from src.agents.risk_scorer import run_risk_scorer
from src.agents.report_generator import run_report
from references.schemas import SteelMindState

graph = StateGraph(SteelMindState)

# Add all nodes
graph.add_node("orchestrator", orchestrate)
graph.add_node("vision_agent", run_vision)
graph.add_node("rag_agent", run_rag)
graph.add_node("anomaly_agent", run_anomaly)
graph.add_node("diagnostic_agent", run_diagnostic)
graph.add_node("risk_scorer", run_risk_scorer)
graph.add_node("report_generator", run_report)

# Entry point
graph.set_entry_point("orchestrator")

# Fan-out: parallel execution
graph.add_conditional_edges(
    "orchestrator",
    route_inputs,
    {
        "vision_agent": "vision_agent",
        "rag_agent": "rag_agent",
        "anomaly_agent": "anomaly_agent"
    }
)

# Fan-in: all parallel agents → diagnostic
graph.add_edge("vision_agent", "diagnostic_agent")
graph.add_edge("rag_agent", "diagnostic_agent")
graph.add_edge("anomaly_agent", "diagnostic_agent")

# Sequential after diagnostic
graph.add_edge("diagnostic_agent", "risk_scorer")
graph.add_edge("risk_scorer", "report_generator")
graph.add_edge("report_generator", END)
```

---

## State Initialization
```python
def orchestrate(state: SteelMindState) -> SteelMindState:
    """
    Initialize state flags and detect input types.
    Detect language from query if voice transcription available.
    """
    state["has_image"] = bool(state.get("image_path"))
    state["has_csv"] = bool(state.get("csv_path"))
    state["has_docs"] = bool(state.get("doc_paths"))
    state["language"] = detect_language(state["query"])  # from utils/voice.py
    return state
```

---

## Error Handling
- If vision_agent fails → continue without vision_output (log warning)
- If anomaly_agent fails → continue without anomaly_result (log warning)
- If rag_agent fails → diagnostic_agent uses query only (log error)
- Never crash entire pipeline for single agent failure
