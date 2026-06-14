"""
OmniSense AI Wizard — RAG Agent
=================================
Retrieves the top-5 most relevant knowledge chunks from the
FAISS vector index for the current maintenance query.

Spec: agents/rag_agent.md
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from src.schemas import OmniSenseState, RAGChunk
from src.utils.embeddings import get_embeddings
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────
FAISS_INDEX_PATH = os.path.join("src", "knowledge_base", "faiss_index")
TOP_K = 5


# ══════════════════════════════════════════════════════════════
# Public Entry Point
# ══════════════════════════════════════════════════════════════

def run_rag(state: OmniSenseState) -> OmniSenseState:
    """
    Retrieve top-5 relevant knowledge chunks for the current query.

    Uses FAISS vector similarity search with
    sentence-transformers/all-MiniLM-L6-v2 embeddings that run
    entirely on CPU (no API cost).

    Steps:
        1. Load the singleton embedding model.
        2. Load the persisted FAISS index from disk.
        3. Optionally prepend equipment context to the query.
        4. Perform similarity_search_with_score(k=5).
        5. Write results to ``state["rag_context"]``.

    Error handling:
        On any failure the agent returns an empty list and
        sets ``state["rag_error"]`` so the Diagnostic Agent
        can still operate with the raw user query.

    Args:
        state: The shared LangGraph pipeline state.

    Returns:
        OmniSenseState: Updated state with ``rag_context`` populated.
    """
    # Extract tool call
    messages = state.get("messages", [])
    if not messages: return state
    last_msg = messages[-1]
    
    tool_call_id = None
    query = state.get("query", "")
    if hasattr(last_msg, "tool_calls"):
        for tc in last_msg.tool_calls:
            if tc["name"] == "run_rag":
                tool_call_id = tc["id"]
                query = tc["args"].get("query", query)
                break
                
    if not tool_call_id:
        return state

    state["agent_status"] = "Querying knowledge base manuals..."

    try:
        # Guard: check that the FAISS index exists
        if not Path(FAISS_INDEX_PATH).exists():
            logger.warning("FAISS index not found.")
            state["rag_context"] = []
            state["rag_error"] = f"FAISS index not found at {FAISS_INDEX_PATH}"
            state["messages"].append(ToolMessage(tool_call_id=tool_call_id, name="run_rag", content="FAISS index missing."))
            return state

        # 1. Load embeddings (singleton — fast on subsequent calls)
        embeddings = get_embeddings()

        # 2. Load FAISS vectorstore from disk
        from langchain_community.vectorstores import FAISS

        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )

        # 3. Build enriched search query
        search_query = _build_search_query(state)

        # 4. Retrieve top-k chunks with cosine similarity scores
        docs_with_scores = vectorstore.similarity_search_with_score(
            search_query, k=TOP_K
        )

        # 5. Format into RAGChunk list
        rag_chunks: List[Dict[str, Any]] = []
        for doc, score in docs_with_scores:
            chunk: Dict[str, Any] = {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": int(doc.metadata.get("page", 0)),
                "relevance_score": round(float(score), 4),
                "chunk_id": doc.metadata.get("chunk_id", ""),
            }
            rag_chunks.append(chunk)

        state["rag_context"] = rag_chunks
        
        # Append ToolMessage
        tool_msg = ToolMessage(
            tool_call_id=tool_call_id,
            name="run_rag",
            content=f"Found {len(rag_chunks)} manuals. Context: {str(rag_chunks)}"
        )
        state["messages"].append(tool_msg)
        
        logger.info(
            "RAG retrieved %d chunks (top score: %.4f)",
            len(rag_chunks),
            rag_chunks[0]["relevance_score"] if rag_chunks else 0.0,
        )

    except Exception as exc:
        logger.error("RAG Agent failed: %s", exc, exc_info=True)
        state["rag_context"] = []
        state["rag_error"] = str(exc)
        state["messages"].append(ToolMessage(tool_call_id=tool_call_id, name="run_rag", content=f"RAG search failed: {exc}"))

    state["agent_status"] = "RAG search complete."
    return state


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _build_search_query(state: OmniSenseState) -> str:
    """
    Build an enriched search query by prepending equipment context.

    Adding equipment type/ID narrows the FAISS search to
    domain-relevant chunks (e.g. "Rolling Mill: bearing noise").

    Args:
        state: Pipeline state containing query and equipment info.

    Returns:
        str: Enriched query string for vector similarity search.
    """
    query = state.get("query", "")

    parts: list[str] = []
    if state.get("equipment_type"):
        parts.append(state["equipment_type"])
    if state.get("equipment_id"):
        parts.append(state["equipment_id"])

    if parts:
        prefix = " ".join(parts)
        return f"{prefix}: {query}"

    return query
