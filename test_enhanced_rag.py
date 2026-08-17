"""
Test script for Enhanced RAG with Query Routing.
Tests both local and global questions.
"""

from core.query_router import classify_query, QueryIntent


def test_query_classification():
    """Test query intent classification."""
    print("=" * 80)
    print("TESTING QUERY INTENT CLASSIFICATION")
    print("=" * 80)
    
    test_queries = [
        # LOCAL_QA
        ("What is RAG?", QueryIntent.LOCAL_QA),
        ("Explain embeddings", QueryIntent.LOCAL_QA),
        ("What did the speaker say about transformers?", QueryIntent.LOCAL_QA),
        ("How does attention mechanism work?", QueryIntent.LOCAL_QA),
        
        # GLOBAL_SUMMARY
        ("Summarize the entire video", QueryIntent.GLOBAL_SUMMARY),
        ("What is this video about?", QueryIntent.GLOBAL_SUMMARY),
        ("Give me an overview of the complete discussion", QueryIntent.GLOBAL_SUMMARY),
        ("What are the main takeaways from the whole video?", QueryIntent.GLOBAL_SUMMARY),
        
        # TOPIC_EXTRACTION
        ("What are the 7 key concepts discussed?", QueryIntent.TOPIC_EXTRACTION),
        ("List all the main topics covered", QueryIntent.TOPIC_EXTRACTION),
        ("What are the major concepts in this video?", QueryIntent.TOPIC_EXTRACTION),
        ("How many topics were discussed?", QueryIntent.TOPIC_EXTRACTION),
        ("Identify the key themes mentioned", QueryIntent.TOPIC_EXTRACTION),
        
        # TIMELINE
        ("When did the speaker discuss RAG?", QueryIntent.TIMELINE),
        ("At what timestamp were embeddings explained?", QueryIntent.TIMELINE),
        ("What time did they talk about transformers?", QueryIntent.TIMELINE),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_intent in test_queries:
        result = classify_query(query)
        status = "✓" if result.intent == expected_intent else "✗"
        
        if result.intent == expected_intent:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} Query: {query}")
        print(f"  Expected: {expected_intent.value}")
        print(f"  Got: {result.intent.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Reasoning: {result.reasoning}")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_queries)} tests")
    print("=" * 80)
    
    return passed, failed


def test_rag_routing():
    """Test RAG routing with sample transcript."""
    print("\n" + "=" * 80)
    print("TESTING RAG ROUTING (requires backend running)")
    print("=" * 80)
    
    # This would require a running backend with a processed video
    print("\nTo test RAG routing:")
    print("1. Start the backend: python -m uvicorn api.main:app --reload")
    print("2. Upload a video through the UI")
    print("3. Try these questions in the chat:")
    print("\n   LOCAL QUESTIONS:")
    print("   - What is RAG?")
    print("   - Explain embeddings")
    print("\n   GLOBAL QUESTIONS:")
    print("   - What are the 7 key concepts discussed?")
    print("   - Summarize the entire video")
    print("   - List all main topics covered")
    print("\n   The system should route them to different strategies!")


if __name__ == "__main__":
    # Test classification
    passed, failed = test_query_classification()
    
    # Show routing test instructions
    test_rag_routing()
    
    print("\n" + "=" * 80)
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"⚠ {failed} TESTS FAILED")
    print("=" * 80)
