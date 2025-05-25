import pypandoc
from io import BytesIO
import tempfile
import os
import sys

def convert_to_docx(markdown_text: str) -> bytes:
    try:
        # Verify Pandoc is installed
        if not pypandoc.get_pandoc_version():
            raise RuntimeError("Pandoc is not installed or not found in PATH.")

        # Validate input
        if not markdown_text or not isinstance(markdown_text, str):
            raise ValueError("Invalid or empty Markdown text provided.")

        # Create a temporary file for DOCX output
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_file:
            output_path = tmp_file.name

        # Convert Markdown to DOCX and save to temp file
        pypandoc.convert_text(
            markdown_text,
            "docx",
            format="md",
            outputfile=output_path
        )

        # Read the DOCX content
        with open(output_path, "rb") as f:
            docx_bytes = f.read()

        # Save a debug copy in the current working directory
        debug_path = os.path.join(os.getcwd(), "debug_output.docx")
        try:
            with open(debug_path, "wb") as debug_file:
                debug_file.write(docx_bytes)
            print(f"Debug DOCX saved at: {debug_path}")
        except Exception as e:
            print(f"Failed to save debug DOCX: {str(e)}")

        return docx_bytes

    except Exception as e:
        raise RuntimeError(f"Failed to convert Markdown to DOCX: {str(e)}") from e

    finally:
        # Clean up the temp file
        if "output_path" in locals() and os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except Exception as e:
                print(f"Failed to delete temp file {output_path}: {str(e)}")