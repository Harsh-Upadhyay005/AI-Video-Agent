"""
Cross-Encoder Reranker for RAG Pipeline.

Uses HuggingFace cross-encoder models to rerank retrieved documents
for better relevance. Cross-encoders jointly encode query + document
pairs, providing better ranking than separate embeddings.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
- Fast inference (~10ms per doc on CPU)
- Good accuracy for information retrieval tasks
- Trained on MS MARCO passage ranking dataset
"""

from typing import Optional
from core.logger import get_logger

logger = get_logger(__name__)

# Model configuration
DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Import flags
_CROSS_ENCODER_AVAILABLE = False
_CrossEncoderReranker = None
_HuggingFaceCrossEncoder = None

try:
    from langchain.retrievers.document_compressors import CrossEncoderReranker
    from langchain_community.cross_encoders import HuggingFaceCrossEncoder
    _CROSS_ENCODER_AVAILABLE = True
    _CrossEncoderReranker = CrossEncoderReranker
    _HuggingFaceCrossEncoder = HuggingFaceCrossEncoder
    logger.info("[Reranker] Cross-encoder imports successful")
except ImportError as e:
    logger.warning(f"[Reranker] Cross-encoder not available: {e}")
    logger.warning("[Reranker] Reranking will be disabled")


def is_reranker_available() -> bool:
    """Check if cross-encoder reranking is available."""
    return _CROSS_ENCODER_AVAILABLE


def get_cross_encoder_reranker(
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
    top_n: int = 5
):
    """
    Create a cross-encoder reranker.
    
    The reranker scores each (query, document) pair and returns
    the top_n highest-scoring documents.
    
    Args:
        model_name: HuggingFace cross-encoder model name
        top_n: Number of top documents to return after reranking
        
    Returns:
        CrossEncoderReranker instance or None if unavailable
    """
    if not _CROSS_ENCODER_AVAILABLE:
        logger.warning("[Reranker] Cross-encoder not available, skipping reranker")
        return None
    
    try:
        logger.info(f"[Reranker] Initializing cross-encoder: {model_name}")
        
        # Create HuggingFace cross-encoder
        model = _HuggingFaceCrossEncoder(model_name=model_name)
        
        # Wrap in reranker
        reranker = _CrossEncoderReranker(
            model=model,
            top_n=top_n
        )
        
        logger.info(f"[Reranker] ✓ Reranker initialized (top_n={top_n})")
        return reranker
        
    except Exception as e:
        logger.error(f"[Reranker] Failed to initialize reranker: {e}")
        return None


def get_reranked_retriever(
    base_retriever,
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
    top_n: int = 5
):
    """
    Wrap a retriever with cross-encoder reranking.
    
    Flow:
    1. Base retriever fetches candidates (e.g., 20 docs)
    2. Cross-encoder scores each (query, doc) pair
    3. Return top_n highest-scoring docs
    
    Args:
        base_retriever: Base retriever (hybrid or dense)
        model_name: Cross-encoder model name
        top_n: Number of final documents after reranking
        
    Returns:
        ContextualCompressionRetriever with reranking or base retriever if unavailable
    """
    if not _CROSS_ENCODER_AVAILABLE:
        logger.warning("[Reranker] Reranking unavailable, using base retriever")
        return base_retriever
    
    try:
        from langchain.retrievers import ContextualCompressionRetriever
        
        # Get cross-encoder reranker
        reranker = get_cross_encoder_reranker(
            model_name=model_name,
            top_n=top_n
        )
        
        if reranker is None:
            logger.warning("[Reranker] Failed to create reranker, using base retriever")
            return base_retriever
        
        # Wrap base retriever with reranking
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=reranker,
            base_retriever=base_retriever
        )
        
        logger.info(f"[Reranker] ✓ Created reranked retriever (top_n={top_n})")
        return compression_retriever
        
    except Exception as e:
        logger.error(f"[Reranker] Failed to create reranked retriever: {e}")
        logger.warning("[Reranker] Falling back to base retriever")
        return base_retriever


# Singleton cache for reranker model
_reranker_cache: Optional[any] = None


def get_cached_reranker(
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
    top_n: int = 5
):
    """
    Get cached reranker instance to avoid reloading model.
    
    Args:
        model_name: Cross-encoder model name
        top_n: Number of top documents
        
    Returns:
        Cached reranker or newly created one
    """
    global _reranker_cache
    
    if _reranker_cache is None:
        _reranker_cache = get_cross_encoder_reranker(
            model_name=model_name,
            top_n=top_n
        )
        if _reranker_cache:
            logger.info("[Reranker] ✓ Cached reranker initialized")
    
    return _reranker_cache
