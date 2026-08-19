"""
RAG Diagnosis Tool - Trace complete pipeline and identify failure points.

This script helps diagnose:
1. Where information is lost in the RAG pipeline
2. Whether retrieval or generation is the problem
3. Whether the transcript contains the answer
4. If the LLM can answer with full context
"""

import os
import sys
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Test transcript with known concepts
SAMPLE_TRANSCRIPT = """
Welcome to this comprehensive guide on Generative AI concepts. Today, we'll discuss seven key concepts that every AI practitioner should understand.

First, let's talk about Large Language Models or LLMs. These are neural networks trained on vast amounts of text data that can understand and generate human-like text. Models like GPT-4, Claude, and Gemini are examples of LLMs that power many AI applications today.

Second, we have RAG, which stands for Retrieval Augmented Generation. RAG is a technique that combines information retrieval with text generation. Instead of relying solely on the model's training data, RAG systems retrieve relevant documents from a knowledge base and use them to generate more accurate, grounded responses. This is particularly useful for reducing hallucinations.

Third, let's discuss Embeddings. Embeddings are numerical representations of text that capture semantic meaning. They allow us to convert words, sentences, or documents into vectors in a high-dimensional space where similar concepts are positioned close together. This is fundamental for semantic search and retrieval.

Fourth, we have Vector Databases. These specialized databases store and index embeddings, enabling fast similarity search. Popular vector databases include ChromaDB, Pinecone, Weaviate, and Milvus. They're essential for RAG systems as they allow quick retrieval of relevant information.

Fifth, let's examine Prompt Engineering. This is the art and science of crafting effective prompts to guide LLMs toward desired outputs. Good prompt engineering includes clear instructions, relevant context, and examples when needed. It's crucial for getting consistent, high-quality results from AI models.

Sixth, we have Fine-tuning. This is the process of adapting a pre-trained model to a specific task or domain by training it on specialized data. Fine-tuning allows you to customize model behavior without training from scratch, making it more efficient than building models from the ground up.

Finally, the seventh concept is Agents. AI agents are autonomous systems that can perceive their environment, make decisions, and take actions to achieve goals. They often combine LLMs with tools, memory, and planning capabilities. Agents can break down complex tasks, use external tools, and maintain context across multiple interactions.

These seven concepts - LLMs, RAG, Embeddings, Vector Databases, Prompt Engineering, Fine-tuning, and Agents - form the foundation of modern generative AI applications. Understanding how they work together is key to building effective AI systems.
"""

EXPECTED_CONCEPTS = [
    "Large Language Models (LLMs)",
    "RAG (Retrieval Augmented Generation)",
    "Embeddings",
    "Vector Databases",
    "Prompt Engineering",
    "Fine-tuning",
    "AI Agents"
]


def test_1_verify_transcript_contains_concepts():
    """Test 1: Verify the transcript actually contains the expected concepts."""
    print("\n" + "="*80)
    print("TEST 1: VERIFY TRANSCRIPT CONTAINS EXPECTED CONCEPTS")
    print("="*80)
    
    found_concepts = []
    missing_concepts = []
    
    transcript_lower = SAMPLE_TRANSCRIPT.lower()
    
    for concept in EXPECTED_CONCEPTS:
        # Extract key term from concept
        key_term = concept.split("(")[0].strip().lower()
        
        if key_term in transcript_lower or concept.lower() in transcript_lower:
            found_concepts.append(concept)
            print(f"✓ Found: {concept}")
        else:
            missing_concepts.append(concept)
            print(f"✗ Missing: {concept}")
    
    print(f"\nResult: {len(found_concepts)}/{len(EXPECTED_CONCEPTS)} concepts found in transcript")
    
    if len(found_concepts) == len(EXPECTED_CONCEPTS):
        print("✓ TEST PASSED: All expected concepts are in the transcript")
        return True
    else:
        print("✗ TEST FAILED: Some concepts are missing")
        return False


