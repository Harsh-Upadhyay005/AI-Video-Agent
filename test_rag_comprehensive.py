"""
Comprehensive RAG System Test Suite.
Tests all fixed functionality end-to-end.
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Sample transcript with known structure
TRANSCRIPT = """
Today we'll discuss artificial intelligence fundamentals. This guide covers three main areas.

First, Machine Learning is the foundation of modern AI. It involves training algorithms on data to recognize patterns and make predictions. Common techniques include supervised learning, unsupervised learning, and reinforcement learning.

Second, Deep Learning uses neural networks with multiple layers. These networks can automatically learn hierarchical features from data. Deep learning has revolutionized computer vision, natural language processing, and speech recognition.

Third, Neural Networks are computing systems inspired by biological brains. They consist of interconnected nodes that process information. Each connection has a weight that adjusts during training to improve performance.

These three concepts - Machine Learning, Deep Learning, and Neural Networks - work together to power modern AI applications.
"""

EXPECTED_CONCEPTS = ["Machine Learning", "Deep Learning", "Neural Networks"]


def test_scenario(name: str, test_func):
    """Run a test scenario and report results."""
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    
    try:
        result = test_func()
        if result:
            print(f"✓ PASSED: {name}")
            return True
        else:
            print(f"✗ FAILED: {name}")
            return False
    except Exception as e:
        print(f"✗ ERROR in {name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_1_topic_extraction():
    """Test: Topic extraction with precomputed metadata."""
    from core.rag_engine import build_rag_chain, ask_question
    from core.global_analyzer import analyze_video_global
    from core.global_metadata import save_video_metadata
    
    video_id = "test_comprehensive_001"
    
    # Generate and save metadata
    metadata = analyze_video_global(
        video_id=video_id,
        source="test",
        source_type="test",
        transcript=TRANSCRIPT,
        title="AI Fundamentals"
    )
    save_video_metadata(metadata)
    
    # Build RAG chain
    rag_chain = build_rag_chain(
        transcript=TRANSCRIPT,
        video_id=video_id,
        metadata={"video_id": video_id}
    )
    
    # Ask topic extraction question
    question = "What are the 3 main concepts discussed?"
    print(f"Question: {question}")
    
    answer = ask_question(rag_chain, question, debug=False)
    print(f"Answer: {answer}")
    
    # Validation: Check if all expected concepts are mentioned
    answer_lower = answer.lower()
    found = sum(1 for c in EXPECTED_CONCEPTS if c.lower() in answer_lower)
    
    print(f"\nConcepts found: {found}/{len(EXPECTED_CONCEPTS)}")
    for concept in EXPECTED_CONCEPTS:
        if concept.lower() in answer_lower:
            print(f"  ✓ {concept}")
        else:
            print(f"  ✗ {concept} (MISSING)")
    
    # Also check for hallucinations (concepts not in transcript)
    hallucination_terms = ["quantum", "blockchain", "cloud computing", "big data"]
    hallucinations = [term for term in hallucination_terms if term.lower() in answer_lower]
    
    if hallucinations:
        print(f"\n⚠ HALLUCINATIONS DETECTED: {hallucinations}")
        return False
    
    return found == len(EXPECTED_CONCEPTS)


def test_2_local_qa():
    """Test: Local QA with specific questions."""
    from core.rag_engine import build_rag_chain, ask_question
    
    video_id = "test_comprehensive_002"
    
    rag_chain = build_rag_chain(
        transcript=TRANSCRIPT,
        video_id=video_id,
        metadata={"video_id": video_id}
    )
    
    question = "What is deep learning?"
    print(f"Question: {question}")
    
    answer = ask_question(rag_chain, question, debug=False)
    print(f"Answer: {answer}")
    
    # Validation: Should mention neural networks and layers
    answer_lower = answer.lower()
    keywords = ["neural", "layer"]
    
    found = sum(1 for kw in keywords if kw in answer_lower)
    print(f"\nKeywords found: {found}/{len(keywords)}")
    
    return found >= 1  # At least one keyword


def test_3_global_summary():
    """Test: Global summary generation."""
    from core.rag_engine import build_rag_chain, ask_question
    from core.global_analyzer import analyze_video_global
    from core.global_metadata import save_video_metadata
    
    video_id = "test_comprehensive_003"
    
    # Generate metadata
    metadata = analyze_video_global(
        video_id=video_id,
        source="test",
        source_type="test",
        transcript=TRANSCRIPT,
        title="AI Fundamentals"
    )
    save_video_metadata(metadata)
    
    rag_chain = build_rag_chain(
        transcript=TRANSCRIPT,
        video_id=video_id,
        metadata={"video_id": video_id}
    )
    
    question = "Summarize this video"
    print(f"Question: {question}")
    
    answer = ask_question(rag_chain, question, debug=False)
    print(f"Answer: {answer}")
    
    # Validation: Should mention AI/artificial intelligence
    answer_lower = answer.lower()
    ai_mentioned = "ai" in answer_lower or "artificial intelligence" in answer_lower
    
    print(f"\nAI mentioned: {ai_mentioned}")
    
    return ai_mentioned


def test_4_followup_questions():
    """Test: Conversation memory and follow-up question handling."""
    from core.rag_engine import build_rag_chain, ask_question
    
    video_id = "test_comprehensive_004"
    
    rag_chain = build_rag_chain(
        transcript=TRANSCRIPT,
        video_id=video_id,
        metadata={"video_id": video_id}
    )
    
    # First question
    q1 = "What are the three concepts discussed?"
    print(f"Q1: {q1}")
    a1 = ask_question(rag_chain, q1, debug=False)
    print(f"A1: {a1[:150]}...")
    
    # Follow-up question
    q2 = "Explain the first one"
    print(f"\nQ2: {q2}")
    a2 = ask_question(rag_chain, q2, debug=True)  # Enable debug to see rewriting
    print(f"A2: {a2[:150]}...")
    
    # Validation: Second answer should mention machine learning
    ml_mentioned = "machine learning" in a2.lower()
    
    print(f"\nMachine Learning mentioned in follow-up: {ml_mentioned}")
    
    return ml_mentioned


def test_5_no_hallucination():
    """Test: Verify no hallucinations for non-existent topics."""
    from core.rag_engine import build_rag_chain, ask_question
    
    video_id = "test_comprehensive_005"
    
    rag_chain = build_rag_chain(
        transcript=TRANSCRIPT,
        video_id=video_id,
        metadata={"video_id": video_id}
    )
    
    # Ask about something NOT in the transcript
    question = "What does the video say about quantum computing?"
    print(f"Question: {question}")
    
    answer = ask_question(rag_chain, question, debug=False)
    print(f"Answer: {answer}")
    
    # Validation: Should indicate it's not in the transcript
    answer_lower = answer.lower()
    refuses = any(phrase in answer_lower for phrase in [
        "not found",
        "could not find",
        "not mentioned",
        "does not",
        "don't have"
    ])
    
    # Also check it didn't hallucinate quantum content
    no_quantum_details = not any(term in answer_lower for term in [
        "qubit",
        "superposition",
        "entanglement"
    ])
    
    print(f"\nRefuses to answer: {refuses}")
    print(f"No quantum hallucinations: {no_quantum_details}")
    
    return refuses and no_quantum_details


def test_6_cross_video_isolation():
    """Test: Verify videos don't contaminate each other."""
    from core.rag_engine import build_rag_chain, ask_question
    
    # Video 1: About AI
    video_id_1 = "test_isolation_video1"
    rag_chain_1 = build_rag_chain(
        transcript=TRANSCRIPT,
        video_id=video_id_1,
        metadata={"video_id": video_id_1}
    )
    
    # Video 2: About cooking
    cooking_transcript = """
    Today we'll learn to make pasta. First, boil water. Second, add pasta. Third, drain and serve.
    """
    video_id_2 = "test_isolation_video2"
    rag_chain_2 = build_rag_chain(
        transcript=cooking_transcript,
        video_id=video_id_2,
        metadata={"video_id": video_id_2}
    )
    
    # Ask video 2 about its content
    question = "What are the main steps?"
    print(f"Asking Video 2: {question}")
    answer = ask_question(rag_chain_2, question, debug=False)
    print(f"Answer: {answer}")
    
    # Validation: Should mention cooking, NOT AI
    has_cooking = "pasta" in answer.lower() or "boil" in answer.lower()
    has_ai = "machine learning" in answer.lower() or "neural" in answer.lower()
    
    print(f"\nContains cooking content: {has_cooking}")
    print(f"Contains AI content (contamination): {has_ai}")
    
    return has_cooking and not has_ai


