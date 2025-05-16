import json
import logging
from typing import Dict, Any

def configure_logger(name, level=logging.INFO):
    """
    Configure a logger with the specified name and level.
    
    Args:
        name: Name for the logger.
        level: Logging level.
        
    Returns:
        Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler with a specific format
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def sanitize_metadata_for_chroma(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata to ensure it's compatible with Chroma.
    
    Chroma requires metadata values to be either:
    - str
    - int
    - float
    - bool
    
    Args:
        metadata: The metadata dictionary to sanitize.
        
    Returns:
        Sanitized metadata dictionary.
    """
    if not metadata:
        return {}
        
    sanitized = {}
    
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, (list, dict, tuple, set)):
            # Convert complex types to JSON strings
            try:
                sanitized[key] = json.dumps(value)
            except (TypeError, OverflowError):
                sanitized[key] = str(value)
        elif value is None:
            # Skip None values or convert them to empty strings
            sanitized[key] = ""
        else:
            # Convert anything else to string
            sanitized[key] = str(value)
    
    return sanitized

def log_with_truncation(logger, level, message, max_length=1000):
    """
    Log a potentially long message with truncation.
    
    Args:
        logger: The logger to use.
        level: Logging level.
        message: Message to log.
        max_length: Maximum length before truncation.
    """
    if len(message) > max_length:
        truncated_message = message[:max_length] + "... [truncated]"
    else:
        truncated_message = message
        
    if level == 'debug':
        logger.debug(truncated_message)
    elif level == 'info':
        logger.info(truncated_message)
    elif level == 'warning':
        logger.warning(truncated_message)
    elif level == 'error':
        logger.error(truncated_message)
    elif level == 'critical':
        logger.critical(truncated_message)
    else:
        logger.info(truncated_message)