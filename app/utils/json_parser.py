import os
from llama_cloud_services import LlamaParse
import json
from app.config.config import load_config, set_env
from app.config.logging import get_logger
from typing import List, Dict

# Initialize logger for this module
logger = get_logger(__name__)

# Load configuration
config = load_config()
set_env(config)


async def parse_json(file_path: str) -> str:
    """Load JSON file content as raw string without parsing"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading JSON file: {str(e)}")
        return ""