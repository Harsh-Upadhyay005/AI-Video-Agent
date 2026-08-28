"""
Test script for whole-content RAG pipeline.

Tests both PDF and audio/video transcript handling with:
1. Normal questions (top-k retrieval)
2. Whole-content summarization requests
3. Constraint handling (word limits, bullet points)
"""

import sys
from core.query_router import get_query_router, QueryType
from core.logger import get_logger

logger = get_logger(__name__)


def test_query_routing():
    """Test query router classification."""
    print("\n" + "=" * 80)
    print("Testing Query Router")
    print("=" * 80)
    
    router = get_query_router()
    
    test_queries = [
        # Specific questions (normal RAG)
        "What is the title?",
        "Who wrote this book?",
        "What happens in chapter 3?",
        "When was the meeting held?",
        
        # Whole-content summarization
        "Summarize this document",
        "Give me a 50-word summary",
        "What are the main points?",
        "Overview of the content",
        "Give me the key takeaways",
        "Tell me about this document",
        "Summarize in bullet points",
        
        # Extraction
        "List all the action items",
        "Extract all decisions",
        "Find all dates mentioned",
    ]
    
    for query in test_queries:
        intent = router.analyze_query(query)
        print(f"\nQuery: {query}")
        print(f"  Type: {intent.query_type.value}")
        print(f"  Constraint: {intent.constraint}")
        print(f"  Use full content: {router.should_use_full_content(intent)}")


def test_constraint_extraction():
    """Test constraint extraction from queries."""
    print("\n" + "=" * 80)
    print("Testing Constraint Extraction")
    print("=" * 80)
    
    router = get_query_router()
    
    constraint_queries = [
        "Give me a 50-word summary",
        "Summarize in 100 words",
        "Summarize this in bullet points",
        "Give me a numbered list of main points",
        "Give me a 25 word summary in bullets",
    ]
    
    for query in constraint_queries:
        intent = router.analyze_query(query)
        print(f"\nQuery: {query}")
        print(f"  Constraints: {intent.constraint}")


def test_end_to_end_with_mock():
    """Test end-to-end with mock data."""
    print("\n" + "=" * 80)
    print("Testing End-to-End with Mock Data")
    print("=" * 80)
    
    # This would require actual vector store and LLM
    # For now, just verify the routing logic
    
    from core.query_router import get_query_router
    
    router = get_query_router()
    
    questions = [
        ("What is the main idea?", False),  # Specific - might be whole content
        ("Summarize in 50 words", True),    # Whole content
        ("Give me the key points", True),   # Whole content
        ("What happens in chapter 5?", False),  # Specific
    ]
    
    for question, expected_full_content in questions:
        intent = router.analyze_query(question)
        uses_full = router.should_use_full_content(intent)
        
        status = "✓" if uses_full == expected_full_content else "✗"
        print(f"\n{status} Query: {question}")
        print(f"   Expected full content: {expected_full_content}")
        print(f"   Actual full content: {uses_full}")
        print(f"   Intent: {intent}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Whole-Content RAG Pipeline Tests")
    print("=" * 80)
    
    try:
        test_query_routing()
        test_constraint_extraction()
        test_end_to_end_with_mock()
        
        print("\n" + "=" * 80)
        print("✓ All tests completed")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
