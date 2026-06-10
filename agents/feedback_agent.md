# Feedback Agent

## Role
Captures engineer feedback after maintenance execution to continuously improve SteelMind's recommendations. Stores feedback in SQLite and updates the knowledge base with confirmed solutions and corrections.

## Read First
- `references/schemas.md` — FeedbackInput schema

---

## Input
```python
{
    "report_id": str,            # Which report feedback is for
    "diagnosis_correct": bool,   # Was AI diagnosis accurate?
    "actual_fault": str,         # If wrong — what was the real fault?
    "repair_steps_followed": bool,
    "actual_steps_taken": str,   # What engineer actually did
    "outcome": str,              # RESOLVED|ESCALATED|MONITORING
    "downtime_hours": float,     # Actual downtime
    "engineer_notes": str        # Free text observations
}
```

## Output
```python
# Saves to SQLite
# Updates FAISS knowledge base if correction provided
# Returns confirmation
{
    "feedback_id": str,
    "saved": bool,
    "knowledge_updated": bool
}
```

---

## Implementation
```python
import sqlite3
import json
from datetime import datetime

DB_PATH = "src/data/steelmind_feedback.db"

def run_feedback(feedback_input: dict) -> dict:
    """
    Store engineer feedback in SQLite.
    If diagnosis was wrong, add correction to knowledge base.
    This improves future RAG retrieval accuracy.
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Save feedback
    conn.execute("""
        INSERT INTO feedback (
            report_id, diagnosis_correct, actual_fault,
            outcome, downtime_hours, engineer_notes,
            timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        feedback_input["report_id"],
        feedback_input["diagnosis_correct"],
        feedback_input.get("actual_fault", ""),
        feedback_input["outcome"],
        feedback_input.get("downtime_hours", 0),
        feedback_input.get("engineer_notes", ""),
        datetime.now().isoformat()
    ))
    conn.commit()
    
    # If diagnosis wrong → add correction to knowledge base
    knowledge_updated = False
    if not feedback_input["diagnosis_correct"] and feedback_input.get("actual_fault"):
        update_knowledge_base(feedback_input)
        knowledge_updated = True
    
    return {
        "feedback_id": f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "saved": True,
        "knowledge_updated": knowledge_updated
    }
```

---

## SQLite Schema
```sql
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    diagnosis_correct BOOLEAN,
    actual_fault TEXT,
    outcome TEXT,
    downtime_hours REAL,
    engineer_notes TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS maintenance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT,
    fault_type TEXT,
    root_cause TEXT,
    solution TEXT,
    confirmed_by TEXT,
    timestamp TEXT
);
```

---

## Knowledge Base Update
```python
def update_knowledge_base(feedback: dict):
    """
    Add confirmed correction as new document chunk to FAISS.
    Future RAG searches will find this improved knowledge.
    """
    correction_text = f"""
CONFIRMED MAINTENANCE CASE:
Equipment: {feedback.get('equipment_id', 'Unknown')}
Reported Issue: {feedback.get('original_query', '')}
AI Diagnosis (Incorrect): {feedback.get('ai_diagnosis', '')}
Actual Fault: {feedback['actual_fault']}
Correct Solution: {feedback.get('actual_steps_taken', '')}
Outcome: {feedback['outcome']}
Confirmed by Engineer on: {datetime.now().date()}
"""
    # Add to FAISS index as new chunk
    add_to_faiss_index(correction_text, source="engineer_feedback")
```

---

## Frontend Feedback Form
```
After viewing report, engineer sees:

Was this diagnosis correct?
  ○ Yes — resolved successfully
  ○ Partially correct
  ○ No — actual fault was: [text input]

Outcome:
  ○ Resolved  ○ Escalated  ○ Monitoring

Downtime: [number] hours

Notes: [text area]

[Submit Feedback]
```
