import pypandoc
from io import BytesIO

def convert_to_pdf(markdown_text: str):
    try:
        # Convert directly to PDF bytes
        pdf_bytes = pypandoc.convert_text(
            markdown_text,
            "pdf",
            format="md",
            outputfile="output.pdf",  # Not actually saved (see below)
        )
        #for debugging purposes, we can  store the output to a file
   
        
        return pdf_bytes
    except Exception as e:
        raise RuntimeError(f"Failed to convert Markdown to PDF: {str(e)}")