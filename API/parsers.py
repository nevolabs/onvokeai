import os
from llama_cloud_services import LlamaParse
import json
from config import load_config, set_env
from typing import List, Dict
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
        return documents[0].text
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"
    
    

async def parse_json(file_path: str) -> str:
    """Load JSON file content as raw string without parsing"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading JSON file: {str(e)}")
        return ""