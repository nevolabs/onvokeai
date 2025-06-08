import pypandoc
import tempfile
import os
from docx2pdf import convert
import io

def convert_to_pdf(markdown_text: str) -> bytes:
    """
    Convert Markdown text to PDF via DOCX intermediate format.
    
    Args:
        markdown_text: String containing Markdown content
        
    Returns:
        bytes: PDF file content as bytes
        
    Raises:
        RuntimeError: If any conversion step fails
    """
    temp_md_path = None
    temp_docx_path = None
    temp_pdf_path = None
    
    try:
        # Validate input
        if not markdown_text or not isinstance(markdown_text, str):
            raise ValueError("Invalid or empty Markdown text provided")

        # Step 1: Create temporary Markdown file
        with tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.md', encoding='utf-8'
        ) as temp_md:
            temp_md.write(markdown_text)
            temp_md_path = temp_md.name

        # Step 2: Convert Markdown to DOCX
        temp_docx_path = tempfile.mktemp(suffix='.docx')
        
        pypandoc.convert_file(
            temp_md_path,
            'docx',
            format='markdown',
            outputfile=temp_docx_path,
            extra_args=[
                '--wrap=auto',
            ]
        )

        # Step 3: Convert DOCX to PDF
        temp_pdf_path = tempfile.mktemp(suffix='.pdf')
        convert(temp_docx_path, temp_pdf_path)

        # Read the generated PDF
        with open(temp_pdf_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()

        return pdf_bytes

    except Exception as e:
        raise RuntimeError(f"PDF conversion failed: {str(e)}") from e
        
    finally:
        # Cleanup temporary files
        for path in [temp_md_path, temp_docx_path, temp_pdf_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass

