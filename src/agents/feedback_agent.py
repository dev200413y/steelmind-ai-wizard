"""
OmniSense AI Wizard — Feedback Agent
======================================
Captures engineer feedback and stores it in SQLite.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("src/data/omnisense_feedback.db")

def init_db():
    """Initialize SQLite database tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            diagnosis_correct BOOLEAN,
            actual_fault TEXT,
            outcome TEXT,
            downtime_hours REAL,
            engineer_notes TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def update_knowledge_base(feedback: dict):
    """
    Mock function to update FAISS knowledge base.
    In a full implementation, this would embed the feedback and append to FAISS.
    """
    logger.info(f"🧠 Knowledge base would be updated with correction for {feedback.get('report_id')}")

def run_feedback(feedback_input: dict) -> dict:
    """Store engineer feedback in SQLite."""
    logger.info("🗣️ Running Feedback Agent")
    init_db()
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("""
            INSERT INTO feedback (
                report_id, diagnosis_correct, actual_fault,
                outcome, downtime_hours, engineer_notes,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_input.get("report_id", "UNKNOWN"),
            feedback_input.get("diagnosis_correct", True),
            feedback_input.get("actual_fault", ""),
            feedback_input.get("outcome", "RESOLVED"),
            feedback_input.get("downtime_hours", 0.0),
            feedback_input.get("engineer_notes", ""),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        knowledge_updated = False
        if not feedback_input.get("diagnosis_correct", True) and feedback_input.get("actual_fault"):
            update_knowledge_base(feedback_input)
            knowledge_updated = True
            
        feedback_id = f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"✅ Feedback saved: {feedback_id}")
        
        return {
            "feedback_id": feedback_id,
            "saved": True,
            "knowledge_updated": knowledge_updated
        }
        
    except Exception as e:
        logger.error(f"❌ Feedback Agent failed: {str(e)}")
        return {
            "saved": False,
            "error": str(e)
        }
