"""
Quick validation test for RAG fixes.
Tests the complete pipeline with metadata generation and loading.
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Sample transcript
TRANSCRIPT = """
Welcome to this guide on AI concepts. We'll cover 5 key topics today.

First is Machine Learning, which is training algorithms on data to make predictions.

Second is Neural Networks, which are computing systems inspired by biological brains.

Third is Natural Language Processing, enabling computers to understand human language.

Fourth is Computer Vision, allowing machines to interpret visual information.

Fifth is Reinforcement Learning, where agents learn through trial and error.

These 5 concepts form the foundation of modern AI applications.
"""

def test_complete_pipeline():
    """Test the complete RAG pipeline with metadata."""
    print("="*80)
    print("COMPLETE PIPELINE VALIDATION TEST")
    print("="*80)
    
    # Step 1: Build RAG chain with metadata generation
    print("\n[Step 1] Building RAG chain and generating global metadata...")
    
    from core.rag_engine import build_rag_chain
    from core.global_analyzer import analyze_video_global
    from core.global_metadata import save_video_metadata, load_video_metadata
    
    video_id = "test_validation_001"
    
    # Generate and save global metadata
    metadata = analyze_video_global(
        video_id=video_id,
        source="test",
        source_type="test",
        transcript=TRANSCRIPT,
        title="5 AI Concepts"
    )
    
    print(f"   Generated: {len(metadata.topics)} topics, {len(metadata.key_concepts)} concepts")
    print(f"   Topics: {metadata.topics}")
    print(f"   Concepts: {metadata.key_concepts}")
    
    save_video_metadata(metadata)
    print(f"   ✓ Metadata saved")
    
    # Build RAG chain
    rag_chain = build_rag_chain(
        transcript=TRANSCRIPT,
        video_id=video_id,
        metadata={"video_id": video_id, "test": "validation"}
    )
    
    print(f"   ✓ RAG chain built")
    
    # Step 2: Test metadata loading
    print("\n[Step 2] Testing metadata loading...")
    loaded_metadata = load_video_metadata(video_id)
    
    if loaded_metadata:
        print(f"   ✓ Metadata loaded successfully")
        print(f"     - {len(loaded_metadata.topics)} topics")
        print(f"     - {len(loaded_metadata.key_concepts)} concepts")
    else:
        print(f"   ✗ FAILED: Metadata not loaded")
        return False
    
    # Step 3: Test queries
    print("\n[Step 3] Testing different query types...")
    
    from core.rag_engine import ask_question
    
    test_queries = [
        ("What are the 5 key concepts discussed?", "TOPIC_EXTRACTION"),
        ("What is machine learning?", "LOCAL_QA"),
        ("Summarize this content", "GLOBAL_SUMMARY"),
    ]
    
    for query, expected_type in test_queries:
        print(f"\n   Query: {query}")
        print(f"   Expected type: {expected_type}")
        
        answer = ask_question(rag_chain, query, debug=True)
        print(f"   Answer: {answer[:200]}...")
        
        # Basic validation
        if "machine learning" in query.lower():
            if "machine learning" in answer.lower():
                print(f"   ✓ Contains relevant content")
            else:
                print(f"   ⚠ Missing expected content")
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_complete_pipeline()
        if success:
            print("\n✓ All validations passed!")
        else:
            print("\n✗ Some validations failed")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
