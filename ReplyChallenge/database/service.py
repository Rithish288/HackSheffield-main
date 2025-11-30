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


def add_memory(content: str, embedding: list, user_id: str | None = None):
    """Insert a memory row into the memory table with a vector embedding.
    embedding should be a list of floats matching the DB vector dimension (1536).
    Returns the inserted row or None.
    """
    if supabase is None:
        print(f"⚠️  Database not connected. Skipping memory insert: {content[:50]}...")
        return None

    try:
        payload = {
            "user_id": user_id,
            "content": content,
            "embedding": embedding,
        }
        result = supabase.table("memory").insert(payload).execute()
        if hasattr(result, "data") and result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"✗ Database Error inserting memory: {e}")
        raise


def find_similar_memories(query_embedding: list, match_count: int = 5):
    """Call the database RPC `match_memory` function to find similar memory rows.
    Returns a list of rows with fields (id, user_id, content, similarity).
    """
    if supabase is None:
        print("⚠️  Database not connected. Skipping memory search")
        return []


def add_fact(user_id: str | None, username: str | None, request_id: str | None, fact_type: str, value: str, normalized_value: str | None = None, confidence: float | None = None, metadata: dict | None = None):
    """Insert a structured fact (e.g. birthday) into `facts` table.
    Returns inserted row or None.
    """
    if supabase is None:
        print(f"⚠️  Database not connected. Skipping fact insert: {fact_type}={value}")
        return None

    try:
        payload = {
            "user_id": user_id,
            "username": username,
            "request_id": request_id,
            "fact_type": fact_type,
            "value": value,
            "normalized_value": normalized_value,
            "confidence": confidence,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = supabase.table("facts").insert(payload).execute()
        if hasattr(result, "data") and result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"✗ Database Error inserting fact: {e}")
        raise


def get_facts_for_user(user_id: str | None = None, username: str | None = None):
    """Retrieve facts for a user either by user_id or username (or both)."""
    if supabase is None:
        print("⚠️  Database not connected. Skipping facts lookup")
        return []

    try:
        q = supabase.table("facts").select("*")
        if user_id:
            q = q.eq("user_id", user_id)
        if username:
            q = q.eq("username", username)
        # only return active facts by default
        q = q.eq("active", True)
        result = q.execute()
        if hasattr(result, "data") and result.data:
            return result.data
        return []
    except Exception as e:
        # If the table doesn't exist, supabase/pgrst returns a specific code
        # (PGRST205). Instead of crashing the server we log and return an empty
        # list so frontends can handle it gracefully. The UI can surface a
        # friendly message explaining the table needs creating.
        err_text = str(e)
        print(f"✗ Database Error fetching facts: {err_text}")
        # Return empty list on missing table or schema issues so UI doesn't explode
        if "Could not find the table" in err_text or "PGRST205" in err_text:
            return []
        # otherwise re-raise for unexpected errors so they surface during dev
        raise


def upsert_fact(user_id: str | None, username: str | None, request_id: str | None, fact_type: str, value: str, normalized_value: str | None = None, confidence: float | None = None, metadata: dict | None = None):
    """Insert or update a fact for a user. For MVP we dedupe by (user_id or username) + fact_type."""
    if supabase is None:
        print("⚠️  Database not connected. Skipping upsert for fact")
        return None

    try:
        # prefer user_id for dedupe else username
        if user_id:
            existing = supabase.table("facts").select("*").eq("user_id", user_id).eq("fact_type", fact_type).execute()
        elif username:
            existing = supabase.table("facts").select("*").eq("username", username).eq("fact_type", fact_type).execute()
        else:
            existing = None

        if existing and hasattr(existing, "data") and existing.data:
            # update the first matching fact
            row_id = existing.data[0].get("id")
            payload = {
                "value": value,
                "normalized_value": normalized_value,
                "confidence": confidence,
                "metadata": (metadata or {}),
                "updated_at": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "active": True,
            }
            return supabase.table("facts").update(payload).eq("id", row_id).execute()

        # no existing row -> insert
        return add_fact(user_id, username, request_id, fact_type, value, normalized_value, confidence, metadata)
    except Exception as e:
        print(f"✗ Database Error upserting fact: {e}")
        raise


def delete_fact(fact_id: str):
    """Soft-delete a fact (set active=false)."""
    if supabase is None:
        print(f"⚠️  Database not connected. Skipping delete for fact {fact_id}")
        return None

    try:
        payload = {"active": False, "updated_at": datetime.utcnow().isoformat()}
        result = supabase.table("facts").update(payload).eq("id", fact_id).execute()
        return result
    except Exception as e:
        print(f"✗ Database Error deleting fact {fact_id}: {e}")
        raise


def update_fact(fact_id: str, updates: dict):
    """Update arbitrary fields on a fact row (safe for metadata/values)."""
    if supabase is None:
        print(f"⚠️  Database not connected. Skipping update for fact {fact_id}")
        return None

    try:
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = supabase.table("facts").update(updates).eq("id", fact_id).execute()
        return result
    except Exception as e:
        print(f"✗ Database Error updating fact {fact_id}: {e}")
        raise