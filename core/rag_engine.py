"""
Enhanced RAG Engine with Query Intent Routing.
Handles both local (specific) and global (whole-video) questions.
"""

import os
from typing import List, Optional, Dict, Any

try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda
    from langchain_core.documents import Document
except Exception:
    ChatMistralAI = None
    ChatPromptTemplate = None
    StrOutputParser = None
    RunnablePassthrough = None
    RunnableLambda = None
    Document = None

from core.vector_store import build_vector_store, load_vector_store, get_retriever
from core.query_router import classify_query, QueryIntent
from core.global_metadata import load_video_metadata


def get_llm():
    if ChatMistralAI is None:
        return None
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])


def build_rag_chain(transcript: str, video_id: str = None, metadata: dict = None):
    """
    Build RAG chain with enhanced metadata support.
    
    Args:
        transcript: Full transcript text
        video_id: Optional video ID for global metadata lookup
        metadata: Optional metadata dict (source, timestamps, etc.)
    
    Returns:
        Enhanced RAG chain with routing capability
    """
    # Build vector store with metadata
    vector_store_metadata = metadata or {}
    if video_id:
        vector_store_metadata['video_id'] = video_id
    
    vector_store = build_vector_store(transcript, metadata=vector_store_metadata)
    
    # Create enhanced RAG chain that supports routing
    enhanced_chain = EnhancedRAGChain(
        vector_store=vector_store,
        video_id=video_id,
        full_transcript=transcript
    )
    
    return enhanced_chain


class EnhancedRAGChain:
    """
    Enhanced RAG chain with query intent routing.
    Routes questions to appropriate retrieval strategies.
    """
    
    def __init__(self, vector_store, video_id: str = None, full_transcript: str = ""):
        """
        Initialize enhanced RAG chain.
        
        Args:
            vector_store: Chroma vector store
            video_id: Optional video ID for metadata lookup
            full_transcript: Full transcript text for global queries
        """
        self.vector_store = vector_store
        self.video_id = video_id
        self.full_transcript = full_transcript
        self.llm = get_llm()
        
        # Load global metadata if available
        self.global_metadata = None
        if video_id:
            self.global_metadata = load_video_metadata(video_id)
    
    def invoke(self, question: str, debug: bool = False) -> str:
        """
        Process question with intent-based routing.
        
        Args:
            question: User's question
            debug: If True, print debug information
            
        Returns:
            Answer string
        """
        # Classify query intent
        classified = classify_query(question)
        
        if debug:
            print(f"\n[RAG Debug]")
            print(f"Question: {question}")
            print(f"Intent: {classified.intent.value}")
            print(f"Confidence: {classified.confidence}")
            print(f"Reasoning: {classified.reasoning}")
        
        # Route to appropriate strategy
        if classified.intent == QueryIntent.GLOBAL_SUMMARY:
            return self._handle_global_summary(question, debug)
        elif classified.intent == QueryIntent.TOPIC_EXTRACTION:
            return self._handle_topic_extraction(question, debug)
        elif classified.intent == QueryIntent.TIMELINE:
            return self._handle_timeline_query(question, debug)
        else:  # LOCAL_QA
            return self._handle_local_qa(question, debug)
    
    def _handle_local_qa(self, question: str, debug: bool = False) -> str:
        """
        Handle local/specific questions using vector retrieval.
        
        Args:
            question: User's question
            debug: Debug mode
            
        Returns:
            Answer
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return "RAG is unavailable because required dependencies are not installed."
        
        # Retrieve relevant chunks (increased k for better coverage)
        retriever = get_retriever(self.vector_store, k=8)
        docs = retriever.invoke(question)
        
        if debug:
            print(f"Retrieved {len(docs)} chunks")
            for i, doc in enumerate(docs[:3]):
                print(f"Chunk {i+1}: {doc.page_content[:100]}...")
        
        context = format_docs(docs)
        
        # Build prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}"""),
            ("human", "{question}"),
        ])
        
        chain = (
            {"context": RunnableLambda(lambda x: context), "question": RunnablePassthrough()}
            | prompt | self.llm | StrOutputParser()
        )
        
        return chain.invoke(question)
    
    def _handle_global_summary(self, question: str, debug: bool = False) -> str:
        """
        Handle global summary questions using stored metadata or full transcript.
        
        Args:
            question: User's question
            debug: Debug mode
            
        Returns:
            Answer
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return "Summary unavailable - LLM dependencies not installed."
        
        # Try to use precomputed metadata first
        if self.global_metadata:
            if debug:
                print("Using precomputed global metadata")
            
            summary = self.global_metadata.summary
            topics = self.global_metadata.topics
            concepts = self.global_metadata.key_concepts
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are answering a question about an entire video/audio recording.

Video Summary: {summary}

Main Topics Discussed:
{topics}

Key Concepts:
{concepts}

Answer the user's question based on this global information. Be comprehensive but concise."""),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({
                "summary": summary,
                "topics": "\n".join(f"• {t}" for t in topics),
                "concepts": "\n".join(f"• {c}" for c in concepts),
                "question": question
            })
        
        # Fallback: Use transcript (truncated if too long)
        if debug:
            print("Using full transcript for global summary")
        
        transcript_sample = self.full_transcript[:8000]  # Limit to avoid token limits
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are answering a question about an entire video/audio recording.

