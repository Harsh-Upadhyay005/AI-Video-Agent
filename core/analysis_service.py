"""
Optional Analysis Service - RAG-based Analysis.

This service provides OPTIONAL analysis features that users can explicitly request:
- Key decisions extraction
- Action items extraction
- Open questions extraction
- Content summarization

CRITICAL ARCHITECTURE:
1. User explicitly requests analysis (button click, API call)
2. Service retrieves relevant chunks using RAG
3. Service sends ONLY retrieved chunks to LLM (not entire document)
4. Returns structured results

This is NOT automatic during ingestion.
This is ONLY triggered by explicit user request.
"""

from typing import Dict, Any, Optional
from enum import Enum

from core.llm_service import get_rag_orchestrator, AnalysisRequest
from core.logger import get_logger

logger = get_logger(__name__)


class AnalysisType(Enum):
    """Types of analysis that can be requested."""
    KEY_DECISIONS = "key_decisions"
    ACTION_ITEMS = "action_items"
    OPEN_QUESTIONS = "open_questions"
    SUMMARY = "summary"
    TOPICS = "topics"
    CONCEPTS = "concepts"


class AnalysisService:
    """
    Service for optional document/transcript analysis using RAG.
    
    IMPORTANT: This is NOT called automatically during ingestion.
    This is ONLY used when user explicitly requests analysis.
    """
    
    def __init__(self):
        """Initialize analysis service."""
        self.orchestrator = get_rag_orchestrator()
        logger.info("[AnalysisService] Initialized - RAG-based analysis only")
    
    def analyze(
        self,
        vector_store,
        analysis_type: AnalysisType,
        top_k: int = 20,
        custom_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform analysis using RAG retrieval.
        
        Flow:
        1. Retrieve relevant chunks from vector store
        2. Send ONLY retrieved chunks to LLM
        3. Return structured analysis
        
        Args:
            vector_store: Vector store with indexed content
            analysis_type: Type of analysis to perform
            top_k: Number of chunks to retrieve
            custom_query: Optional custom retrieval query
            
        Returns:
            Dict with analysis results
        """
        logger.info(f"[AnalysisService] Starting {analysis_type.value} analysis")
        logger.info(f"[AnalysisService] Will retrieve top {top_k} relevant chunks")
        logger.info("[AnalysisService] LLM will receive ONLY retrieved chunks, not entire document")
        
        try:
            # Create analysis request
            analysis_request = AnalysisRequest(
                analysis_type=analysis_type.value,
                vector_store_key="",  # Not needed, we pass vector_store directly
                query=custom_query,
                top_k=top_k
            )
            
            # Perform analysis using RAG orchestrator
            result = self.orchestrator.analyze_with_retrieval(
                vector_store=vector_store,
                analysis_request=analysis_request
            )
            
            logger.info(f"[AnalysisService] ✓ {analysis_type.value} analysis complete")
            
            return {
                "analysis_type": analysis_type.value,
                "result": result,
                "chunks_analyzed": top_k,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[AnalysisService] Analysis failed: {e}", exc_info=True)
            return {
                "analysis_type": analysis_type.value,
                "result": f"Analysis failed: {str(e)}",
                "chunks_analyzed": 0,
                "success": False,
                "error": str(e)
            }
    
    def extract_key_decisions(
        self,
        vector_store,
        top_k: int = 20
    ) -> str:
        """
        Extract key decisions using RAG.
        
        Args:
            vector_store: Vector store with indexed content
            top_k: Number of chunks to retrieve
            
        Returns:
            Key decisions text
        """
        logger.info("[AnalysisService] Extracting key decisions via RAG")
        
        result = self.analyze(
            vector_store=vector_store,
            analysis_type=AnalysisType.KEY_DECISIONS,
            top_k=top_k,
            custom_query="decisions made, conclusions reached, determinations, choices"
        )
        
        return result.get('result', 'No key decisions found.')
    
    def extract_action_items(
        self,
        vector_store,
        top_k: int = 20
    ) -> str:
        """
        Extract action items using RAG.
        
        Args:
            vector_store: Vector store with indexed content
            top_k: Number of chunks to retrieve
            
        Returns:
            Action items text
        """
        logger.info("[AnalysisService] Extracting action items via RAG")
        
        result = self.analyze(
            vector_store=vector_store,
            analysis_type=AnalysisType.ACTION_ITEMS,
            top_k=top_k,
            custom_query="tasks, action items, to-do, follow-up, next steps, assignments"
        )
        
        return result.get('result', 'No action items found.')
    
    def extract_open_questions(
        self,
        vector_store,
        top_k: int = 20
    ) -> str:
        """
        Extract open questions using RAG.
        
        Args:
            vector_store: Vector store with indexed content
            top_k: Number of chunks to retrieve
            
        Returns:
            Open questions text
        """
        logger.info("[AnalysisService] Extracting open questions via RAG")
        
        result = self.analyze(
            vector_store=vector_store,
            analysis_type=AnalysisType.OPEN_QUESTIONS,
            top_k=top_k,
            custom_query="questions, uncertainties, unknowns, unresolved issues, clarifications needed"
        )
        
        return result.get('result', 'No open questions found.')
    
    def generate_summary(
        self,
        vector_store,
        top_k: int = 30
    ) -> str:
        """
        Generate summary using RAG.
        
        Args:
            vector_store: Vector store with indexed content
            top_k: Number of chunks to retrieve
            
        Returns:
            Summary text
        """
        logger.info("[AnalysisService] Generating summary via RAG")
        
        result = self.analyze(
            vector_store=vector_store,
            analysis_type=AnalysisType.SUMMARY,
            top_k=top_k,
            custom_query="main points, key information, important topics, overview"
        )
        
        return result.get('result', 'Summary unavailable.')
    
    def extract_topics(
        self,
        vector_store,
        top_k: int = 40
    ) -> str:
        """
        Extract topics using RAG.
        
        Args:
            vector_store: Vector store with indexed content
            top_k: Number of chunks to retrieve
            
        Returns:
            Topics text
        """
        logger.info("[AnalysisService] Extracting topics via RAG")
        
        result = self.analyze(
            vector_store=vector_store,
            analysis_type=AnalysisType.TOPICS,
            top_k=top_k,
            custom_query="main topics, subjects discussed, themes, areas covered"
        )
        
        return result.get('result', 'No topics identified.')
    
    def batch_analyze(
        self,
        vector_store,
        analysis_types: list[AnalysisType],
        top_k: int = 20
    ) -> Dict[str, Any]:
        """
        Perform multiple analyses in sequence.
        
        Args:
            vector_store: Vector store with indexed content
            analysis_types: List of analysis types to perform
            top_k: Number of chunks to retrieve for each analysis
            
        Returns:
            Dict mapping analysis type to result
        """
        logger.info(f"[AnalysisService] Batch analysis: {len(analysis_types)} types")
        
        results = {}
        
        for analysis_type in analysis_types:
            result = self.analyze(
                vector_store=vector_store,
                analysis_type=analysis_type,
                top_k=top_k
            )
            results[analysis_type.value] = result
        
        logger.info("[AnalysisService] ✓ Batch analysis complete")
        
        return results


# Singleton instance
_analysis_service_instance = None


def get_analysis_service() -> AnalysisService:
    """
    Get singleton analysis service instance.
    
    Returns:
        AnalysisService instance
    """
    global _analysis_service_instance
    
    if _analysis_service_instance is None:
        _analysis_service_instance = AnalysisService()
    
    return _analysis_service_instance


def analyze_content(
    vector_store,
    analysis_type: str,
    top_k: int = 20
) -> str:
    """
    Convenience function for content analysis.
    
    This performs RAG-based analysis (retrieve → LLM).
    
    Args:
        vector_store: Vector store with indexed content
        analysis_type: Type of analysis (key_decisions, action_items, etc.)
        top_k: Number of chunks to retrieve
        
    Returns:
        Analysis result text
    """
    service = get_analysis_service()
    
    # Map string to enum
    type_map = {
        'key_decisions': AnalysisType.KEY_DECISIONS,
        'action_items': AnalysisType.ACTION_ITEMS,
        'open_questions': AnalysisType.OPEN_QUESTIONS,
        'summary': AnalysisType.SUMMARY,
        'topics': AnalysisType.TOPICS,
        'concepts': AnalysisType.CONCEPTS
    }
    
    analysis_enum = type_map.get(analysis_type)
    if not analysis_enum:
        raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    result = service.analyze(
        vector_store=vector_store,
        analysis_type=analysis_enum,
        top_k=top_k
    )
    
    return result.get('result', '')
