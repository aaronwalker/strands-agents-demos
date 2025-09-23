"""Logging configuration for the Orik system."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    include_timestamp: bool = True
) -> logging.Logger:
    """Set up logging configuration for the Orik system."""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    if include_timestamp:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        log_format = "%(name)s - %(levelname)s - %(message)s"
    
    # Set up root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )
    
    # Create main logger
    logger = logging.getLogger("orik")
    logger.info("Orik logging system initialized")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific component."""
    return logging.getLogger(f"orik.{name}")


class OrikLoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for Orik with additional context."""
    
    def __init__(self, logger: logging.Logger, extra: dict):
        super().__init__(logger, extra)
    
    def process(self, msg, kwargs):
        """Add extra context to log messages."""
        timestamp = datetime.now().isoformat()
        return f"[{timestamp}] {msg}", kwargs


def create_component_logger(component_name: str, **extra_context) -> OrikLoggerAdapter:
    """Create a logger adapter for a specific component with context."""
    base_logger = get_logger(component_name)
    return OrikLoggerAdapter(base_logger, extra_context)