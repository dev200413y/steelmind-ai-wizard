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
    Embed the feedback and append to FAISS index.
    """
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_core.documents import Document
        from pathlib import Path

        EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
        FAISS_INDEX_DIR = Path("src/knowledge_base/faiss_index")

        if not FAISS_INDEX_DIR.exists():
            logger.warning("FAISS index directory does not exist, cannot update knowledge base.")
            return

        logger.info(f"🧠 Updating knowledge base with correction for {feedback.get('report_id')}")
        
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        
        vectorstore = FAISS.load_local(
            str(FAISS_INDEX_DIR),
            embeddings,
            allow_dangerous_deserialization=True,
        )

        # Create a document from the feedback
        content = f"Feedback Correction for Report {feedback.get('report_id')}:\n"
        content += f"Actual Fault: {feedback.get('actual_fault', 'None provided')}\n"
        content += f"Engineer Notes: {feedback.get('engineer_notes', 'None provided')}\n"
        content += f"Outcome: {feedback.get('outcome', 'UNKNOWN')}\n"
        
        doc = Document(
            page_content=content,
            metadata={
                "source": "engineer_feedback",
                "report_id": feedback.get('report_id'),
                "type": "correction"
            }
        )

        vectorstore.add_documents([doc])
        vectorstore.save_local(str(FAISS_INDEX_DIR))
        logger.info("✅ Successfully updated FAISS knowledge base with feedback.")
        
    except Exception as e:
        logger.error(f"❌ Failed to update knowledge base: {e}")

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
