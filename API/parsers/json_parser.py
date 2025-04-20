import os
from llama_cloud_services import LlamaParse
import json
from config.config import load_config, set_env
from typing import List, Dict
# Load configuration
config = load_config()
set_env(config)


async def parse_json(file_path: str) -> str:
    """Load JSON file content as raw string without parsing"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading JSON file: {str(e)}")
        return ""