"""
PDF Document Processing for AI Video Agent.
Extracts text from PDF documents for RAG-based Q&A.
High performance: supports modern pypdf with fallback to PyPDF2, single-pass extraction.
"""

import os
from pathlib import Path
from typing import Optional, Callable, Tuple

# Try modern pypdf first, then PyPDF2
PDF_BACKEND = None
try:
    import pypdf
    PDF_BACKEND = pypdf
except ImportError:
    try:
        import PyPDF2
        PDF_BACKEND = PyPDF2
    except ImportError:
        PDF_BACKEND = None


def extract_text_from_pdf(
    pdf_path: str,
    progress_callback: Optional[Callable[[str, str], None]] = None
) -> Tuple[str, int]:
    """
    Extract text content from a PDF file in a single fast pass.
    
    Args:
        pdf_path: Path to the PDF file
        progress_callback: Optional callback(stage, message) for progress updates
        
    Returns:
        Tuple of (extracted text content, total page count)
        
    Raises:
        ImportError: If neither pypdf nor PyPDF2 is installed
        FileNotFoundError: If PDF file doesn't exist
        Exception: For other PDF processing errors
    """
    if PDF_BACKEND is None:
        raise ImportError(
            "pypdf or PyPDF2 is required for PDF processing. "
            "Install with: pip install pypdf"
        )
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    file_name = os.path.basename(pdf_path)
    if progress_callback:
        progress_callback("pdf_extraction", f"Opening PDF: {file_name}")
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PDF_BACKEND.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            if progress_callback:
                progress_callback("pdf_extraction", f"Processing {num_pages} pages...")
            
            text_content = []
            report_interval = max(1, num_pages // 10)  # Report progress at 10% steps
            
            for page_num, page in enumerate(pdf_reader.pages):
                if progress_callback and (page_num % report_interval == 0 or page_num == num_pages - 1):
                    progress_callback(
                        "pdf_extraction",
                        f"Extracting page {page_num + 1}/{num_pages}..."
                    )
                
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(f"[Page {page_num + 1}]\n{page_text}")
                except Exception as e:
                    continue
            
            full_text = "\n\n".join(text_content)
            
            if not full_text or not full_text.strip():
                raise ValueError("No text content extracted from PDF. PDF might be image-based or empty.")
            
            if progress_callback:
                progress_callback("pdf_extraction", f"Extracted text from {num_pages} pages")
            
            return full_text, num_pages
            
    except Exception as e:
        if "empty" in str(e).lower() or "image-based" in str(e).lower():
            raise
        raise Exception(f"PDF processing error: {e}")


def is_pdf_file(file_path: str) -> bool:
    """Check if a file is a PDF based on extension."""
    return Path(file_path).suffix.lower() == '.pdf'


def validate_pdf(file_path: str, max_size_mb: int = 500) -> tuple[bool, str]:
    """
    Validate PDF file before processing.
    
    Args:
        file_path: Path to the PDF file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "PDF file not found"
    
    if not is_pdf_file(file_path):
        return False, "File is not a PDF"
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"PDF file too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)"
    
    return True, ""


def process_pdf_document(
    pdf_path: str,
    progress_callback: Optional[Callable[[str, str], None]] = None
) -> dict:
    """
    Process PDF document in a single pass and return structured data.
    
    Args:
        pdf_path: Path to the PDF file
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary with text, page_count, file_name, char_count
    """
    # Validate PDF
    is_valid, error_msg = validate_pdf(pdf_path)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Extract text and page count in one single pass
    text, page_count = extract_text_from_pdf(pdf_path, progress_callback)
    
    result = {
        "text": text,
        "page_count": page_count,
        "file_name": os.path.basename(pdf_path),
        "char_count": len(text)
    }
    
    return result
