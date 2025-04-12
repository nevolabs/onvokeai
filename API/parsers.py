import os
from llama_cloud_services import LlamaParse
import json
from config import load_config, set_env
from typing import List, Dict
# Load configuration
config = load_config()
set_env(config)

import os
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv
from config import load_config, set_env

# Load configuration
config = load_config()
set_env(config)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

async def parse_pdf(file_path: str) -> str:
    return " "
    
    

async def parse_json(file_path: str) -> str:
    """Load JSON file content as raw string without parsing"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading JSON file: {str(e)}")
        return ""