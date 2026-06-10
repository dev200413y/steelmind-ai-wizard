"""
SteelMind AI Wizard — Embeddings Utility
==========================================
Singleton loader for the sentence-transformers embedding model.
Used by RAG Agent and Knowledge Base Indexer.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Embedding model name
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Singleton instance
_embeddings_instance = None


def get_embeddings():
    """
    Get or create the HuggingFace embeddings model singleton.

    Uses sentence-transformers/all-MiniLM-L6-v2 which:
    - Runs locally (no API cost)
    - Fast inference on CPU
    - 384-dimensional embeddings
    - Good for semantic similarity search

    Returns:
        HuggingFaceEmbeddings instance
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        logger.info(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("✅ Embedding model loaded successfully")

    return _embeddings_instance


def embed_text(text: str) -> list:
    """
    Embed a single text string into a vector.

    Args:
        text: Text to embed

    Returns:
        List of floats (384-dimensional vector)
    """
    embeddings = get_embeddings()
    return embeddings.embed_query(text)


def embed_documents(texts: list) -> list:
    """
    Embed a list of text strings into vectors.

    Args:
        texts: List of texts to embed

    Returns:
        List of vectors (each 384-dimensional)
    """
    embeddings = get_embeddings()
    return embeddings.embed_documents(texts)
