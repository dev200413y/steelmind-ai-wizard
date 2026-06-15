"""
OmniSense AI Wizard — All Schemas & Type Definitions
=====================================================
Central schema definitions for shared LangGraph state.
All agents MUST import types from this module.
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


# ══════════════════════════════════════════════════════════════
# Main LangGraph Shared State
# ══════════════════════════════════════════════════════════════

class OmniSenseState(TypedDict):
    """
    Shared state passed through all agents in the LangGraph pipeline.
    Every agent reads from and writes to this state.
    """
    # ── Conversation History ─────────────────────
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ── Agent Status (For WebSocket Streaming) ───
    agent_status: Optional[str]         # e.g., "Analyzing image...", "Querying RAG..."
    
    # ── Multimodal/Context Variables ─────────────
    query: str                          # latest engineer query
    language: str                       # hi|or|bn|en|nl|th|unknown
    has_image: bool
    has_csv: bool
    has_docs: bool
    image_paths: List[str]              # Allowing multiple uploads during chat
    csv_paths: List[str]
    doc_paths: List[str]
    equipment_id: Optional[str]         # e.g. "BF-001"
    equipment_type: Optional[str]       # e.g. "Blast Furnace"
    session_id: str

    # ── Agent/Tool Outputs (Stored for Context) ──
    vision_output: Optional[Dict]       # VisionOutput
    rag_context: Optional[List[Dict]]   # List of RAGChunk
    anomaly_result: Optional[Dict]      # AnomalyResult
    diagnosis: Optional[Dict]           # DiagnosisOutput
    risk_level: Optional[str]           # LOW|MEDIUM|HIGH|CRITICAL
    risk_details: Optional[Dict]        # RiskDetails
    report: Optional[Dict]              # ReportOutput

    # ── Control Flags ────────────────────────────
    force_critical: Optional[bool]      # Set by Anomaly Agent
    rag_error: Optional[str]
    pipeline_errors: Optional[List[str]]


# ══════════════════════════════════════════════════════════════
# Agent Output Schemas
# ══════════════════════════════════════════════════════════════

class VisionOutput(TypedDict):
    """Output from Vision Agent — image fault analysis."""
    fault_detected: bool
    fault_type: str          # corrosion|crack|wear|overheating|leak|vibration|other
    affected_component: str  # bearing|pipe|gear|motor|frame|belt|valve|other
    severity: str            # LOW|MEDIUM|HIGH|CRITICAL
    visual_observations: List[str]
    immediate_action_required: bool
    confidence: float        # 0.0 to 1.0
    additional_context: str
    error: Optional[str]     # Set if agent failed


class RAGChunk(TypedDict):
    """Single knowledge chunk retrieved by RAG Agent."""
    content: str             # Text chunk from document
    source: str              # Document filename
    page: int                # Page number
    relevance_score: float   # Cosine similarity score
    chunk_id: str            # Unique identifier


class AnomalyResult(TypedDict):
    """Output from Anomaly Detection Agent — sensor analysis."""
    anomaly_detected: bool
    anomaly_score: float         # 0.0 to 1.0
    severity: str                # LOW|MEDIUM|HIGH|CRITICAL
    anomalous_sensor: str        # Which sensor is abnormal
    current_value: float
    normal_range: str            # e.g. "0.5-2.0 mm/s"
    rul_days: int                # Remaining Useful Life
    rul_confidence: float
    alert_triggered: bool        # True if RUL < 7 days
    trend_data: List[Dict]       # Last 30 readings for chart
    recommendations: List[str]


class DiagnosisOutput(TypedDict):
    """Output from Diagnostic Agent — core reasoning results."""
    fault_identified: str
    root_cause: str
    confidence: float
    repair_steps: List[str]          # Ordered action list
    immediate_actions: List[str]     # Do RIGHT NOW
    spare_parts_needed: List[Dict]   # [{name, qty, part_number}]
    estimated_repair_time: str       # e.g. "2-4 hours"
    sources_cited: List[str]         # RAG source references
    long_term_recommendations: str
    language: str                    # Response language
    error: Optional[str]


class SparePartItem(TypedDict):
    """Single spare part entry."""
    name: str
    quantity: int
    part_number: str
    warehouse_location: Optional[str]
    in_stock: Optional[bool]
    procurement_days: Optional[int]


class RiskDetails(TypedDict):
    """Output from Risk Scorer Agent — multi-factor risk assessment."""
    final_risk: str              # LOW|MEDIUM|HIGH|CRITICAL
    risk_score: float            # 0.0 to 1.0
    factors: Dict[str, float]    # Individual factor scores
    urgency_hours: int           # Act within N hours
    bottleneck_risk: bool
    escalate_to_supervisor: bool
    forced_by: Optional[str]     # If overridden by Anomaly Agent


class ReportOutput(TypedDict):
    """Output from Report Generator Agent."""
    summary: str                 # 2-3 line executive summary
    full_report_md: str          # Complete markdown report
    pdf_path: Optional[str]      # Path to PDF file
    report_path: Optional[str]   # Path to markdown report
    report_id: str               # RPT-YYYYMMDD-NNNN
    timestamp: str
    sections: Dict[str, str]     # Named report sections


class FeedbackInput(TypedDict):
    """Input for Feedback Agent — engineer's post-repair feedback."""
    report_id: str
    diagnosis_correct: bool
    actual_fault: Optional[str]
    repair_steps_followed: bool
    actual_steps_taken: Optional[str]
    outcome: str                 # RESOLVED|ESCALATED|MONITORING
    downtime_hours: float
    engineer_notes: Optional[str]
    equipment_id: Optional[str]


