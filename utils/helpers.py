"""Utility helper functions for logging, validation, and error handling."""

import logging
import os
from typing import Optional
from datetime import datetime


def setup_logging(log_level: str, log_dir: str = "logs", log_file: str = "v3_bot.log"):
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        log_file: Name of log file
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, log_file)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path),
        ],
    )
    
    return logging.getLogger(__name__)


def validate_user_id(user_id: int) -> bool:
    """
    Validate Telegram user ID.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        bool: True if valid
    """
    return isinstance(user_id, int) and user_id > 0


def validate_group_id(group_id: int) -> bool:
    """
    Validate Telegram group ID.
    Telegram group IDs are negative.
    
    Args:
        group_id: Group ID to validate
        
    Returns:
        bool: True if valid
    """
    return isinstance(group_id, int) and group_id < 0


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime for display.
    
    Args:
        dt: Datetime to format
        
    Returns:
        str: Formatted timestamp
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_action_emoji(action_type: str) -> str:
    """
    Get emoji for action type.
    
    Args:
        action_type: Type of action
        
    Returns:
        str: Emoji for action
    """
    emojis = {
        "ban": "🚫",
        "unban": "✅",
        "kick": "👢",
        "warn": "⚠️",
        "mute": "🔇",
        "unmute": "🔊",
    }
    return emojis.get(action_type.lower(), "📋")
