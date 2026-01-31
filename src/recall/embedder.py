"""Embedding module using sentence-transformers."""

import numpy as np
from typing import List, Optional
from pathlib import Path

# Lazy load to speed up CLI startup
_model = None
_model_name = "all-MiniLM-L6-v2"


def get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        import logging
        import warnings
        
        # Suppress verbose model loading output
        logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
        warnings.filterwarnings("ignore", category=FutureWarning)
        
        from sentence_transformers import SentenceTransformer
        
        # Use cache dir in ~/.recall
        cache_dir = Path.home() / ".recall" / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        _model = SentenceTransformer(_model_name, cache_folder=str(cache_dir))
    return _model


def embed_text(text: str) -> np.ndarray:
    """Embed a single text string into a vector."""
    model = get_model()
    return model.encode(text, convert_to_numpy=True)


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed multiple texts into vectors."""
    model = get_model()
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=len(texts) > 10)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cosine_similarities(query: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    """Compute cosine similarities between a query and multiple vectors."""
    # Normalize
    query_norm = query / np.linalg.norm(query)
    vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.dot(vectors_norm, query_norm)
