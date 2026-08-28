"""
Query Router - Intelligent routing for RAG queries.

Detects query intent and routes to appropriate handler:
1. Whole-content summarization (map-reduce over full document)
2. Normal RAG retrieval (top-k semantic search)

Works uniformly for PDF documents and audio/video transcripts.
"""

import re
from typing import Dict, Any, Optional, List
from enum import Enum

from core.logger import get_logger

logger = get_logger(__name__)


class QueryType(Enum):
    """Types of user queries."""
    WHOLE_CONTENT_SUMMARY = "whole_content_summary"  # Needs full document
    SPECIFIC_QUESTION = "specific_question"  # Needs RAG retrieval
    EXTRACTION = "extraction"  # Needs targeted retrieval


class QueryIntent:
    """
    Analyzed query intent with routing information.
    """
    
    def __init__(
        self,
        query_type: QueryType,
        original_query: str,
        constraint: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize query intent.
        
        Args:
            query_type: Type of query
            original_query: Original user query
            constraint: Optional constraints (word_limit, format, etc.)
        """
        self.query_type = query_type
        self.original_query = original_query
        self.constraint = constraint or {}
    
    def __repr__(self):
        return f"QueryIntent(type={self.query_type.value}, constraint={self.constraint})"


class QueryRouter:
    """
    Routes queries to appropriate processing pipeline.
    
    Detects:
    - Whole-content summarization requests
    - Explicit constraints (word limits, bullet points, etc.)
    - Specific questions requiring retrieval
    """
    
    # Patterns for whole-content requests
    SUMMARY_PATTERNS = [
        r'\bsummar(y|ize|ization)\b',
        r'\boverview\b',
        r'\bmain\s+(points?|ideas?|topics?)\b',
        r'\bkey\s+(points?|takeaways?|insights?)\b',
        r'\bgive\s+me\s+(the|a)\s+(main|key|overall)',
        r'\bwhat\s+(is|are)\s+the\s+main',
        r'\btell\s+me\s+about',
        r'\bgeneral\s+idea\b',
        r'\bhighlights?\b',
        r'\bsynops(is|es)\b',
        r'\bgist\b',
        r'\bexecutive\s+summary\b',
        r'\bquick\s+summary\b',
    ]
    
    # Patterns for extraction requests
    EXTRACTION_PATTERNS = [
        r'\blist\s+(all|the)',
        r'\bextract\b',
        r'\bfind\s+all',
        r'\benumerate\b',
        r'\bidentify\s+all\b',
    ]
    
    # Patterns for explicit constraints
    WORD_LIMIT_PATTERN = r'(\d+)\s*[-–]?\s*word'
    BULLET_PATTERN = r'\bbullet\s+(points?|list)\b|\bbulleted\b'
    NUMBERED_PATTERN = r'\bnumbered\s+list\b'
    
    def __init__(self):
        """Initialize query router."""
        logger.info("[QueryRouter] Initialized")
    
    def analyze_query(self, query: str) -> QueryIntent:
        """
        Analyze query and determine routing.
        
        Args:
            query: User's query text
            
        Returns:
            QueryIntent with routing information
        """
        query_lower = query.lower()
        
        # Check for word limit constraint
        word_limit = None
        word_match = re.search(self.WORD_LIMIT_PATTERN, query_lower)
        if word_match:
            word_limit = int(word_match.group(1))
            logger.info(f"[QueryRouter] Detected word limit: {word_limit}")
        
        # Check for format constraints
        constraints = {}
        if word_limit:
            constraints['word_limit'] = word_limit
        
        if re.search(self.BULLET_PATTERN, query_lower):
            constraints['format'] = 'bullets'
            logger.info("[QueryRouter] Detected bullet point format")
        elif re.search(self.NUMBERED_PATTERN, query_lower):
            constraints['format'] = 'numbered'
            logger.info("[QueryRouter] Detected numbered list format")
        
        # Determine query type
        
        # 1. Check for whole-content summarization
        for pattern in self.SUMMARY_PATTERNS:
            if re.search(pattern, query_lower):
                logger.info(f"[QueryRouter] Matched summary pattern: {pattern}")
                return QueryIntent(
                    query_type=QueryType.WHOLE_CONTENT_SUMMARY,
                    original_query=query,
                    constraint=constraints
                )
        
        # 2. Check for extraction requests (often needs more chunks)
        for pattern in self.EXTRACTION_PATTERNS:
            if re.search(pattern, query_lower):
                logger.info(f"[QueryRouter] Matched extraction pattern: {pattern}")
                # Extraction with constraints might need full content
                if constraints.get('word_limit') or constraints.get('format'):
                    return QueryIntent(
                        query_type=QueryType.WHOLE_CONTENT_SUMMARY,
                        original_query=query,
                        constraint=constraints
                    )
                return QueryIntent(
                    query_type=QueryType.EXTRACTION,
                    original_query=query,
                    constraint=constraints
                )
        
        # 3. Default: specific question needing retrieval
        logger.info("[QueryRouter] Classified as specific question (RAG retrieval)")
        return QueryIntent(
            query_type=QueryType.SPECIFIC_QUESTION,
            original_query=query,
            constraint=constraints
        )
    
    def should_use_full_content(self, query_intent: QueryIntent) -> bool:
        """
        Determine if query requires full content processing.
        
        Args:
            query_intent: Analyzed query intent
            
        Returns:
            True if full content should be used (map-reduce)
        """
        return query_intent.query_type == QueryType.WHOLE_CONTENT_SUMMARY
    
    def get_retrieval_k(self, query_intent: QueryIntent) -> int:
        """
        Get appropriate number of chunks for retrieval.
        
        Args:
            query_intent: Analyzed query intent
            
        Returns:
            Number of chunks to retrieve
        """
        if query_intent.query_type == QueryType.EXTRACTION:
            # Extraction might need more context
            return 15
        elif query_intent.query_type == QueryType.SPECIFIC_QUESTION:
            # Normal questions use default
            return 5
        else:
            # Shouldn't be called for whole-content
            return 10


# Singleton instance
_query_router_instance = None


def get_query_router() -> QueryRouter:
    """Get singleton query router instance."""
    global _query_router_instance
    
    if _query_router_instance is None:
        _query_router_instance = QueryRouter()
    
    return _query_router_instance