# ══════════════════════════════════════════════════════════════
# Constants & Reference Data
# ══════════════════════════════════════════════════════════════

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",      # Jamshedpur, Kalinganagar
    "or": "Odia",       # Kalinganagar
    "bn": "Bengali",    # Jamshedpur
    "sat": "Santali",   # Jamshedpur tribal workforce
    "en": "English",    # All plants
    "nl": "Dutch",      # IJmuiden, Netherlands
    "cy": "Welsh",      # Port Talbot, UK
    "th": "Thai",       # Thailand
}

EQUIPMENT_IDS = {
    "BF-001": "Blast Furnace 1",
    "BF-002": "Blast Furnace 2",
    "RM-001": "Rolling Mill 1",
    "RM-002": "Rolling Mill 2",
    "CC-001": "Continuous Caster 1",
    "HS-001": "Hydraulic System 1",
    "EAF-001": "Electric Arc Furnace 1",
    "CV-001": "Conveyor System 1",
    "CP-001": "Compressor 1",
}

EQUIPMENT_TYPES = {
    "BF": "Blast Furnace",
    "RM": "Rolling Mill",
    "CC": "Continuous Caster",
    "HS": "Hydraulic System",
    "EAF": "Electric Arc Furnace",
    "CV": "Conveyor System",
    "CP": "Compressor",
}

# Equipment criticality scores for Risk Scorer
EQUIPMENT_CRITICALITY = {
    "Blast Furnace": 1.0,
    "Electric Arc Furnace": 0.95,
    "Continuous Caster": 0.90,
    "Rolling Mill": 0.85,
    "Hydraulic System": 0.75,
    "Compressor": 0.65,
    "Conveyor System": 0.55,
}

# Sensor normal ranges for reference
SENSOR_THRESHOLDS = {
    "sensor_temperature": {"normal": (1150, 1300), "warning": 1400, "critical": 1550, "unit": "°C"},
    "sensor_vibration": {"normal": (0.5, 2.0), "warning": 3.5, "critical": 6.0, "unit": "mm/s"},
    "sensor_pressure": {"normal": (150, 200), "warning": 220, "critical": 250, "unit": "bar"},
    "sensor_rpm": {"normal": (1400, 1600), "warning": 1750, "critical": 1900, "unit": "RPM"},
    "sensor_current": {"normal": (80, 100), "warning": 115, "critical": 130, "unit": "A"},
}
