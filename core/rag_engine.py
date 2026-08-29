"""
RAG Engine - Unified Retrieval and Question Answering.
Handles both PDF documents and audio/video transcripts uniformly.

Architecture:
1. Content ingestion creates vector store (PDF or transcript)
2. User asks question
3. RAG retrieves relevant chunks
4. LLM answers using ONLY retrieved chunks (not entire document)

CRITICAL: LLM is used ONLY after retrieval, never on entire documents.
LAZY INITIALIZATION: LLM service is NOT loaded during ingestion.
"""

import os
from typing import List, Optional, Dict, Any

try:
    from langchain_core.documents import Document
except Exception:
    Document = None

from core.vector_store import build_vector_store, load_vector_store, get_retriever, _load_documents
from core.source_types import IngestionResult, ProcessingMetadata
# NOTE: llm_service is imported lazily when needed, not during ingestion
from core.logger import get_logger

logger = get_logger(__name__)


def format_docs(docs):
    """Format retrieved documents for display."""
    return "\n\n".join([doc.page_content for doc in docs])


def build_rag_chain(
    text: str,
    metadata: Optional[ProcessingMetadata] = None,
    video_id: str = None,
    **kwargs
):
    """
    Build RAG chain for PDF or transcript content.
    
    This function:
    1. Creates vector store from text content
    2. Persists documents for BM25 retrieval
    3. Returns enhanced RAG chain for querying with hybrid search
    
    NO LLM ANALYSIS during this step - just indexing.
    LLM is used LATER when user asks questions.
    
    Args:
        text: Full text content (PDF or transcript)
        metadata: Optional ProcessingMetadata with source info
        video_id: Optional ID for backward compatibility
        **kwargs: Additional metadata for backward compatibility
    
    Returns:
        EnhancedRAGChain for querying
    """
    text_length = len(text)
    logger.info(f"[RAG] Building vector store: {text_length} chars")
    
    if text_length > 500000:  # ~125k tokens
        logger.warning(
            f"[RAG] Very long content ({text_length} chars). "
            "Vector store creation may take time."
        )
    
    # Build vector store metadata
    vector_metadata = kwargs.get('metadata', {})
    
    if metadata:
        vector_metadata.update({
            'source_type': metadata.source_type.value,
            'source': metadata.source,
            'language': metadata.language or 'unknown',
            'char_count': metadata.char_count
        })
    
    if video_id:
        vector_metadata['video_id'] = video_id
    
    # Create vector store (local processing - embeddings only, no LLM)
    logger.info("[RAG] Creating embeddings and building vector store...")
    logger.info("[RAG] No LLM calls during vector store creation")
    
    vector_store = build_vector_store(text, metadata=vector_metadata)
    
    # Load persisted documents for BM25
    docs = _load_documents(video_id)
    if docs:
        logger.info(f"[RAG] ✓ Loaded {len(docs)} documents for hybrid search")
    else:
        logger.warning("[RAG] No documents loaded - hybrid search will fallback to dense-only")
    
    logger.info("[RAG] ✓ Vector store created successfully")
    
    # Create enhanced RAG chain with documents
    enhanced_chain = EnhancedRAGChain(
        vector_store=vector_store,
        source_id=video_id,
        metadata=metadata,
        docs=docs
    )
    
    return enhanced_chain


