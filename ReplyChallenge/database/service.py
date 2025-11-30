import json
from datetime import datetime
from .client import supabase

def log_chat_to_db(user_prompt: str, ai_response: str, tokens: int, session_id: str, metadata: dict, username: str = "WebUser", user_id: str | None = None):
    """
    Saves the chat interaction to Supabase.
    
    Table 'requests' should have columns:
    - id (uuid, primary key)
    - session_id (text)
    - prompt (text)
    - response (text)
    - tokens_used (integer)
    - metadata (jsonb)
    - username (text)
    - user_id (text, nullable)
    - created_at (timestamp)
    """
    if supabase is None:
        print(f"⚠️  Database not connected. Set SUPABASE_URL and SUPABASE_KEY in .env file")
        print(f"   Message would have been saved: {user_prompt[:50]}...")
        return None
    
    try:
        data_payload = {
            "prompt": user_prompt,
            "response": ai_response,
            "tokens_used": tokens,
            "session_id": session_id,
            "metadata": metadata,
            "username": username,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }

        # Execute the insert
        result = supabase.table("requests").insert(data_payload).execute()
        print(f"✓ Logged to Supabase (Session: {session_id})")
        return result
        
    except Exception as e:
        print(f"✗ Database Error: {e}")
        raise


def get_session_history(session_id: str):
    """
    Retrieves all chat messages for a specific session.
    """
    if supabase is None:
        print(f"⚠️  Database not connected. Set SUPABASE_URL and SUPABASE_KEY in .env file")
        return []
    
    try:
        result = supabase.table("requests").select("*").eq("session_id", session_id).execute()
        print(f"✓ Retrieved {len(result.data)} messages from session {session_id}")
        return result.data
    except Exception as e:
        print(f"✗ Database Error retrieving history: {e}")
        raise


def create_request_entry(prompt: str, session_id: str, username: str | None = None, user_id: str | None = None, metadata: dict | None = None):
    """Insert a new row into the requests table for an incoming user message.
    Returns the inserted row (or None if DB unavailable).
    """
    if supabase is None:
        print(f"⚠️  Database not connected. Skipping insert: {prompt[:50]}...")
        return None

    try:
        payload = {
            "prompt": prompt,
            "response": None,
            "tokens_used": None,
            "session_id": session_id,
            "metadata": metadata or {},
            "username": username or "WebUser",
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        result = supabase.table("requests").insert(payload).execute()
        if hasattr(result, 'data') and result.data:
            # return the first inserted row (supabase returns a list)
            return result.data[0]
        return None
    except Exception as e:
        print(f"✗ Database Error inserting request: {e}")
        raise


def update_request_response(request_id: str, ai_response: str | None, tokens: int | None = None, metadata: dict | None = None):
    """Update an existing request row with AI response, tokens used and metadata."""
    if supabase is None:
        print(f"⚠️  Database not connected. Skipping update for id={request_id}")
        return None

    try:
        payload = {
            "response": ai_response,
            "tokens_used": tokens,
            "metadata": metadata or {},
            "updated_at": datetime.utcnow().isoformat()
        }
        result = supabase.table("requests").update(payload).eq("id", request_id).execute()
        return result
    except Exception as e:
        print(f"✗ Database Error updating request {request_id}: {e}")
        raise


def verify_database_connection():
    """
    Test if Supabase connection is working.
    """
    if supabase is None:
        print(f"⚠️  Database not connected. Set SUPABASE_URL and SUPABASE_KEY in .env file")
        return False
    
    try:
        result = supabase.table("requests").select("count", count="exact").execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        print(f"✓ Database connection verified. Total requests: {count}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False