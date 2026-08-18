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
    Build RAG chain with enhanced metadata support and context window protection.
    
    Args:
        transcript: Full transcript text
        video_id: Optional video ID for global metadata lookup
        metadata: Optional metadata dict (source, timestamps, etc.)
    
    Returns:
        Enhanced RAG chain with routing capability
    """
    # Context window protection: Check transcript size
    transcript_length = len(transcript)
    print(f"[RAG] Building chain for transcript: {transcript_length} chars")
    
    if transcript_length > 500000:  # ~125k tokens
        print(f"[RAG] WARNING: Very long transcript ({transcript_length} chars). "
              "Some operations may be slow or hit token limits.")
    
    # Build vector store with metadata
    vector_store_metadata = metadata or {}
    if video_id:
        vector_store_metadata['video_id'] = video_id
    
    vector_store = build_vector_store(transcript, metadata=vector_store_metadata)
    
    # Create enhanced RAG chain that supports routing
    enhanced_chain = EnhancedRAGChain(
        vector_store=vector_store,
        video_id=video_id,
        full_transcript=transcript if transcript_length < 50000 else ""  # Only store if manageable
    )
    
    return enhanced_chain


class EnhancedRAGChain:
    """
    Enhanced RAG chain with query intent routing and conversation memory.
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
        
        # Conversation memory (simple list of recent Q&A pairs)
        self.conversation_history = []
        self.max_history = 5  # Keep last 5 exchanges
        
        # Load global metadata if available
        self.global_metadata = None
        if video_id:
            try:
                self.global_metadata = load_video_metadata(video_id)
                if self.global_metadata:
                    print(f"[EnhancedRAG] Loaded global metadata for {video_id}: "
                          f"{len(self.global_metadata.topics)} topics, "
                          f"{len(self.global_metadata.key_concepts)} concepts")
                else:
                    print(f"[EnhancedRAG] No global metadata found for {video_id}")
            except Exception as e:
                print(f"[EnhancedRAG] Warning: Could not load global metadata: {e}")
    
    def _add_to_history(self, question: str, answer: str):
        """Add Q&A pair to conversation history."""
        self.conversation_history.append({"question": question, "answer": answer})
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def _rewrite_followup_question(self, question: str) -> str:
        """
        Rewrite follow-up questions into standalone questions using conversation history.
        
        Args:
            question: User's question (may contain references like "it", "the third one")
            
        Returns:
            Rewritten standalone question
        """
        # Check if this looks like a follow-up question
        followup_indicators = [
            r'\b(it|this|that|they|them|these|those)\b',
            r'\b(the\s+(first|second|third|fourth|fifth|last|previous))\b',
            r'\b(what\s+about|how\s+about)\b',
            r'\b(explain\s+(more|further|that))\b',
            r'\b(tell\s+me\s+more)\b'
        ]
        
        import re
        is_followup = any(re.search(pattern, question.lower()) for pattern in followup_indicators)
        
        if not is_followup or not self.conversation_history:
            return question  # Not a follow-up or no history
        
        # Use LLM to rewrite with context
        if self.llm is None or ChatPromptTemplate is None or StrOutputParser is None:
            return question  # Can't rewrite, return as-is
        
        # Get recent context
        recent_context = "\n".join([
            f"Q: {h['question']}\nA: {h['answer'][:200]}..."
            for h in self.conversation_history[-2:]  # Last 2 exchanges
        ])
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are helping rewrite a follow-up question into a standalone question.

Recent conversation:
{context}

The user's new question may contain references (like "it", "the third one", "that") that refer to the conversation above.

Rewrite the question to be standalone and clear, replacing pronouns and references with specific terms from the conversation.

If the question is already standalone, return it unchanged.

