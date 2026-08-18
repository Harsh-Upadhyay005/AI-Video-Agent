"""
Query Intent Classification and Routing for RAG System.
Routes questions to appropriate retrieval strategies.
"""

import os
import re
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass

try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
except ImportError:
    ChatMistralAI = None
    ChatPromptTemplate = None
    StrOutputParser = None


class QueryIntent(Enum):
    """Types of user queries."""
    LOCAL_QA = "local_qa"  # Specific factual question about a topic
    GLOBAL_SUMMARY = "global_summary"  # Summarize entire video
    TOPIC_EXTRACTION = "topic_extraction"  # List main topics/concepts
    TIMELINE = "timeline"  # When was X discussed?
    UNKNOWN = "unknown"


@dataclass
class ClassifiedQuery:
    """Result of query classification."""
    intent: QueryIntent
    original_query: str
    confidence: str  # high, medium, low
    reasoning: Optional[str] = None


class QueryClassifier:
    """
    Classifies user queries into intent categories.
    Uses rule-based classification first, falls back to LLM if needed.
    """
    
    # Keywords for rule-based classification
    GLOBAL_KEYWORDS = [
        r'\b(all|entire|complete|whole|overall)\b.*\b(video|content|discussion|transcript|meeting)\b',
        r'\b(summarize|summary)\b',  # Simplified to catch all summarize requests
        r'\bwhat\s+(is|was|are|were)\s+(this|the)\s+(video|meeting|discussion)\s+about\b',
        r'\bmain\s+(point|points|idea|ideas|takeaway|takeaways)\b',
        r'\bkey\s+(takeaway|takeaways|point|points)\b',
        r'\b(give me|provide)\s+(a\s+)?(summary|overview)\b'
    ]
    
    TOPIC_EXTRACTION_KEYWORDS = [
        r'\b(list|what|identify|name|enumerate)\b.*\b(\d+\s+)?(main|key|major|important|primary)\s+(topic|topics|concept|concepts|theme|themes|subject|subjects|idea|ideas)\b',
        r'\b(\d+\s+)?(key|main|major|important)\s+(concept|concepts|topic|topics)\b.*\b(discuss|discussed|cover|covered|mention|mentioned)\b',
        r'\bhow\s+many\b.*\b(topic|topics|concept|concepts|theme|themes)\b',
        r'\bwhat\s+(are|were)\s+the\b.*\b(topic|topics|concept|concepts|idea|ideas)\b'
    ]
    
    TIMELINE_KEYWORDS = [
        r'\b(when|at what (time|timestamp|point))\b.*\b(discuss|discussed|mention|mentioned|talk|talked|explain|explained|introduce|introduced)\b',
        r'\b(timestamp|time|minute|second)\b.*\b(for|of|when)\b',
        r'\bat\s+what\s+(point|timestamp|time)\b',
        r'\bwhat\s+(time|timestamp)\b.*\b(did|were|was)\b'
    ]
    
    def __init__(self):
        """Initialize classifier."""
        self.llm = None
        if ChatMistralAI is not None:
            try:
                self.llm = ChatMistralAI(
                    model="mistral-small-latest",
                    mistral_api_key=os.getenv("MISTRAL_API_KEY"),
                    temperature=0.0
                )
            except Exception as e:
                print(f"[QueryClassifier] Warning: Could not initialize LLM: {e}")
    
    def classify(self, query: str) -> ClassifiedQuery:
        """
        Classify user query into intent category.
        
        Args:
            query: User's question
            
        Returns:
            ClassifiedQuery with intent and confidence
        """
        query_lower = query.lower().strip()
        
        # Rule-based classification (fast and reliable)
        
        # Check for TIMELINE questions
        for pattern in self.TIMELINE_KEYWORDS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return ClassifiedQuery(
                    intent=QueryIntent.TIMELINE,
                    original_query=query,
                    confidence="high",
                    reasoning="Contains timestamp/time-based keywords"
                )
        
        # Check for TOPIC_EXTRACTION questions
        for pattern in self.TOPIC_EXTRACTION_KEYWORDS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return ClassifiedQuery(
                    intent=QueryIntent.TOPIC_EXTRACTION,
                    original_query=query,
                    confidence="high",
                    reasoning="Requests list of topics/concepts"
                )
        
        # Check for GLOBAL_SUMMARY questions
        for pattern in self.GLOBAL_KEYWORDS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return ClassifiedQuery(
                    intent=QueryIntent.GLOBAL_SUMMARY,
                    original_query=query,
                    confidence="high",
                    reasoning="Asks about entire video/overall content"
                )
        
        # Check for specific question patterns (LOCAL_QA)
        local_patterns = [
            r'\bwhat\s+is\b',
            r'\bexplain\b',
            r'\bdescribe\b',
            r'\bhow\s+does\b',
            r'\bwhy\s+(is|does|did)\b',
            r'\bdefine\b',
            r'\btell\s+me\s+about\b'
        ]
        
        for pattern in local_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                # Make sure it's not also a global question
                if not any(re.search(p, query_lower, re.IGNORECASE) for p in self.GLOBAL_KEYWORDS):
                    return ClassifiedQuery(
                        intent=QueryIntent.LOCAL_QA,
                        original_query=query,
                        confidence="high",
                        reasoning="Specific factual question pattern"
                    )
        
        # Default to LOCAL_QA for most questions
        # (Better to over-retrieve than under-retrieve)
        return ClassifiedQuery(
            intent=QueryIntent.LOCAL_QA,
            original_query=query,
            confidence="medium",
            reasoning="Default classification - no strong global/timeline signals"
        )
    
    def classify_with_llm(self, query: str) -> ClassifiedQuery:
        """
        Use LLM for classification (backup method).
        
        Args:
            query: User's question
            
        Returns:
            ClassifiedQuery with intent
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            # Fallback to rule-based
            return self.classify(query)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a query intent classifier. Classify the user's question into one of these categories:

LOCAL_QA: Specific question about a particular topic, concept, or fact
GLOBAL_SUMMARY: Request to summarize the entire video/content
TOPIC_EXTRACTION: Request to list main topics, concepts, or themes
TIMELINE: Question about when something was discussed (timestamps)

Respond with ONLY the category name (e.g., "LOCAL_QA")."""),
            ("human", "{query}")
        ])
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"query": query}).strip().upper()
            
            # Map to enum
            intent_map = {
                "LOCAL_QA": QueryIntent.LOCAL_QA,
                "GLOBAL_SUMMARY": QueryIntent.GLOBAL_SUMMARY,
                "TOPIC_EXTRACTION": QueryIntent.TOPIC_EXTRACTION,
                "TIMELINE": QueryIntent.TIMELINE
            }
            
            intent = intent_map.get(result, QueryIntent.LOCAL_QA)
            
            return ClassifiedQuery(
                intent=intent,
                original_query=query,
                confidence="high",
                reasoning="LLM classification"
            )
        except Exception as e:
            print(f"[QueryClassifier] LLM classification failed: {e}")
            # Fallback to rule-based
            return self.classify(query)


# Global instance
_classifier = None

def get_query_classifier() -> QueryClassifier:
    """Get singleton query classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier


def classify_query(query: str) -> ClassifiedQuery:
    """
    Convenience function to classify a query.
    
    Args:
        query: User's question
        
    Returns:
        ClassifiedQuery with intent and confidence
    """
    classifier = get_query_classifier()
    return classifier.classify(query)