def test_2_check_chunking():
    """Test 2: Check how transcript is chunked and if concepts are fragmented."""
    print("\n" + "="*80)
    print("TEST 2: ANALYZE CHUNKING BEHAVIOR")
    print("="*80)
    
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        # Current settings from vector_store.py
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        chunks = splitter.split_text(SAMPLE_TRANSCRIPT)
        
        print(f"Transcript length: {len(SAMPLE_TRANSCRIPT)} characters")
        print(f"Number of chunks: {len(chunks)}")
        print(f"Chunk size setting: 500 chars, overlap: 50 chars")
        print()
        
        # Check if each concept appears in at least one chunk
        concept_coverage = {}
        
        for concept in EXPECTED_CONCEPTS:
            key_term = concept.split("(")[0].strip().lower()
            found_in_chunks = []
            
            for i, chunk in enumerate(chunks):
                if key_term in chunk.lower():
                    found_in_chunks.append(i)
            
            concept_coverage[concept] = found_in_chunks
            
            if found_in_chunks:
                print(f"✓ '{concept}' found in chunk(s): {found_in_chunks}")
            else:
                print(f"✗ '{concept}' NOT found in any chunk")
        
        # Show sample chunks
        print(f"\nSample chunks:")
        for i in range(min(3, len(chunks))):
            print(f"\n--- Chunk {i} ({len(chunks[i])} chars) ---")
            print(chunks[i][:200] + "...")
        
        # Analysis
        fragmented = sum(1 for v in concept_coverage.values() if len(v) > 1)
        missing = sum(1 for v in concept_coverage.values() if len(v) == 0)
        
        print(f"\n📊 Chunking Analysis:")
        print(f"  - Concepts in single chunk: {len(EXPECTED_CONCEPTS) - fragmented - missing}")
        print(f"  - Concepts fragmented across chunks: {fragmented}")
        print(f"  - Concepts missing from chunks: {missing}")
        
        if missing > 0:
            print("✗ WARNING: Chunking lost some concepts!")
        elif fragmented > len(EXPECTED_CONCEPTS) // 2:
            print("⚠ WARNING: Many concepts are fragmented across chunks")
        else:
            print("✓ Chunking preserves concepts reasonably well")
        
        return chunks
        
    except ImportError:
        print("✗ Cannot test chunking - langchain not installed")
        return []


def test_3_check_retrieval(chunks: List[str]):
    """Test 3: Check if retrieval returns relevant chunks for global questions."""
    print("\n" + "="*80)
    print("TEST 3: TEST RETRIEVAL FOR GLOBAL QUESTION")
    print("="*80)
    
    try:
        from core.vector_store import build_vector_store, get_retriever
        
        # Build vector store
        print("Building vector store from sample transcript...")
        vector_store = build_vector_store(SAMPLE_TRANSCRIPT, metadata={"test": "diagnosis"})
        
        # Test query
        query = "What are the 7 key concepts discussed in this video?"
        print(f"\nQuery: {query}")
        
        # Test different k values
        for k in [4, 8, 12, 20]:
            print(f"\n--- Testing with k={k} ---")
            retriever = get_retriever(vector_store, k=k)
            docs = retriever.invoke(query)
            
            print(f"Retrieved {len(docs)} chunks")
            
            # Check which concepts are covered
            covered_concepts = []
            retrieved_text = " ".join([doc.page_content for doc in docs])
            
            for concept in EXPECTED_CONCEPTS:
                key_term = concept.split("(")[0].strip().lower()
                if key_term in retrieved_text.lower():
                    covered_concepts.append(concept)
            
            print(f"Concepts covered: {len(covered_concepts)}/{len(EXPECTED_CONCEPTS)}")
            
            for concept in EXPECTED_CONCEPTS:
                key_term = concept.split("(")[0].strip().lower()
                if key_term in retrieved_text.lower():
                    print(f"  ✓ {concept}")
                else:
                    print(f"  ✗ {concept} (MISSING)")
        
        print("\n📊 Retrieval Analysis:")
        if len(covered_concepts) < len(EXPECTED_CONCEPTS):
            print(f"✗ CRITICAL ISSUE: Retrieval missing {len(EXPECTED_CONCEPTS) - len(covered_concepts)} concepts")
            print("  This means the LLM will NOT have access to all information!")
        else:
            print("✓ Retrieval returns all necessary concepts")
        
        return vector_store
        
    except Exception as e:
        print(f"✗ Retrieval test failed: {e}")
        return None


