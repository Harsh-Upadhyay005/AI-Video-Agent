"""
PDF Document Processing for AI Video Agent.
Extracts text from PDF documents for RAG-based Q&A.
"""

import os
from pathlib import Path
from typing import Optional, Callable

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("[PDFProcessor] Warning: PyPDF2 not installed. PDF support disabled.")


def extract_text_from_pdf(
    pdf_path: str,
    progress_callback: Optional[Callable[[str, str], None]] = None
) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        progress_callback: Optional callback(stage, message) for progress updates
        
    Returns:
        Extracted text content
        
    Raises:
        ImportError: If PyPDF2 is not installed
        FileNotFoundError: If PDF file doesn't exist
        Exception: For other PDF processing errors
    """
    if not PYPDF2_AVAILABLE:
        raise ImportError(
            "PyPDF2 is required for PDF processing. "
            "Install it with: pip install PyPDF2"
        )
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if progress_callback:
        progress_callback("pdf_extraction", f"Opening PDF: {os.path.basename(pdf_path)}")
    
    print(f"[PDFProcessor] Extracting text from: {pdf_path}")
    
    try:
        # Open PDF file
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"[PDFProcessor] PDF has {num_pages} pages")
            
            if progress_callback:
                progress_callback("pdf_extraction", f"Processing {num_pages} pages...")
            
            # Extract text from all pages
            text_content = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                if progress_callback:
                    progress_callback(
                        "pdf_extraction",
                        f"Extracting page {page_num + 1}/{num_pages}..."
                    )
                
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        # Add page marker for reference
                        text_content.append(f"[Page {page_num + 1}]\n{page_text}")
                except Exception as e:
                    print(f"[PDFProcessor] Warning: Failed to extract page {page_num + 1}: {e}")
                    continue
            
            # Combine all pages
            full_text = "\n\n".join(text_content)
            
            if not full_text or not full_text.strip():
                raise ValueError("No text content extracted from PDF. PDF might be image-based or empty.")
            
            print(f"[PDFProcessor] Extracted {len(full_text)} characters from {num_pages} pages")
            
            if progress_callback:
                progress_callback("pdf_extraction", f"Successfully extracted text from {num_pages} pages")
            
            return full_text
            
    except PyPDF2.errors.PdfReadError as e:
        raise Exception(f"Failed to read PDF file: {e}")
    except Exception as e:
        raise Exception(f"PDF processing error: {e}")


def is_pdf_file(file_path: str) -> bool:
    """
    Check if a file is a PDF based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is a PDF, False otherwise
    """
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
    
    # Check file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"PDF file too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)"
    
    return True, ""


def process_pdf_document(
    pdf_path: str,
    progress_callback: Optional[Callable[[str, str], None]] = None
) -> dict:
    """
    Process PDF document and return structured data.
    
    Args:
        pdf_path: Path to the PDF file
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary with:
            - text: Extracted text content
            - page_count: Number of pages
            - file_name: Original file name
            - char_count: Character count
    """
    # Validate PDF
    is_valid, error_msg = validate_pdf(pdf_path)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Extract text
    text = extract_text_from_pdf(pdf_path, progress_callback)
    
    # Get metadata
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        page_count = len(pdf_reader.pages)
    
    result = {
        "text": text,
        "page_count": page_count,
        "file_name": os.path.basename(pdf_path),
        "char_count": len(text)
    }
    
    print(f"[PDFProcessor] Processed PDF: {page_count} pages, {len(text)} characters")
    
    return result
