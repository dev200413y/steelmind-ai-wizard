"""
OmniSense AI Wizard — Embeddings Utility
==========================================
Singleton loader for the embedding model.
Used by RAG Agent and Knowledge Base Indexer.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton instance
_embeddings_instance = None

def get_embeddings():
    """
    Get or create the Google Gemini embeddings model singleton.
    Uses models/text-embedding-004 which is extremely fast, free, and uses 0 RAM locally.
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        import os
        from dotenv import load_dotenv

        load_dotenv()
        
        # Verify API key exists
        if not os.getenv("GOOGLE_API_KEY"):
            logger.warning("GOOGLE_API_KEY not found. Embeddings will fail.")

        logger.info("🧠 Loading Gemini embedding model: models/text-embedding-004")
        _embeddings_instance = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        logger.info("✅ Gemini Embedding model loaded successfully")

    return _embeddings_instance

def embed_text(text: str) -> list:
    embeddings = get_embeddings()
    return embeddings.embed_query(text)

def embed_documents(texts: list) -> list:
    embeddings = get_embeddings()
    return embeddings.embed_documents(texts)