def test_4_test_llm_with_full_context():
    """Test 4: Test if LLM can answer correctly with FULL transcript."""
    print("\n" + "="*80)
    print("TEST 4: TEST LLM WITH FULL TRANSCRIPT (NO RAG)")
    print("="*80)
    
    try:
        from langchain_mistralai import ChatMistralAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        llm = ChatMistralAI(
            model="mistral-small-latest",
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.3
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are analyzing a video transcript. Answer the question based ONLY on the transcript provided.

Rules:
- Use ONLY information from the transcript
- Do not use outside knowledge
- Do not invent concepts not in the transcript
- If the transcript mentions fewer than requested, say so

Transcript:
{transcript}"""),
            ("human", "{question}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        
        question = "What are the 7 key concepts discussed in this video?"
        print(f"Question: {question}\n")
        
        answer = chain.invoke({
            "transcript": SAMPLE_TRANSCRIPT,
            "question": question
        })
        
        print("LLM Answer:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        
        # Check if answer mentions all concepts
        answer_lower = answer.lower()
        found_in_answer = []
        
        for concept in EXPECTED_CONCEPTS:
            key_term = concept.split("(")[0].strip().lower()
            if key_term in answer_lower:
                found_in_answer.append(concept)
        
        print(f"\n📊 LLM Response Analysis:")
        print(f"Concepts mentioned in answer: {len(found_in_answer)}/{len(EXPECTED_CONCEPTS)}")
        
        for concept in EXPECTED_CONCEPTS:
            key_term = concept.split("(")[0].strip().lower()
            if key_term in answer_lower:
                print(f"  ✓ {concept}")
            else:
                print(f"  ✗ {concept} (MISSING FROM ANSWER)")
        
        if len(found_in_answer) == len(EXPECTED_CONCEPTS):
            print("\n✓ SUCCESS: LLM can correctly answer when given full transcript")
            print("  → This means the problem is with RETRIEVAL or ROUTING, not the LLM")
        else:
            print("\n✗ FAILURE: LLM fails even with full transcript")
            print("  → This indicates a GENERATION or PROMPT problem")
        
        return answer
        
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_5_test_rag_system():
    """Test 5: Test the actual RAG system with the sample transcript."""
    print("\n" + "="*80)
    print("TEST 5: TEST ACTUAL RAG SYSTEM")
    print("="*80)
    
    try:
        from core.rag_engine import build_rag_chain, ask_question
        
        # Build RAG chain
        print("Building RAG chain...")
        rag_chain = build_rag_chain(
            transcript=SAMPLE_TRANSCRIPT,
            video_id="test_diagnosis",
            metadata={"test": "diagnosis"}
        )
        
        question = "What are the 7 key concepts discussed in this video?"
        print(f"\nQuestion: {question}")
        
        # Test with debug mode
        print("\n--- RAG Response (with debug) ---")
        answer = ask_question(rag_chain, question, debug=True)
        
        print("\nRAG Answer:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        
        # Analyze answer
        answer_lower = answer.lower()
        found_in_answer = []
        
        for concept in EXPECTED_CONCEPTS:
            key_term = concept.split("(")[0].strip().lower()
            if key_term in answer_lower:
                found_in_answer.append(concept)
        
        print(f"\n📊 RAG System Analysis:")
        print(f"Concepts in RAG answer: {len(found_in_answer)}/{len(EXPECTED_CONCEPTS)}")
        
        for concept in EXPECTED_CONCEPTS:
            key_term = concept.split("(")[0].strip().lower()
            if key_term in answer_lower:
                print(f"  ✓ {concept}")
            else:
                print(f"  ✗ {concept} (MISSING)")
        
        if len(found_in_answer) == len(EXPECTED_CONCEPTS):
            print("\n✓ RAG system works correctly!")
        else:
            print(f"\n✗ RAG system failed - missing {len(EXPECTED_CONCEPTS) - len(found_in_answer)} concepts")
        
        return answer
        
    except Exception as e:
        print(f"✗ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_6_test_query_routing():
    """Test 6: Verify query routing classifies questions correctly."""
    print("\n" + "="*80)
    print("TEST 6: TEST QUERY ROUTING")
    print("="*80)
    
    try:
        from core.query_router import classify_query, QueryIntent
        
        test_queries = [
            ("What are the 7 key concepts discussed?", QueryIntent.TOPIC_EXTRACTION),
            ("What is RAG?", QueryIntent.LOCAL_QA),
            ("Summarize this video", QueryIntent.GLOBAL_SUMMARY),
            ("What are the main topics?", QueryIntent.TOPIC_EXTRACTION),
            ("When was embeddings discussed?", QueryIntent.TIMELINE),
            ("Explain fine-tuning", QueryIntent.LOCAL_QA),
        ]
        
        print("Testing query classification:\n")
        
        correct = 0
        for query, expected_intent in test_queries:
            result = classify_query(query)
            match = "✓" if result.intent == expected_intent else "✗"
            
            if result.intent == expected_intent:
                correct += 1
            
            print(f"{match} Query: {query}")
            print(f"   Expected: {expected_intent.value}")
            print(f"   Got: {result.intent.value} (confidence: {result.confidence})")
            print(f"   Reasoning: {result.reasoning}")
            print()
        
        print(f"📊 Routing Accuracy: {correct}/{len(test_queries)} correct")
        
        if correct == len(test_queries):
            print("✓ Query routing works correctly")
        else:
            print("⚠ Some queries routed incorrectly")
        
    except Exception as e:
        print(f"✗ Query routing test failed: {e}")


def test_7_check_global_metadata():
    """Test 7: Check if global metadata is generated and loaded correctly."""
    print("\n" + "="*80)
    print("TEST 7: TEST GLOBAL METADATA SYSTEM")
    print("="*80)
    
    try:
        from core.global_analyzer import analyze_video_global
        from core.global_metadata import load_video_metadata
        
        # Generate global metadata
        print("Generating global metadata...")
        metadata = analyze_video_global(
            video_id="test_diagnosis",
            source="test",
            source_type="test",
            transcript=SAMPLE_TRANSCRIPT,
            title="Test Video - 7 GenAI Concepts"
        )
        
        print(f"\nGenerated Metadata:")
        print(f"  Topics: {len(metadata.topics)}")
        for i, topic in enumerate(metadata.topics, 1):
            print(f"    {i}. {topic}")
        
        print(f"\n  Key Concepts: {len(metadata.key_concepts)}")
        for i, concept in enumerate(metadata.key_concepts, 1):
            print(f"    {i}. {concept}")
        
        print(f"\n  Summary: {metadata.summary[:200]}...")
        
        # Check coverage
        metadata_text = " ".join(metadata.topics + metadata.key_concepts).lower()
        covered = []
        
        for concept in EXPECTED_CONCEPTS:
            key_term = concept.split("(")[0].strip().lower()
            if key_term in metadata_text:
                covered.append(concept)
        
        print(f"\n📊 Metadata Coverage: {len(covered)}/{len(EXPECTED_CONCEPTS)} concepts")
        
        for concept in EXPECTED_CONCEPTS:
            key_term = concept.split("(")[0].strip().lower()
            if key_term in metadata_text:
                print(f"  ✓ {concept}")
            else:
                print(f"  ✗ {concept} (MISSING)")
        
        if len(covered) >= len(EXPECTED_CONCEPTS) - 1:  # Allow 1 missing
            print("\n✓ Global metadata extraction works well")
        else:
            print(f"\n⚠ Global metadata missing {len(EXPECTED_CONCEPTS) - len(covered)} concepts")
        
        # Test loading
        print("\nTesting metadata loading...")
        loaded = load_video_metadata("test_diagnosis")
        
        if loaded:
            print("✓ Metadata can be loaded successfully")
        else:
            print("✗ Metadata loading failed")
        
    except Exception as e:
        print(f"✗ Global metadata test failed: {e}")
        import traceback
        traceback.print_exc()


def run_full_diagnosis():
    """Run complete diagnostic suite."""
    print("\n" + "="*80)
    print("RAG HALLUCINATION DIAGNOSIS - FULL TEST SUITE")
    print("="*80)
    print("\nThis diagnostic will:")
    print("1. Verify transcript contains expected concepts")
    print("2. Analyze chunking behavior")
    print("3. Test retrieval effectiveness")
    print("4. Test LLM with full context (baseline)")
    print("5. Test actual RAG system")
    print("6. Test query routing")
    print("7. Test global metadata system")
    print("\n" + "="*80)
    
    # Run tests
    test_1_verify_transcript_contains_concepts()
    chunks = test_2_check_chunking()
    vector_store = test_3_check_retrieval(chunks)
    test_4_test_llm_with_full_context()
    test_5_test_rag_system()
    test_6_test_query_routing()
    test_7_check_global_metadata()
    
    # Summary
    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)
    print("\nReview the results above to identify where the pipeline fails.")
    print("\nKey questions to answer:")
    print("1. Does chunking fragment concepts? (Test 2)")
    print("2. Does retrieval miss concepts? (Test 3)")
    print("3. Can LLM answer with full context? (Test 4)")
    print("4. Does RAG system answer correctly? (Test 5)")
    print("5. Is query routing working? (Test 6)")
    print("6. Is global metadata complete? (Test 7)")
    print("\nIf Test 4 succeeds but Test 5 fails → Problem is RETRIEVAL/ROUTING")
    print("If Test 4 also fails → Problem is GENERATION/PROMPTING")
    print("="*80)


if __name__ == "__main__":
    run_full_diagnosis()