class EnhancedRAGChain:
    """
    Enhanced RAG chain for querying indexed content.
    Works uniformly for PDF documents and audio/video transcripts.
    
    Query flow:
    User question → Retrieve relevant chunks → LLM answers using chunks
    
    CRITICAL: LLM receives ONLY retrieved chunks, never entire document.
    
    ARCHITECTURE: LLM initialization is LAZY - only happens when user asks a question.
    """
    
    def __init__(
        self,
        vector_store,
        source_id: str = None,
        metadata: Optional[ProcessingMetadata] = None,
        docs: Optional[List[Document]] = None
    ):
        """
        Initialize enhanced RAG chain.
        
        Args:
            vector_store: Chroma vector store with indexed content
            source_id: Optional source identifier
            metadata: Optional ProcessingMetadata
            docs: Optional list of Document chunks (for BM25 retrieval)
        """
        self.vector_store = vector_store
        self.source_id = source_id
        self.metadata = metadata
        self.docs = docs  # Store for hybrid retrieval
        
        # LAZY INITIALIZATION: Do NOT initialize orchestrator here
        # It will be initialized when user asks first question
        self._orchestrator = None
        
        # Conversation memory
        self.conversation_history = []
        self.max_history = 5
        
        source_type = metadata.source_type.value if metadata else "unknown"
        logger.info(f"[EnhancedRAG] Initialized for {source_type} content")
        logger.info("[EnhancedRAG] Vector store ready, LLM will be initialized on first query")
    
    @property
    def orchestrator(self):
        """Lazy initialization of RAG orchestrator."""
        if self._orchestrator is None:
            logger.info("[EnhancedRAG] Initializing LLM service for query (lazy initialization)")
            from core.llm_service import get_rag_orchestrator
            self._orchestrator = get_rag_orchestrator()
            logger.info("[EnhancedRAG] LLM service ready for queries")
        return self._orchestrator
    
    def ask(self, question: str, top_k: int = 5, debug: bool = False) -> Dict[str, Any]:
        """
        Ask a question about the indexed content.
        
        Intelligently routes query to:
        1. Whole-content summarization (map-reduce) for requests like "summarize", "give me 50-word summary"
        2. Normal RAG retrieval for specific questions
        
        Flow for whole-content:
        1. Detect summarization intent
        2. Retrieve ALL chunks (not just top-k)
        3. Hierarchically summarize using map-reduce
        4. Apply user constraints (word limits, format)
        
        Flow for specific questions:
        1. Retrieve relevant chunks (top-k)
        2. Send ONLY retrieved chunks to LLM
        3. Return answer with sources
        
        Args:
            question: User's question
            top_k: Number of chunks to retrieve (for specific questions)
            debug: Enable debug logging
            
        Returns:
            Dict with answer, sources, retrieved_chunks, query_type
        """
        logger.info(f"[EnhancedRAG] Question: {question[:100]}...")
        
        # Import router and processor
        from core.query_router import get_query_router, QueryType
        from core.whole_content_processor import get_whole_content_processor
        
        # Analyze query intent
        router = get_query_router()
        query_intent = router.analyze_query(question)
        
        logger.info(f"[EnhancedRAG] Query intent: {query_intent}")
        
        # Route based on intent
        if query_intent.query_type == QueryType.WHOLE_CONTENT_SUMMARY:
            # Use whole-content processor for summarization
            logger.info("[EnhancedRAG] Routing to whole-content processor")
            
            processor = get_whole_content_processor()
            answer = processor.process_summary_request(
                vector_store=self.vector_store,
                query=question,
                constraint=query_intent.constraint,
                metadata=self.metadata.to_dict() if self.metadata else None
            )
            
            result = {
                'answer': answer,
                'sources': [],  # Whole content doesn't cite specific chunks
                'retrieved_chunks': 'all',
                'query_type': 'whole_content_summary'
            }
            
        else:
            # Use normal RAG retrieval for specific questions
            logger.info(f"[EnhancedRAG] Routing to RAG retrieval (top_k={top_k})")
            
            # Adjust top_k for extraction queries
            if query_intent.query_type == QueryType.EXTRACTION:
                top_k = router.get_retrieval_k(query_intent)
                logger.info(f"[EnhancedRAG] Adjusted top_k to {top_k} for extraction query")
            
            # Create hybrid + reranked retriever if documents available
            custom_retriever = None
            if self.docs:
                try:
                    from core.vector_store import get_reranked_retriever
                    logger.info("[EnhancedRAG] Creating hybrid + reranked retriever")
                    custom_retriever = get_reranked_retriever(
                        vector_store=self.vector_store,
                        docs=self.docs,
                        fetch_k=top_k * 4,  # Fetch 4x for reranking
                        top_n=top_k,
                        use_hybrid=True
                    )
                except Exception as e:
                    logger.warning(f"[EnhancedRAG] Failed to create hybrid retriever: {e}")
                    logger.warning("[EnhancedRAG] Falling back to dense-only retrieval")
            else:
                logger.info("[EnhancedRAG] No documents available - using dense-only retrieval")
            
            result = self.orchestrator.answer_with_retrieval(
                vector_store=self.vector_store,
                question=question,
                top_k=top_k,
                conversation_history=self.conversation_history,
                custom_retriever=custom_retriever
            )
            
            result['query_type'] = query_intent.query_type.value
        
        # Update conversation history
        if result.get('answer'):
            self._add_to_history(question, result['answer'])
        
        if debug:
            logger.info(f"[EnhancedRAG] Result: {result}")
        
        return result
    
    def _add_to_history(self, question: str, answer: str):
        """Add Q&A pair to conversation history."""
        self.conversation_history.append({
            "question": question,
            "answer": answer
        })
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def invoke(self, input_data: Any) -> str:
        """
        Invoke chain with question (for backward compatibility).
        
        Args:
            input_data: Question string or dict with 'question' key
            
        Returns:
            Answer string
        """
        if isinstance(input_data, dict):
            question = input_data.get('question') or input_data.get('input', '')
        else:
            question = str(input_data)
        
        result = self.ask(question)
        return result.get('answer', '')
    
    def get_metadata(self) -> Optional[ProcessingMetadata]:
        """Get source metadata."""
        return self.metadata


