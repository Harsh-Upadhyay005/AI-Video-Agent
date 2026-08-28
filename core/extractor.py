"""
Content Extraction with Chunked Processing for Large Documents.
Extracts action items, key decisions, and open questions.
"""

import os
from typing import List, Dict, Optional

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


def _build_extraction_chain(system_prompt: str):
    """
    Build LangChain extraction chain.
    
    Args:
        system_prompt: System prompt for extraction
        
    Returns:
        LangChain chain or None if dependencies unavailable
    """
    if not LANGCHAIN_AVAILABLE:
        return None
    
    mistral_client = get_mistral_client(temperature=0.2)
    llm = mistral_client._get_llm()
    
    if llm is None:
        return None
    
    return (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )


def _extract_from_chunks(
    chunks: List[Dict],
    extraction_type: str,
    system_prompt: str
) -> str:
    """
    Extract information from chunks using map-reduce pattern.
    
    Args:
        chunks: List of document chunks
        extraction_type: Type of extraction (for logging)
        system_prompt: System prompt for extraction
        
    Returns:
        Combined extraction results
    """
    if not chunks:
        logger.warning(f"[Extractor] No chunks provided for {extraction_type}")
        return f"No {extraction_type} found."
    
    if len(chunks) == 1 and chunks[0]['token_count'] < 6000:
        # Single small chunk - process directly
        logger.info(f"[Extractor] {extraction_type}: Processing single chunk ({chunks[0]['token_count']} tokens)")
        chain = _build_extraction_chain(system_prompt)
        
        if chain is None:
            return f"No {extraction_type} found."
        
        try:
            mistral_client = get_mistral_client()
            result = mistral_client.invoke_with_retry(
                chain,
                chunks[0]['text'],
                operation_name=f"{extraction_type} extraction"
            )
            return result
        except MistralRateLimitError as e:
            logger.error(f"[Extractor] Rate limit exceeded for {extraction_type}: {e}")
            return f"Could not extract {extraction_type} due to API rate limiting. Please try again later."
        except Exception as e:
            logger.error(f"[Extractor] Error extracting {extraction_type}: {e}")
            return f"Error extracting {extraction_type}."
    
    # Multiple chunks or large chunk - use map-reduce
    logger.info(f"[Extractor] {extraction_type}: Processing {len(chunks)} chunks with map-reduce")
    
    # Map phase: Extract from each chunk
    chunk_results = []
    mistral_client = get_mistral_client()
    
    map_prompt = f"{system_prompt}\n\nNote: This is part of a larger document. Extract all relevant items from this section."
    map_chain = _build_extraction_chain(map_prompt)
    
    if map_chain is None:
        return f"No {extraction_type} found."
    
    for i, chunk in enumerate(chunks):
        try:
            logger.debug(f"[Extractor] Processing chunk {i+1}/{len(chunks)} ({chunk['token_count']} tokens)")
            
            result = mistral_client.invoke_with_retry(
                map_chain,
                chunk['text'],
                operation_name=f"{extraction_type} extraction (chunk {i+1}/{len(chunks)})"
            )
            
            # Only keep non-empty results
            if result and "no " not in result.lower()[:20]:
                chunk_results.append(result)
                
        except MistralRateLimitError as e:
            logger.error(f"[Extractor] Rate limit on chunk {i+1}: {e}")
            # Continue with what we have so far
            break
        except Exception as e:
            logger.warning(f"[Extractor] Error on chunk {i+1}: {e}")
            continue
    
    if not chunk_results:
        return f"No {extraction_type} found."
    
    # Reduce phase: Combine and deduplicate results
    logger.info(f"[Extractor] {extraction_type}: Combining {len(chunk_results)} chunk results")
    
    combined_text = "\n\n".join(chunk_results)
    
    # If combined results are reasonable size, do final consolidation
    if len(combined_text) < 24000:  # ~6k tokens
        reduce_prompt = (
            f"You are consolidating {extraction_type} extracted from different parts of a document.\n\n"
            f"Below are {extraction_type} found in various sections:\n\n"
            f"{{text}}\n\n"
            f"Your task:\n"
            f"1. Merge similar or duplicate items\n"
            f"2. Remove redundancies\n"
            f"3. Organize into a clear numbered list\n"
            f"4. Preserve all unique items\n"
            f"5. If there are no {extraction_type}, say 'No {extraction_type} found.'\n\n"
            f"Provide the final consolidated list."
        )
        
        reduce_chain = _build_extraction_chain(reduce_prompt)
        
        if reduce_chain:
            try:
                final_result = mistral_client.invoke_with_retry(
                    reduce_chain,
                    combined_text,
                    operation_name=f"{extraction_type} consolidation"
                )
                return final_result
            except Exception as e:
                logger.warning(f"[Extractor] Consolidation failed: {e}. Returning combined results.")
    
    # Return combined results if consolidation not possible
    return combined_text


