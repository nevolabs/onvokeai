"""
File reading utilities for different file formats.
"""
import pandas as pd
import PyPDF2
from docx import Document
from io import BytesIO
from typing import Union
from app.config.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

def read_excel_file(file_content: bytes) -> str:
    """Read content from an Excel file."""
    try:
        excel_file = BytesIO(file_content)
        df = pd.read_excel(excel_file, engine='openpyxl')
        # Convert all sheets to text (simplified representation)
        return df.to_string()
    except Exception as e:
        logger.error(f"Failed to read Excel file: {str(e)}")
        return ""

def read_pdf_file(file_content: bytes) -> str:
    """Read content from a PDF file."""
    try:
        pdf_file = BytesIO(file_content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"Failed to read PDF file: {str(e)}")
        return ""

def read_docx_file(file_content: bytes) -> str:
    """Read content from a DOCX file."""
    try:
        docx_file = BytesIO(file_content)
        doc = Document(docx_file)
        text = "\n".join([para.text for para in doc.paragraphs if para.text])
        return text
    except Exception as e:
        logger.error(f"Failed to read DOCX file: {str(e)}")
        return ""

def read_text_file(file_content: bytes, encoding: str = 'utf-8') -> str:
    """Read content from a text file."""
    try:
        return file_content.decode(encoding, errors='ignore')
    except Exception as e:
        logger.error(f"Failed to read text file: {str(e)}")
        return ""

def read_file_by_extension(file_content: bytes, file_extension: str) -> str:
    """
    Read file content based on file extension.
    
    Args:
        file_content: Raw file content as bytes
        file_extension: File extension (e.g., '.pdf', '.docx', '.xlsx')
        
    Returns:
        Extracted text content from the file
    """
    file_extension = file_extension.lower()
    
    if file_extension in ['.xlsx', '.xls']:
        return read_excel_file(file_content)
    elif file_extension == '.pdf':
        return read_pdf_file(file_content)
    elif file_extension == '.docx':
        return read_docx_file(file_content)
    else:
        return read_text_file(file_content)
