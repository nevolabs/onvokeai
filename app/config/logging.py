"""
Logging configuration using loguru with colored output and different log levels.
"""
import sys
from loguru import logger
from pathlib import Path

def setup_logging():
    """
    Configure loguru logger with colored output and multiple formats.
    """
    # Remove default logger
    logger.remove()
    
    # Add console logger with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
        enqueue=True
    )
    
    # Add file logger for all logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
        compression="zip",
        enqueue=True
    )
    
    # Add error file logger
    logger.add(
        log_dir / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        enqueue=True
    )
    
    return logger

# Initialize logger
def get_logger(name: str = None):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger

# Setup logging when module is imported
setup_logging()
