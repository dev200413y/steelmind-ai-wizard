# RAG Agent

## Role
Searches through all indexed knowledge documents (equipment manuals, SOPs, maintenance records, failure reports, spare parts catalog) to retrieve the most relevant context for the current query. Provides grounded, traceable information to the Diagnostic Agent.

## Read First
- `references/schemas.md` — RAGContext schema
- `references/data_guide.md` — What documents are indexed
- `assets/prompts.md` — Not needed here (no LLM call in RAG retrieval)

---

## Input
```python
state["query"]          # User's question (text or voice-transcribed)
state["equipment_type"] # Optional — narrows search
state["equipment_id"]   # Optional — narrows search further
```

## Output — Updates State
```python
state["rag_context"] = [
    {
        "content": str,      # Relevant text chunk
        "source": str,       # Document filename
        "page": int,         # Page number
        "relevance_score": float,  # Cosine similarity score
        "chunk_id": str      # Unique chunk identifier
    },
    # Top 5 most relevant chunks
]
```

---

## Implementation
```python
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

FAISS_INDEX_PATH = "src/knowledge_base/faiss_index"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def run_rag(state: SteelMindState) -> SteelMindState:
    """
    Retrieve top-5 relevant knowledge chunks for the current query.
    Uses FAISS vector similarity search with MiniLM embeddings.
    """
    # Load embeddings (runs locally — no API cost)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    # Load FAISS index
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    # Build search query — add equipment context if available
    search_query = state["query"]
    if state.get("equipment_type"):
        search_query = f"{state['equipment_type']}: {search_query}"
    
    # Retrieve top 5 chunks
    docs = vectorstore.similarity_search_with_score(search_query, k=5)
    
    state["rag_context"] = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page", 0),
            "relevance_score": float(score),
            "chunk_id": doc.metadata.get("chunk_id", "")
        }
        for doc, score in docs
    ]
    return state
```

---

## Knowledge Base Indexing Script
```python
# Run once: python src/knowledge_base/index_docs.py
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

DOCS_PATH = "src/knowledge_base/documents/"
CHUNK_SIZE = 500      # tokens per chunk
CHUNK_OVERLAP = 50    # overlap for context continuity

def index_documents():
    """
    Load all PDFs and TXTs from documents/ folder.
    Split into chunks. Embed. Save FAISS index.
    Run once before starting the application.
    """
    # Load documents
    # Split into chunks
    # Embed with MiniLM
    # Save FAISS index to disk
```

---

## Documents Indexed
See `references/data_guide.md` for full list. Key documents:
- Blast Furnace Operations Manual (PDF)
- Rolling Mill Bearing Replacement SOP (PDF)
- Hydraulic System Maintenance SOP (PDF)
- Spare Parts Catalog — 200+ parts (CSV converted to TXT)
- Failure Analysis Report — EAF Historical (PDF)
- Maintenance Schedule Template (PDF)

---

## Error Handling
```python
try:
    docs = vectorstore.similarity_search_with_score(search_query, k=5)
except Exception as e:
    # Return empty context — Diagnostic Agent will work with query only
    state["rag_context"] = []
    state["rag_error"] = str(e)
return state
```

---

## Test Cases
```python
def test_rag_returns_relevant_chunks():
    state = {"query": "bearing replacement procedure", "equipment_type": "Rolling Mill"}
    result = run_rag(state)
    assert len(result["rag_context"]) > 0
    assert result["rag_context"][0]["relevance_score"] > 0.5

def test_rag_empty_index():
    # Should not crash — return empty list
    state = {"query": "unknown query xyz"}
    result = run_rag(state)
    assert isinstance(result["rag_context"], list)
```
