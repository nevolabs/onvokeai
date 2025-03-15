import os
from llama_cloud_services import LlamaParse
import json
from config import load_config, set_env

# Load configuration
config = load_config()
set_env(config)

# Initialize parser
parser = LlamaParse(result_type="markdown")

async def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using LlamaParse asynchronously."""
    try:
        # Use LlamaParse's async method directly instead of SimpleDirectoryReader
        documents = await parser.aload_data(file_path)
        return documents[0].text if documents else "No text extracted from PDF."
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

async def parse_json(file_path: str) -> dict:
    """Load event JSON data from a file asynchronously."""
    try:
        # Since file I/O is synchronous, we can wrap it in an async context if needed
        # For simplicity, keeping it sync here as it's lightweight
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Error loading JSON: {str(e)}"}