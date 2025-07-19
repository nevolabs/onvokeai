import pypandoc
import tempfile
import os
from app.config.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

def convert_to_docx(markdown_text: str) -> bytes:
    temp_md_path = None
    temp_docx_path = None
    try:
        # Validate input
        if not markdown_text or not isinstance(markdown_text, str):
            raise ValueError("Invalid or empty Markdown text provided.")

        # Create temporary Markdown file
        with tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.md', encoding='utf-8'
        ) as temp_md:
            temp_md.write(markdown_text)
            temp_md_path = temp_md.name

        # Generate temporary DOCX path
        temp_docx_path = tempfile.mktemp(suffix='.docx')

        # Convert Markdown to DOCX using Pandoc
        pypandoc.convert_file(
            temp_md_path,
            'docx',
            format='markdown',
            outputfile=temp_docx_path,
            extra_args=['--wrap=auto']
        )

        # Read the generated DOCX content
        with open(temp_docx_path, 'rb') as docx_file:
            docx_bytes = docx_file.read()
        
        # Save a debug copy in the current working directory
        debug_path = os.path.join(os.getcwd(), "debug_output.docx")
        try:
            with open(debug_path, "wb") as debug_file:
                debug_file.write(docx_bytes)  # Use the bytes we already read
            logger.debug(f"Debug DOCX saved at: {debug_path}")
        except Exception as e:
            logger.warning(f"Failed to save debug DOCX: {str(e)}")

        return docx_bytes

    except FileNotFoundError as fnf_error:
        if 'pandoc' in str(fnf_error).lower():
            raise RuntimeError(
                "Pandoc not found. Please install Pandoc and ensure it's in your PATH."
            ) from fnf_error
        raise RuntimeError(f"File not found error: {fnf_error}") from fnf_error
    except Exception as e:
        raise RuntimeError(f"DOCX conversion failed: {str(e)}") from e
    finally:
        # Cleanup temporary files
        for path in [temp_md_path, temp_docx_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up {path}: {cleanup_error}")