Below is the transcript (or beginning portion):

{transcript}

Provide a comprehensive answer to the user's question about the overall content."""),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"transcript": transcript_sample, "question": question})
    
    def _handle_topic_extraction(self, question: str, debug: bool = False) -> str:
        """
        Handle topic/concept extraction questions.
        
        Args:
            question: User's question
            debug: Debug mode
            
        Returns:
            Answer with list of topics/concepts
        """
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return "Topic extraction unavailable - LLM dependencies not installed."
        
        # Try to use precomputed metadata first
        if self.global_metadata and (self.global_metadata.topics or self.global_metadata.key_concepts):
            if debug:
                print("Using precomputed topics/concepts")
            
            topics = self.global_metadata.topics
            concepts = self.global_metadata.key_concepts
            
            # Format response based on question
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are answering a question about topics and concepts from a video.

Main Topics Discussed:
{topics}

Key Concepts Explained:
{concepts}

Answer the user's specific question. If they ask for a specific number (e.g., "7 concepts"), 
provide that many if available. Present the information clearly."""),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({
                "topics": "\n".join(f"{i+1}. {t}" for i, t in enumerate(topics)),
                "concepts": "\n".join(f"{i+1}. {c}" for i, c in enumerate(concepts)),
                "question": question
            })
        
        # Fallback: Extract from transcript using map-reduce
        if debug:
            print("Extracting topics from transcript (no precomputed data)")
        
        # Use chunks from vector store
        all_docs = self.vector_store.similarity_search("main topics concepts themes", k=20)
        
        if not all_docs:
            return "Could not extract topics - no transcript chunks available."
        
        # Combine chunks
        combined_text = "\n\n".join([doc.page_content for doc in all_docs[:15]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze this transcript and extract the main topics and key concepts discussed.

Transcript sections:
{transcript}

List the distinct topics and concepts clearly. Be specific and avoid repetition."""),
            ("human", "{question}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"transcript": combined_text, "question": question})
    
    def _handle_timeline_query(self, question: str, debug: bool = False) -> str:
        """
        Handle timeline/timestamp questions.
        
        Args:
            question: User's question
            debug: Debug mode
            
        Returns:
            Answer with timestamp information
        """
        # For now, fall back to local QA with increased context
        # In future: use timestamp metadata from chunks
        if debug:
            print("Timeline query - using enhanced retrieval")
        
        return self._handle_local_qa(question, debug)


def load_rag_chain():
    """Load RAG chain from persistent vector store (backward compatible)."""
    vector_store = load_vector_store()
    
    # Create basic chain for backward compatibility
    retriever = get_retriever(vector_store)

    llm = get_llm()
    if llm is None or ChatPromptTemplate is None or StrOutputParser is None or RunnablePassthrough is None or RunnableLambda is None:
        return None

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context":  retriever| RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question: str, debug: bool = False) -> str:
    """
    Ask a question using RAG chain.
    
    Args:
        rag_chain: RAG chain (can be EnhancedRAGChain or legacy chain)
        question: User's question
        debug: Enable debug mode
        
    Returns:
        Answer string
    """
    if rag_chain is None:
        return "RAG is unavailable because the required LLM dependencies are not installed."

    print(f"Question: {question}")
    
    # Check if it's the enhanced chain
    if isinstance(rag_chain, EnhancedRAGChain):
        answer = rag_chain.invoke(question, debug=debug)
    else:
        # Legacy chain
        answer = rag_chain.invoke(question)
    
    print(f"Answer: {answer}")
    return answer

