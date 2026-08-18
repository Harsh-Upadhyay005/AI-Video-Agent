import os 
import hashlib
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"  # Default for backward compatibility
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"


def _get_collection_name(video_id: str = None) -> str:
    """
    Generate a unique collection name for a video to prevent cross-contamination.
    
    Args:
        video_id: Optional video identifier
        
    Returns:
        Collection name (sanitized for ChromaDB)
    """
    if not video_id:
        return COLLECTION_NAME  # Backward compatible default
    
    # Sanitize video_id for ChromaDB (alphanumeric, underscores, hyphens only)
    # ChromaDB collection names must be 3-63 chars, start/end with alphanumeric
    sanitized = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in video_id)
    
    # Ensure it starts with letter or number
    if sanitized and not sanitized[0].isalnum():
        sanitized = 'v_' + sanitized
    
    # Limit length (ChromaDB max is 63 chars)
    if len(sanitized) > 60:
        # Use hash suffix to ensure uniqueness
        hash_suffix = hashlib.md5(video_id.encode()).hexdigest()[:8]
        sanitized = sanitized[:50] + '_' + hash_suffix
    
    return sanitized or COLLECTION_NAME

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {"device" : 'cpu'}
    )

def build_vector_store(transcript: str, metadata: dict = None) -> Chroma:
    """
    Build vector store from transcript with optional metadata.
    
    Args:
        transcript: Full transcript text
        metadata: Optional dict with video_id, source, timestamps, etc.
    
    Returns:
        Chroma vector store
    """
    print("Building vector Store")

    # Increased chunk size to preserve semantic coherence
    # Larger chunks help keep complete concepts together
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,  # Increased from 500 to reduce fragmentation
        chunk_overlap=200,  # Increased overlap to maintain context
        separators=["\n\n", "\n", ". ", " ", ""]  # Prefer natural boundaries
    )
    chunks = splitter.split_text(transcript)

    # Build documents with metadata
    docs = []
    base_metadata = metadata or {}
    video_id = base_metadata.get('video_id')
    
    for i, chunk in enumerate(chunks):
        chunk_metadata = {
            'chunk_index': i,
            'chunk_total': len(chunks),
            **base_metadata  # Include any additional metadata
        }
        docs.append(Document(page_content=chunk, metadata=chunk_metadata))

    embeddings = get_embeddings()
    
    # Use per-video collection to prevent cross-contamination
    collection_name = _get_collection_name(video_id)
    
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_DIR
    )

    print(f"[VectorStore] Created {len(docs)} document chunks in collection '{collection_name}'")
    return vector_store



def load_vector_store() ->Chroma:
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function= embeddings,
        persist_directory=CHROMA_DIR
    )

    return vector_store

def get_retriever(vector_store : Chroma, k :int = 4):
    return vector_store.as_retriever(
        search_type = 'similarity',
        search_kwargs = {"k":k}
    )


