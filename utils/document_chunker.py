"""
Centralized Document Chunking Utility.
Provides token-aware chunking for PDFs, transcripts, and other documents.
"""

from typing import List, Optional
from dataclasses import dataclass

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    import tiktoken
    CHUNKING_AVAILABLE = True
except ImportError:
    RecursiveCharacterTextSplitter = None
    tiktoken = None
    CHUNKING_AVAILABLE = False

from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for document chunking."""
    chunk_size: int = 8000  # Characters (roughly 2000 tokens)
    chunk_overlap: int = 500
    separators: List[str] = None
    model: str = "gpt-3.5-turbo"  # For token counting
    
    def __post_init__(self):
        if self.separators is None:
            # Default separators: prefer natural boundaries
            self.separators = [
                "\n\n",  # Paragraph breaks
                "\n",    # Line breaks
                ". ",    # Sentences
                "! ",
                "? ",
                ";",
                ":",
                " ",     # Words
                ""       # Characters
            ]


class DocumentChunker:
    """
    Handles intelligent chunking of large documents.
    Supports both character-based and token-aware chunking.
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize document chunker.
        
        Args:
            config: Chunking configuration (uses defaults if None)
        """
        if not CHUNKING_AVAILABLE:
            raise ImportError(
                "Chunking dependencies not available. "
                "Install with: pip install langchain-text-splitters tiktoken"
            )
        
        self.config = config or ChunkingConfig()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators,
            length_function=len  # Character-based for now
        )
        
        # Try to load tokenizer for accurate token counting
        self.tokenizer = None
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.config.model)
        except Exception as e:
            logger.warning(f"[Chunker] Could not load tokenizer: {e}. Using character-based estimation.")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
            
        Returns:
            Estimated token count
        """
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback: rough estimation (1 token ≈ 4 characters)
        return len(text) // 4
    
    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> List[dict]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with 'text', 'index', 'tokens', and metadata
        """
        if not text or not text.strip():
            logger.warning("[Chunker] Empty text provided for chunking")
            return []
        
        logger.info(f"[Chunker] Chunking document: {len(text)} chars")
        
        # Split text
        chunks = self.splitter.split_text(text)
        
        # Add metadata
        result = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'text': chunk,
                'index': i,
                'total_chunks': len(chunks),
                'char_count': len(chunk),
                'token_count': self.count_tokens(chunk)
            }
            
            # Add custom metadata
            if metadata:
                chunk_data.update(metadata)
            
            result.append(chunk_data)
        
        # Log statistics
        total_tokens = sum(c['token_count'] for c in result)
        avg_tokens = total_tokens // len(result) if result else 0
        
        logger.info(
            f"[Chunker] Created {len(result)} chunks: "
            f"avg {avg_tokens} tokens/chunk, {total_tokens} total tokens"
        )
        
        return result
    
    def chunk_for_processing(
        self,
        text: str,
        max_chunk_tokens: int = 6000,
        metadata: Optional[dict] = None
    ) -> List[dict]:
        """
        Chunk text specifically for LLM processing with token limits.
        
        Args:
            text: Text to chunk
            max_chunk_tokens: Maximum tokens per chunk (with safety margin)
            metadata: Optional metadata
            
        Returns:
            List of chunks safe for LLM processing
        """
        # Adjust chunk size based on token limit
        # Add safety margin: use 75% of max to account for prompt overhead
        safe_char_limit = int(max_chunk_tokens * 0.75 * 4)  # ~4 chars per token
        
        # Create temporary config with adjusted size
        temp_config = ChunkingConfig(
            chunk_size=min(safe_char_limit, self.config.chunk_size),
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators
        )
        
        temp_chunker = DocumentChunker(temp_config)
        return temp_chunker.chunk_text(text, metadata)


# Global chunker instance
_default_chunker: Optional[DocumentChunker] = None


def get_default_chunker() -> DocumentChunker:
    """
    Get default document chunker instance.
    
    Returns:
        DocumentChunker with default configuration
    """
    global _default_chunker
    if _default_chunker is None:
        _default_chunker = DocumentChunker()
    return _default_chunker


def chunk_document(
    text: str,
    chunk_size: int = 8000,
    chunk_overlap: int = 500,
    metadata: Optional[dict] = None
) -> List[dict]:
    """
    Convenience function for chunking documents.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        chunk_overlap: Overlap between chunks
        metadata: Optional metadata
        
    Returns:
        List of chunks
    """
    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunker = DocumentChunker(config)
    return chunker.chunk_text(text, metadata)


def chunk_for_llm_processing(
    text: str,
    max_tokens: int = 6000,
    metadata: Optional[dict] = None
) -> List[dict]:
    """
    Chunk document for LLM processing with token limits.
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        metadata: Optional metadata
        
    Returns:
        List of chunks safe for LLM
    """
    chunker = get_default_chunker()
    return chunker.chunk_for_processing(text, max_tokens, metadata)
