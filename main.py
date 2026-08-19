from dotenv import load_dotenv
from typing import Optional, Callable
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()


def _summarize_transcript(transcript: str) -> str:
    try:
        from core.summarizer import summarize, generate_title
    except ImportError:
        return transcript.strip() or "No transcript available"

    return summarize(transcript)


def _generate_title(transcript: str) -> str:
    try:
        from core.summarizer import summarize, generate_title
    except ImportError:
        return "Untitled Analysis"

    return generate_title(transcript)


def run_pipeline(
    source: str, 
    language: str = "english",
    progress_callback: Optional[Callable[[str, str, Optional[int]], None]] = None,
    source_key: Optional[str] = None
) -> dict:
    """
    Main pipeline for video/audio/document analysis with optional progress tracking.
    
    Args:
        source: YouTube URL, local audio/video file path, or PDF document path
        language: Language for transcription (english or hinglish) - ignored for PDFs
        progress_callback: Optional callback(stage, message, progress_percent)
        source_key: Optional unique key for storing RAG chain (defaults to source)
    
    Returns:
        Dictionary with analysis results (JSON-serializable data only)
        Note: RAG chain is built and stored internally, but NOT returned
    """
    print("Starting AI Video Assistant")
    
    if progress_callback:
        progress_callback("initialization", "Starting pipeline...", 5)

    # Check if source is a PDF document
    is_pdf = source.lower().endswith('.pdf')
    
    if is_pdf:
        # Handle PDF document processing
        print("[Pipeline] Detected PDF document")
        
        if progress_callback:
            progress_callback("pdf_processing", "Processing PDF document...", 15)
        
        try:
            from utils.pdf_processor import process_pdf_document
            
            def pdf_progress(stage: str, message: str):
                if progress_callback:
                    progress_callback(stage, message, 30)
            
            pdf_data = process_pdf_document(source, progress_callback=pdf_progress)
            transcript = pdf_data["text"]
            
            print(f"[Pipeline] Extracted {pdf_data['char_count']} characters from {pdf_data['page_count']} pages")
            
            # Generate title from PDF filename or first lines
            title = pdf_data["file_name"].replace('.pdf', '').replace('_', ' ').title()
            
        except ImportError:
            error_msg = "PDF processing requires PyPDF2. Install with: pip install PyPDF2"
            print(f"ERROR: {error_msg}")
            if progress_callback:
                progress_callback("error", error_msg, 0)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"PDF processing failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            if progress_callback:
                progress_callback("error", error_msg, 0)
            raise ValueError(error_msg)
    else:
        # Handle audio/video processing (existing logic)
        if progress_callback:
            progress_callback("downloading", "Downloading and processing audio...", 15)
        chunks = process_input(source)
        
        # Transcribe with progress updates
        if progress_callback:
            progress_callback("transcription", f"Transcribing {len(chunks)} audio chunks...", 25)
        
        def transcription_progress(stage: str, message: str):
            """Wrapper for transcription progress."""
            if progress_callback:
                # Map transcription stages to progress percentages (25-60%)
                progress_map = {
                    "transcription_started": 25,
                    "transcribing_chunk": 30,
                    "chunk_completed": 45,
                    "transcription_complete": 60
                }
                progress_callback(stage, message, progress_map.get(stage, 40))
        
        transcript = transcribe_all(chunks, language, progress_callback=transcription_progress)
        print(f"Raw transcription (first 300 characters): {transcript[:300] if transcript else '(empty)'}")
        
        # Generate title
        if progress_callback:
            progress_callback("title_generation", "Generating title...", 65)
        title = _generate_title(transcript)
    
    # Validate transcript/document text
    if not transcript or transcript.strip() == "":
        error_msg = "No content detected: Transcription or document extraction returned empty result"
        print(f"ERROR: {error_msg}")
        if progress_callback:
            progress_callback("error", error_msg, 0)
        raise ValueError(error_msg)

    # Summarize
    if progress_callback:
        progress_callback("summarization", "Creating summary...", 70)
    summary = _summarize_transcript(transcript)

    # Extract insights
    if progress_callback:
        progress_callback("extraction", "Extracting action items...", 75)
    action_item = extract_action_items(transcript)
    
    if progress_callback:
        progress_callback("extraction", "Extracting key decisions...", 80)
    decisions = extract_key_decisions(transcript)
    
    if progress_callback:
        progress_callback("extraction", "Extracting open questions...", 85)
    questions = extract_questions(transcript)
    
    # Build RAG chain (stored internally for chat, not returned in result)
    if progress_callback:
        progress_callback("rag_building", "Building knowledge base for chat...", 90)
    
    # Use source_key if provided, otherwise use source
    storage_key = source_key if source_key else source
    
    # Prepare metadata for vector store
    vector_metadata = {
        'video_id': storage_key,
        'source': source,
        'language': language if not is_pdf else 'document'
    }
    
    rag_chain = build_rag_chain(transcript, video_id=storage_key, metadata=vector_metadata)
    
    # Generate and store global metadata (topics, concepts, etc.)
    if progress_callback:
        progress_callback("global_analysis", "Analyzing video structure and topics...", 95)
    
    try:
        from core.global_analyzer import analyze_video_global
        from core.global_metadata import save_video_metadata
        
        # Determine source type
        source_type = "youtube" if "youtube.com" in source.lower() or "youtu.be" in source.lower() else "file"
        
        # Analyze and extract global information
        global_metadata = analyze_video_global(
            video_id=storage_key,
            source=source,
            source_type=source_type,
            transcript=transcript,
            title=title,
            duration=None  # Could extract from audio processing if needed
        )
        
        # Save for later use
        save_video_metadata(global_metadata)
        print(f"[Pipeline] Saved global metadata: {len(global_metadata.topics)} topics, {len(global_metadata.key_concepts)} concepts")
    except Exception as e:
        print(f"[Pipeline] Warning: Global metadata generation failed: {e}")
        # Continue anyway - global metadata is optional enhancement
    
    # Store RAG chain internally for later use by chat endpoint
    # Use source_key if provided, otherwise use source
    _store_rag_chain_internally(storage_key, rag_chain)
    
    if progress_callback:
        progress_callback("complete", "Analysis complete!", 100)

    # Return ONLY JSON-serializable data (no LangChain objects)
    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        # NOTE: rag_chain is NOT included here - it's stored separately
    }


