"""
SteelMind AI Wizard — Knowledge Base Indexer
=============================================
Indexes all PDF/TXT documents into a FAISS vector store
for the RAG Agent to search.

Run:
    python src/knowledge_base/index_docs.py

Outputs:
    src/knowledge_base/faiss_index/index.faiss
    src/knowledge_base/faiss_index/index.pkl
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Paths
KB_DIR = Path(__file__).parent
DOCS_DIR = KB_DIR / "documents"
FAISS_INDEX_DIR = KB_DIR / "faiss_index"

# Chunking config
CHUNK_SIZE = 500        # tokens per chunk
CHUNK_OVERLAP = 50      # overlap for context continuity

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_documents() -> list:
    """
    Load all PDF and TXT documents from the documents/ folder.

    Returns:
        List of LangChain Document objects
    """
    from langchain_community.document_loaders import PyPDFLoader, TextLoader

    all_docs = []
    doc_files = list(DOCS_DIR.glob("*.pdf")) + list(DOCS_DIR.glob("*.txt"))

    if not doc_files:
        logger.warning(f"⚠️  No documents found in {DOCS_DIR}")
        logger.info("📄 Generating knowledge documents first...")

        # Generate synthetic documents
        sys.path.insert(0, str(KB_DIR.parent.parent))
        from src.data.generate_knowledge_docs import generate_all_documents
        generate_all_documents()
        doc_files = list(DOCS_DIR.glob("*.pdf")) + list(DOCS_DIR.glob("*.txt"))

    for doc_path in doc_files:
        try:
            if doc_path.suffix == ".pdf":
                loader = PyPDFLoader(str(doc_path))
            elif doc_path.suffix == ".txt":
                loader = TextLoader(str(doc_path), encoding="utf-8")
            else:
                continue

            docs = loader.load()

            # Add source metadata
            for doc in docs:
                doc.metadata["source"] = doc_path.name
                if "page" not in doc.metadata:
                    doc.metadata["page"] = 0

            all_docs.extend(docs)
            logger.info(f"   📄 Loaded: {doc_path.name} ({len(docs)} pages)")

        except Exception as e:
            logger.error(f"   ❌ Failed to load {doc_path.name}: {e}")

    logger.info(f"📚 Total documents loaded: {len(all_docs)}")
    return all_docs


def split_documents(docs: list) -> list:
    """
    Split documents into smaller chunks for embedding.

    Uses RecursiveCharacterTextSplitter which tries to split
    on paragraph boundaries first, then sentences, then words.

    Args:
        docs: List of LangChain Document objects

    Returns:
        List of chunked Document objects
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(docs)

    # Add unique chunk IDs
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i:04d}"

    logger.info(f"✂️  Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def create_faiss_index(chunks: list) -> None:
    """
    Create FAISS vector index from document chunks.

    Embeds each chunk using sentence-transformers/all-MiniLM-L6-v2
    and stores the vectors in a FAISS index on disk.

    Args:
        chunks: List of chunked Document objects
    """
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings

    logger.info(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    logger.info("📐 Creating FAISS index (this may take a minute)...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # Save to disk
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(FAISS_INDEX_DIR))

    logger.info(f"✅ FAISS index saved to: {FAISS_INDEX_DIR}")
    logger.info(f"   📊 Total vectors: {vectorstore.index.ntotal}")


def test_search(query: str = "bearing replacement procedure") -> None:
    """
    Test the FAISS index with a sample query.

    Args:
        query: Test search query
    """
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings

    logger.info(f"\n🔍 Testing search with: '{query}'")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
    )

    vectorstore = FAISS.load_local(
        str(FAISS_INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    results = vectorstore.similarity_search_with_score(query, k=3)

    for i, (doc, score) in enumerate(results):
        logger.info(f"\n   📌 Result {i + 1} (score: {score:.4f})")
        logger.info(f"   Source: {doc.metadata.get('source', 'unknown')}, Page: {doc.metadata.get('page', 0)}")
        logger.info(f"   Content: {doc.page_content[:200]}...")


def index_all():
    """
    Full indexing pipeline: Load → Split → Embed → Save FAISS index.
    """
    logger.info("=" * 60)
    logger.info("🏭 SteelMind AI Wizard — Knowledge Base Indexer")
    logger.info("=" * 60)

    # Ensure directories exist
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load documents
    docs = load_documents()
    if not docs:
        logger.error("❌ No documents to index. Exiting.")
        return

    # Step 2: Split into chunks
    chunks = split_documents(docs)

    # Step 3: Create FAISS index
    create_faiss_index(chunks)

    # Step 4: Test search
    test_search("bearing replacement procedure for Rolling Mill")
    test_search("blast furnace tuyere maintenance")

    logger.info("\n" + "=" * 60)
    logger.info("🎉 Knowledge base indexed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    index_all()