Return ONLY the rewritten question, nothing else."""),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            rewritten = chain.invoke({"context": recent_context, "question": question})
            
            print(f"[FollowUp] Rewritten: '{question}' → '{rewritten}'")
            return rewritten.strip()
            
        except Exception as e:
            print(f"[FollowUp] Error rewriting question: {e}")
            return question  # Return original on error
    
    def invoke(self, question: str, debug: bool = False) -> str:
        """
        Process question with intent-based routing and conversation memory.
        
        Args:
            question: User's question (may be a follow-up)
            debug: If True, print debug information
            
        Returns:
            Answer string
        """
        # Rewrite follow-up questions into standalone questions
        standalone_question = self._rewrite_followup_question(question)
        
        # Classify query intent
        classified = classify_query(standalone_question)
        
        if debug:
            print(f"\n[RAG Debug]")
            print(f"Original Question: {question}")
            if standalone_question != question:
                print(f"Standalone Question: {standalone_question}")
            print(f"Intent: {classified.intent.value}")
            print(f"Confidence: {classified.confidence}")
            print(f"Reasoning: {classified.reasoning}")
        
        # Route to appropriate strategy
        if classified.intent == QueryIntent.GLOBAL_SUMMARY:
            answer = self._handle_global_summary(standalone_question, debug)
        elif classified.intent == QueryIntent.TOPIC_EXTRACTION:
            answer = self._handle_topic_extraction(standalone_question, debug)
        elif classified.intent == QueryIntent.TIMELINE:
            answer = self._handle_timeline_query(standalone_question, debug)
        else:  # LOCAL_QA
            answer = self._handle_local_qa(standalone_question, debug)
        
        # Add to conversation history
        self._add_to_history(question, answer)
        
        return answer
    
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
        retriever = get_retriever(self.vector_store, k=10)  # Increased from 8
        docs = retriever.invoke(question)
        
        if debug:
            print(f"Retrieved {len(docs)} chunks for local QA")
            for i, doc in enumerate(docs[:3]):
                print(f"Chunk {i+1} (score in metadata): {doc.page_content[:100]}...")
        
        context = format_docs(docs)
        
        # Enhanced prompt with strict grounding
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert assistant analyzing a video/audio transcript.

**CRITICAL RULES:**
1. Answer ONLY using the context provided below
2. Do NOT use outside knowledge or general information about topics
3. Do NOT invent facts, examples, or explanations not in the context
4. If the answer is not in the context, say: "I could not find this information in the transcript."
5. Be precise and cite relevant parts of the transcript when possible

**Context from transcript:**
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
                print("Using precomputed global metadata for summary")
            
            summary = self.global_metadata.summary
            topics = self.global_metadata.topics
            concepts = self.global_metadata.key_concepts
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are answering a question about an entire video/audio recording.

You have access to precomputed information about the video:

**Video Summary:**
{summary}

**Main Topics Discussed:**
{topics}

**Key Concepts:**
{concepts}

**CRITICAL RULES:**
1. Use ONLY the information provided above
2. Do NOT add topics/concepts from general knowledge
3. Do NOT invent details not in the summary
4. Be comprehensive but concise

Answer the user's question based strictly on this global information."""),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({
                "summary": summary,
                "topics": "\n".join(f"• {t}" for t in topics),
                "concepts": "\n".join(f"• {c}" for c in concepts),
                "question": question
            })
        
        # Fallback: Use full transcript if available and not too long
        if self.full_transcript:
            if debug:
                print(f"Using full transcript for global summary (length: {len(self.full_transcript)} chars)")
            
            # Truncate if too long to fit in context
            transcript_sample = self.full_transcript[:15000]  # Increased from 8000
            truncated = len(self.full_transcript) > 15000
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are answering a question about an entire video/audio recording.

{"Below is the complete transcript:" if not truncated else "Below is the transcript (first portion):"}

{transcript}

{"" if not truncated else "Note: This is a partial transcript. Base your answer on what's available."}

**CRITICAL RULES:**
1. Use ONLY information from the transcript provided
2. Do NOT add information from general knowledge
3. Provide a comprehensive answer about the overall content

Answer the user's question about the overall content."""),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({
                "transcript": transcript_sample,
                "truncated": truncated,
                "question": question
            })
        
        # Last resort: Cannot provide global summary
        return "Cannot provide a complete summary - neither global metadata nor full transcript is available. Please re-analyze the video to generate global metadata."
    
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
        
        # ALWAYS try to use precomputed metadata first for topic extraction
        if self.global_metadata and (self.global_metadata.topics or self.global_metadata.key_concepts):
            if debug:
                print(f"Using precomputed global metadata: {len(self.global_metadata.topics)} topics, "
                      f"{len(self.global_metadata.key_concepts)} concepts")
            
            topics = self.global_metadata.topics
            concepts = self.global_metadata.key_concepts
            
            # Enhanced prompt with strict grounding
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are answering a question about topics and concepts from a video/audio recording.

You have access to precomputed information extracted from the complete transcript:

**Main Topics Discussed:**
{topics}

**Key Concepts Explained:**
{concepts}

**CRITICAL RULES:**
1. Use ONLY the topics and concepts listed above
2. Do NOT add topics/concepts not in the lists
3. Do NOT use outside knowledge about these topics
4. If the user asks for more items than available, explain that only N were discussed
5. Present information clearly and accurately

Answer the user's question based strictly on the information provided."""),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            
            try:
                answer = chain.invoke({
                    "topics": "\n".join(f"{i+1}. {t}" for i, t in enumerate(topics)),
                    "concepts": "\n".join(f"{i+1}. {c}" for i, c in enumerate(concepts)),
                    "question": question
                })
                return answer
            except Exception as e:
                print(f"[EnhancedRAG] Error in topic extraction with metadata: {e}")
                # Fall through to fallback
        
        # Fallback: Use full transcript if available
        if self.full_transcript and len(self.full_transcript) < 12000:
            if debug:
                print("Fallback: Extracting topics from full transcript")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are analyzing a complete transcript to extract topics and concepts.

**Complete Transcript:**
{transcript}

**CRITICAL RULES:**
1. Extract ONLY topics/concepts actually discussed in this transcript
2. Do NOT add topics from general knowledge
3. Be specific and accurate
4. If fewer topics than requested exist, say so clearly

Analyze the transcript and answer the user's question."""),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            
            try:
                answer = chain.invoke({
                    "transcript": self.full_transcript,
                    "question": question
                })
                return answer
            except Exception as e:
                print(f"[EnhancedRAG] Error in transcript-based extraction: {e}")
        
        # Last resort: Extract from retrieved chunks (less reliable)
        if debug:
            print("Last resort: Extracting topics from retrieved chunks (may be incomplete)")
        
        # Use broader retrieval for topic extraction
        all_docs = self.vector_store.similarity_search("", k=50)  # Get many chunks
        
        if not all_docs:
            return "Could not extract topics - no transcript chunks available."
        
        # Combine chunks (limit to avoid token overflow)
        combined_text = "\n\n".join([doc.page_content for doc in all_docs[:20]])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze these transcript sections and extract the main topics and key concepts.

**WARNING:** You only have access to PORTIONS of the transcript. Be cautious about making definitive statements about "all" topics.

**Transcript Sections:**
{transcript}

Extract topics and concepts clearly. If the user asks for a specific number, note if you can only identify fewer based on available sections."""),
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

