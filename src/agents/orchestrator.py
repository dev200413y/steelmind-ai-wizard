"""
OmniSense AI Wizard — Orchestrator Agent
========================================
Central conversational controller. Routes queries to specialized tools.
"""

import os
import logging
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from src.schemas import OmniSenseState

logger = logging.getLogger(__name__)

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

def orchestrate(state: OmniSenseState) -> OmniSenseState:
    logger.info("🧠 Orchestrator thinking...")
    
    messages = state.get("messages", [])
    
    # System prompt
    system_prompt = SystemMessage(content='''
You are OmniSense AI Wizard, a highly advanced multimodal maintenance decision support agent for Tata Steel.
Your goal is to help maintenance engineers diagnose equipment faults and predict failures.

You have access to specialized tools (sub-agents). Use them when appropriate:
- If the user uploaded an image, ALWAYS call `run_vision`.
- If you need to consult manuals or SOPs, ALWAYS call `run_rag`.
- If you need to check live sensor readings (vibration, temp), call `run_anomaly`.
- Once you have gathered sufficient context from your tools, call `run_diagnostic` to perform the actual diagnosis and root cause analysis.
- You can converse naturally with the user.

IMPORTANT RULES:
1. Do not hallucinate data. If you lack information, call a tool to get it.
2. If the user is just greeting you (e.g. "hi", "hello"), greet them warmly and ask how you can assist with their equipment maintenance. DO NOT invent or assume an ongoing equipment fault.
''')

    try:
        # Fallback to direct Mistral API if Groq fails
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is not set.")
            
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
            model="mistral-small-latest",
            temperature=0.1
        )
        llm_with_tools = llm.bind_tools(tools)
        
        response = llm_with_tools.invoke([system_prompt] + messages)
        state["messages"].append(response)
        
    except Exception as e:
        logger.error(f"Orchestrator LLM failed: {e}")
        state["messages"].append(AIMessage(content=f"Error connecting to my core reasoning engine. Please check if your API keys are valid. Details: {e}"))

    return state
