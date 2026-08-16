import os 
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"

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

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(transcript)

    # Build documents with metadata
    docs = []
    base_metadata = metadata or {}
    
    for i, chunk in enumerate(chunks):
        chunk_metadata = {
            'chunk_index': i,
            'chunk_total': len(chunks),
            **base_metadata  # Include any additional metadata
        }
        docs.append(Document(page_content=chunk, metadata=chunk_metadata))

    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR
    )

    print(f"[VectorStore] Created {len(docs)} document chunks with metadata")
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