def ask_question(rag_chain: EnhancedRAGChain, question: str, top_k: int = 5, debug: bool = False) -> str:
    """
    Ask a question using RAG chain.
    
    This is the main entry point for question answering.
    Intelligently routes to:
    - Whole-content summarization for "summarize", "give me 50 words", etc.
    - Normal RAG retrieval for specific questions
    
    Args:
        rag_chain: EnhancedRAGChain instance
        question: User's question
        top_k: Number of chunks to retrieve (for specific questions)
        debug: Enable debug logging
        
    Returns:
        Answer string
    """
    result = rag_chain.ask(question, top_k=top_k, debug=debug)
    return result.get('answer', '')


def get_similar_chunks(
    rag_chain: EnhancedRAGChain,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve similar chunks without LLM processing.
    Useful for debugging or custom processing.
    
    Args:
        rag_chain: EnhancedRAGChain instance
        query: Search query
        top_k: Number of chunks to retrieve
        
    Returns:
        List of dicts with content and metadata
    """
    logger.info(f"[RAG] Retrieving {top_k} similar chunks")
    
    try:
        retriever = rag_chain.vector_store.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.get_relevant_documents(query)
        
        chunks = []
        for doc in docs:
            chunks.append({
                'content': doc.page_content,
                'metadata': doc.metadata if hasattr(doc, 'metadata') else {}
            })
        
        logger.info(f"[RAG] Retrieved {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        logger.error(f"[RAG] Retrieval error: {e}")
        return []


def load_rag_chain(video_id: str = None):
    """
    Load RAG chain from persistent vector store.
    
    Args:
        video_id: Optional video/source ID
        
    Returns:
        EnhancedRAGChain or None
    """
    try:
        vector_store = load_vector_store()
        
        if vector_store is None:
            return None
        
        # Create enhanced chain
        enhanced_chain = EnhancedRAGChain(
            vector_store=vector_store,
            source_id=video_id,
            metadata=None
        )
        
        return enhanced_chain
        
    except Exception as e:
        logger.error(f"[RAG] Error loading chain: {e}")
        return None
