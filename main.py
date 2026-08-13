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
    progress_callback: Optional[Callable[[str, str, Optional[int]], None]] = None
) -> dict:
    """
    Main pipeline for video/audio analysis with optional progress tracking.
    
    Args:
        source: YouTube URL or local file path
        language: Language for transcription (english or hinglish)
        progress_callback: Optional callback(stage, message, progress_percent)
    
    Returns:
        Dictionary with analysis results
    """
    print("Starting AI Video Assistant")
    
    if progress_callback:
        progress_callback("initialization", "Starting pipeline...", 5)

    # Process audio input
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
    
    transcript = transcribe_all(chunks, language, progress_callback=transcription_progress, parallel=True)
    print(f"Raw transcription (first 300 characters): {transcript[:300]}")

    # Generate title
    if progress_callback:
        progress_callback("title_generation", "Generating title...", 65)
    title = _generate_title(transcript)

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
    
    # Build RAG chain
    if progress_callback:
        progress_callback("rag_building", "Building knowledge base for chat...", 90)
    rag_chain = build_rag_chain(transcript)
    
    if progress_callback:
        progress_callback("complete", "Analysis complete!", 100)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f" Title: {result['title']}")
    print(f"\n Summary:\n{result['summary']}")
    print(f"\n Action Items:\n{result['action_items']}")
    print(f"\n Key Decisions:\n{result['key_decisions']}")
    print(f"\n Open Questions:\n{result['open_questions']}")
    print("=" * 60)

    # Phase 2 — Chat with your meeting via RAG
    print("\n Chat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print(" Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\n Assistant: {answer}\n")