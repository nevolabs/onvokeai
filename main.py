"""
Main entry point for the SOP Generation application.
"""
import uvicorn
from app.core.app import create_app
from app.config.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app at module level for uvicorn
app = create_app()

def main():
    """
    Main entry point for the application.
    """
    logger.info("Starting SOP Generation API...")
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        workers=1,  # Set to 1 for development with reload
        log_level="info"
    )

if __name__ == "__main__":
    main()
