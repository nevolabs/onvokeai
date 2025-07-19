"""
PDF file validation utilities.
"""
import os
from PyPDF2 import PdfReader
from app.core.initializers import get_file_mime_type
from app.config.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


def validate_pdf_file(file_path: str) -> None:
    """
    Validate that a file is a proper PDF file.
    
    Args:
        file_path (str): Path to the PDF file to validate
        
    Raises:
        ValueError: If the PDF file is invalid, missing, or empty
    """
    if not os.path.exists(file_path):
        raise ValueError(f"PDF not found: {file_path}")
    
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"PDF empty: {file_path}")
    
    # Check MIME type
    try:
        detected_mime = get_file_mime_type(file_path)
        if detected_mime != "application/pdf":
            logger.warning(f"Unexpected MIME type for PDF: {detected_mime} (continuing anyway)")
    except Exception as e:
        logger.warning(f"PDF MIME check failed (continuing): {e}")
    
    # Validate PDF structure with PyPDF2
    try:
        reader = PdfReader(file_path)
        logger.info(f"PDF valid ({len(reader.pages)} pages)")
    except Exception as e:
        raise ValueError(f"Invalid PDF: {e}")
