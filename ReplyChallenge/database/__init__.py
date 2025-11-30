"""
ReplyChallenge Database Module
Handles all interactions with Supabase
"""

from .service import (
    log_chat_to_db,
    get_session_history,
    verify_database_connection
)

__all__ = [
    "log_chat_to_db",
    "get_session_history", 
    "verify_database_connection"
]