# Internal storage for RAG chains (in production, use Redis or database)
_rag_chain_store = {}


def _store_rag_chain_internally(source_key: str, rag_chain):
    """
    Store RAG chain internally for chat functionality.
    
    Args:
        source_key: Unique identifier for the source (e.g., job_id or hash)
        rag_chain: The LangChain RunnableSequence
    """
    _rag_chain_store[source_key] = rag_chain


def get_rag_chain_for_source(source_key: str):
    """
    Retrieve stored RAG chain for a given source.
    
    Args:
        source_key: Unique identifier for the source
        
    Returns:
        The stored RAG chain or None if not found
    """
    return _rag_chain_store.get(source_key)


if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    
    try:
        result = run_pipeline(source, language)
    except ValueError as e:
        print(f"\nERROR: {e}")
        exit(1)

    print("\n" + "=" * 60)
    print(f" Title: {result['title']}")
    print(f"\n Summary:\n{result['summary']}")
    print(f"\n Action Items:\n{result['action_items']}")
    print(f"\n Key Decisions:\n{result['key_decisions']}")
    print(f"\n Open Questions:\n{result['open_questions']}")
    print("=" * 60)

    # Phase 2 — Chat with your meeting via RAG
    print("\n Chat with your meeting (type 'exit' to quit)\n")
    
    # Get the RAG chain from internal storage
    rag_chain = get_rag_chain_for_source(source)
    
    if rag_chain is None:
        print("RAG chain not available. Chat functionality disabled.")
    else:
        while True:
            question = input("You: ").strip()
            if question.lower() in ["exit", "quit", "q"]:
                print(" Goodbye!")
                break
            if not question:
                continue
            answer = ask_question(rag_chain, question)
            print(f"\n Assistant: {answer}\n")