def test_7_chunking_quality():
    """Test: Verify improved chunking doesn't fragment concepts."""
    from core.vector_store import build_vector_store
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    # Build vector store
    vector_store = build_vector_store(TRANSCRIPT, metadata={"test": "chunking"})
    
    # Retrieve all chunks
    all_docs = vector_store.similarity_search("", k=100)
    
    print(f"Total chunks created: {len(all_docs)}")
    
    # Check if concepts appear in chunks
    concept_coverage = {}
    for concept in EXPECTED_CONCEPTS:
        found_in = []
        for i, doc in enumerate(all_docs):
            if concept.lower() in doc.page_content.lower():
                found_in.append(i)
        concept_coverage[concept] = found_in
        print(f"{concept}: found in chunk(s) {found_in}")
    
    # Validation: Each concept should appear in at least one chunk
    all_found = all(len(chunks) > 0 for chunks in concept_coverage.values())
    
    # Check for excessive fragmentation (concept in >3 chunks = problem)
    not_fragmented = all(len(chunks) <= 3 for chunks in concept_coverage.values())
    
    print(f"\nAll concepts found: {all_found}")
    print(f"No excessive fragmentation: {not_fragmented}")
    
    return all_found and not_fragmented


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*80)
    print("COMPREHENSIVE RAG SYSTEM TEST SUITE")
    print("="*80)
    print("\nThis suite validates:")
    print("1. Topic extraction with metadata")
    print("2. Local QA accuracy")
    print("3. Global summary generation")
    print("4. Follow-up question handling")
    print("5. Hallucination prevention")
    print("6. Cross-video isolation")
    print("7. Chunking quality")
    print("\n" + "="*80)
    
    tests = [
        ("Topic Extraction with Metadata", test_1_topic_extraction),
        ("Local QA", test_2_local_qa),
        ("Global Summary", test_3_global_summary),
        ("Follow-up Questions", test_4_followup_questions),
        ("Hallucination Prevention", test_5_no_hallucination),
        ("Cross-Video Isolation", test_6_cross_video_isolation),
        ("Chunking Quality", test_7_chunking_quality),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_scenario(name, test_func)
        results.append((name, result))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed ({100*passed//total}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! RAG system is working correctly.")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Review failures above.")
    
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
