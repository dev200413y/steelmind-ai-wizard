# SteelMind AI Wizard — All Schemas
> Read this FIRST before writing any agent code.

---

## Main LangGraph State
```python
from typing import TypedDict, Optional, List, Dict, Any

class SteelMindState(TypedDict):
    # ── User Input ──────────────────────────────
    query: str                          # Text or STT-transcribed query
    language: str                       # hi|or|bn|en|nl|th|unknown
    has_image: bool
    has_csv: bool
    has_docs: bool
    image_path: Optional[str]
    csv_path: Optional[str]
    doc_paths: Optional[List[str]]
    equipment_id: Optional[str]         # e.g. "BF-001"
    equipment_type: Optional[str]       # e.g. "Blast Furnace"
    session_id: str

    # ── Agent Outputs ────────────────────────────
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
```

---

## VisionOutput Schema
```python
class VisionOutput(TypedDict):
    fault_detected: bool
    fault_type: str          # corrosion|crack|wear|overheating|leak|vibration|other
    affected_component: str  # bearing|pipe|gear|motor|frame|belt|valve|other
    severity: str            # LOW|MEDIUM|HIGH|CRITICAL
    visual_observations: List[str]
    immediate_action_required: bool
    confidence: float        # 0.0 to 1.0
    additional_context: str
    error: Optional[str]     # Set if agent failed
```

---

## RAGChunk Schema
```python
class RAGChunk(TypedDict):
    content: str             # Text chunk from document
    source: str              # Document filename
    page: int                # Page number
    relevance_score: float   # Cosine similarity score
    chunk_id: str            # Unique identifier
```

---

## AnomalyResult Schema
```python
class AnomalyResult(TypedDict):
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
```

---

## DiagnosisOutput Schema
```python
class DiagnosisOutput(TypedDict):
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
```

---

## SparePartItem Schema
```python
class SparePartItem(TypedDict):
    name: str
    quantity: int
    part_number: str
    warehouse_location: Optional[str]
    in_stock: Optional[bool]
    procurement_days: Optional[int]
```

---

## RiskDetails Schema
```python
class RiskDetails(TypedDict):
    final_risk: str              # LOW|MEDIUM|HIGH|CRITICAL
    risk_score: float            # 0.0 to 1.0
    factors: Dict[str, float]    # Individual factor scores
    urgency_hours: int           # Act within N hours
    bottleneck_risk: bool
    escalate_to_supervisor: bool
    forced_by: Optional[str]     # If overridden by Anomaly Agent
```

---

## ReportOutput Schema
```python
class ReportOutput(TypedDict):
    summary: str                 # 2-3 line executive summary
    full_report_md: str          # Complete markdown report
    pdf_path: str                # Path to PDF file
    report_id: str               # RPT-YYYYMMDD-NNNN
    timestamp: str
    sections: Dict[str, str]     # Named report sections
```

---

## FeedbackInput Schema
```python
class FeedbackInput(TypedDict):
    report_id: str
    diagnosis_correct: bool
    actual_fault: Optional[str]
    repair_steps_followed: bool
    actual_steps_taken: Optional[str]
    outcome: str                 # RESOLVED|ESCALATED|MONITORING
    downtime_hours: float
    engineer_notes: Optional[str]
    equipment_id: Optional[str]
```

---

## Language Codes Reference
```python
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
```

---

## Equipment IDs Reference
```python
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
```
