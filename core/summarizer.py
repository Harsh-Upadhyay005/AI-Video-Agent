"""
Document Summarization with Chunked Processing.
Handles large documents using map-reduce pattern.
"""

import os
from typing import List, Dict

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatPromptTemplate = None
    StrOutputParser = None
    RunnablePassthrough = None
    RunnableLambda = None
    LANGCHAIN_AVAILABLE = False

from core.mistral_client import get_mistral_client, MistralRateLimitError
from utils.document_chunker import chunk_for_llm_processing
from core.logger import get_logger

logger = get_logger(__name__)


def summarize(transcript: str) -> str:
    """
    Summarize transcript using map-reduce for large documents.
    
    Args:
        transcript: Full transcript text
        
    Returns:
        Summary text
    """
    if not LANGCHAIN_AVAILABLE:
        logger.warning("[Summarizer] LangChain not available")
        return transcript[:1000] + "..." if len(transcript) > 1000 else transcript
    
    if not transcript or not transcript.strip():
        return "No transcript available"
    
    logger.info(f"[Summarizer] Summarizing document: {len(transcript)} chars")
    
    mistral_client = get_mistral_client(temperature=0.3)
    llm = mistral_client._get_llm()
    
    if llm is None:
        logger.warning("[Summarizer] LLM not available")
        return transcript[:1000] + "..." if len(transcript) > 1000 else transcript
    
    # Decide strategy based on size
    if len(transcript) <= 12000:  # ~3k tokens - process directly
        logger.info("[Summarizer] Small document, processing directly")
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert summarizer. Create a concise 2-4 paragraph summary. "
                "Write in plain text (no markdown, no bullet points). Keep it conversational."
            ),
            ("human", "{text}"),
        ])
        
        chain = (
            RunnablePassthrough()
            | RunnableLambda(lambda x: {"text": x})
            | prompt
            | llm
            | StrOutputParser()
        )
        
        try:
            summary = mistral_client.invoke_with_retry(
                chain,
                transcript,
                operation_name="document summarization"
            )
            return summary
        except MistralRateLimitError as e:
            logger.error(f"[Summarizer] Rate limit exceeded: {e}")
            return "Summary unavailable due to API rate limiting. Please try again later."
        except Exception as e:
            logger.error(f"[Summarizer] Error: {e}")
            return "Summary generation failed."
    
    # Large document - use map-reduce
    logger.info("[Summarizer] Large document, using map-reduce")
    
    # Chunk document
    chunks = chunk_for_llm_processing(
        transcript,
        max_tokens=6000,
        metadata={'operation': 'summarization'}
    )
    
    logger.info(f"[Summarizer] Processing {len(chunks)} chunks")
    
    # Map phase: Summarize each chunk
    map_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Summarize this portion of a document concisely. "
            "Focus on key points and main ideas. 2-3 sentences."
        ),
        ("human", "{text}"),
    ])
    
    map_chain = map_prompt | llm | StrOutputParser()
    
    chunk_summaries = []
    
    for i, chunk in enumerate(chunks):
        try:
            logger.debug(f"[Summarizer] Processing chunk {i+1}/{len(chunks)}")
            
            summary = mistral_client.invoke_with_retry(
                map_chain,
                {"text": chunk['text']},
                operation_name=f"summarization (chunk {i+1}/{len(chunks)})"
            )
            
            chunk_summaries.append(summary)
            
        except MistralRateLimitError as e:
            logger.error(f"[Summarizer] Rate limit on chunk {i+1}: {e}")
            # Use partial results
            break
        except Exception as e:
            logger.warning(f"[Summarizer] Error on chunk {i+1}: {e}")
            continue
    
    if not chunk_summaries:
        logger.error("[Summarizer] No chunk summaries generated")
        return "Summary generation failed."
    
    logger.info(f"[Summarizer] Combining {len(chunk_summaries)} chunk summaries")
    
    # Reduce phase: Combine summaries
    combined = "\n\n".join(chunk_summaries)
    
    reduce_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting summarizer. Combine these partial summaries "
            "into one final professional summary. Write 2-4 concise paragraphs "
            "in plain text (no markdown, no bullet points, no special formatting). "
            "Keep it short and conversational."
        ),
        ("human", "{text}"),
    ])
    
    reduce_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | reduce_prompt
        | llm
        | StrOutputParser()
    )
    
    try:
        final_summary = mistral_client.invoke_with_retry(
            reduce_chain,
            combined,
            operation_name="summary consolidation"
        )
        return final_summary
    except MistralRateLimitError as e:
        logger.error(f"[Summarizer] Rate limit on consolidation: {e}")
        # Return combined chunk summaries as fallback
        return combined
    except Exception as e:
        logger.error(f"[Summarizer] Consolidation error: {e}")
        return combined


def generate_title(transcript: str) -> str:
    """
    Generate title from transcript (using beginning of document).
    
    Args:
        transcript: Full transcript text
        
    Returns:
        Generated title
    """
    if not LANGCHAIN_AVAILABLE:
        logger.warning("[Summarizer] LangChain not available for title generation")
        return "Untitled Analysis"
    
    if not transcript or not transcript.strip():
        return "Untitled Analysis"
    
    logger.info("[Summarizer] Generating title")
    
    mistral_client = get_mistral_client(temperature=0.3)
    llm = mistral_client._get_llm()
    
    if llm is None:
        return "Untitled Analysis"
    
    # Use first 2000 characters for title generation
    sample = transcript[:2000]
    
    title_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages([
            (
                "system",
                "Based on the text, generate a short professional title "
                "(max 8 words). Only return the title, nothing else."
            ),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )
    
    try:
        title = mistral_client.invoke_with_retry(
            title_chain,
            sample,
            operation_name="title generation"
        )
        return title.strip()
    except Exception as e:
        logger.error(f"[Summarizer] Title generation error: {e}")
        return "Untitled Analysis"
