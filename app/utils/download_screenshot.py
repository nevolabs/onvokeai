import asyncio
import concurrent.futures
import os

from app.config.logging import get_logger
# Initialize logger for this module
logger = get_logger(__name__)


async def download_screenshot(storage, full_path: str, temp_path: str, file_name: str) -> tuple:
    """Download a single screenshot file and return the result."""
    try:
        logger.debug(f"Downloading screenshot: {full_path}")
        # Use executor to run blocking operation in thread pool
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            response_content = await loop.run_in_executor(executor, storage.download, full_path)
        
        if not isinstance(response_content, bytes):
            logger.error(f"Failed download: {file_name}")
            return None
        
        with open(temp_path, "wb") as f: 
            f.write(response_content)
        
        logger.debug(f"Saved temp screenshot: {temp_path}")
        return (temp_path, file_name)
    except Exception as e:
        logger.error(f"Failed processing screenshot {file_name}: {str(e)}")
        if os.path.exists(temp_path):
            try: 
                os.remove(temp_path)
            except OSError: 
                pass
        return None