def extract_action_items(transcript: str) -> str:
    """
    Extract action items from transcript with chunked processing.
    
    Args:
        transcript: Full transcript text
        
    Returns:
        Formatted action items
    """
    logger.info(f"[Extractor] Extracting action items from {len(transcript)} chars")
    
    if not LANGCHAIN_AVAILABLE:
        logger.warning("[Extractor] LangChain not available")
        return "No action items found."
    
    # Check transcript size
    if len(transcript) > 30000:  # ~7.5k tokens
        logger.info("[Extractor] Large transcript detected, using chunked processing")
        chunks = chunk_for_llm_processing(
            transcript,
            max_tokens=6000,
            metadata={'extraction_type': 'action_items'}
        )
    else:
        # Small transcript - process as single chunk
        chunks = [{'text': transcript, 'token_count': len(transcript) // 4}]
    
    system_prompt = (
        "You are an expert meeting analyst. From the transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'"
    )
    
    return _extract_from_chunks(chunks, "action items", system_prompt)


def extract_key_decisions(transcript: str) -> str:
    """
    Extract key decisions from transcript with chunked processing.
    
    Args:
        transcript: Full transcript text
        
    Returns:
        Formatted key decisions
    """
    logger.info(f"[Extractor] Extracting key decisions from {len(transcript)} chars")
    
    if not LANGCHAIN_AVAILABLE:
        logger.warning("[Extractor] LangChain not available")
        return "No key decisions found."
    
    # Check transcript size
    if len(transcript) > 30000:
        logger.info("[Extractor] Large transcript detected, using chunked processing")
        chunks = chunk_for_llm_processing(
            transcript,
            max_tokens=6000,
            metadata={'extraction_type': 'key_decisions'}
        )
    else:
        chunks = [{'text': transcript, 'token_count': len(transcript) // 4}]
    
    system_prompt = (
        "You are an expert meeting analyst. From the transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'"
    )
    
    return _extract_from_chunks(chunks, "key decisions", system_prompt)


def extract_questions(transcript: str) -> str:
    """
    Extract open questions from transcript with chunked processing.
    
    Args:
        transcript: Full transcript text
        
    Returns:
        Formatted open questions
    """
    logger.info(f"[Extractor] Extracting open questions from {len(transcript)} chars")
    
    if not LANGCHAIN_AVAILABLE:
        logger.warning("[Extractor] LangChain not available")
        return "No open questions found."
    
    # Check transcript size
    if len(transcript) > 30000:
        logger.info("[Extractor] Large transcript detected, using chunked processing")
        chunks = chunk_for_llm_processing(
            transcript,
            max_tokens=6000,
            metadata={'extraction_type': 'open_questions'}
        )
    else:
        chunks = [{'text': transcript, 'token_count': len(transcript) // 4}]
    
    system_prompt = (
        "From the transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'"
    )
    
    return _extract_from_chunks(chunks, "open questions", system_prompt)
