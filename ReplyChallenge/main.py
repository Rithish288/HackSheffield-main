import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Import your custom database functions
# (Preserving your specific import structure)
from ReplyChallenge.database.service import (
    log_chat_to_db,
    verify_database_connection,
    create_request_entry,
    update_request_response,
    get_session_history,
)

# Load env vars from ReplyChallenge/.env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

app = FastAPI()

# --- 1. NEW: Connection Manager for Multiplayer ---
class ConnectionManager:
    def __init__(self):
        # list of websocket connections and a mapping from websocket -> username
        self.active_connections: List[WebSocket] = []
        self.usernames: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            # remove username mapping for this websocket
            if websocket in self.usernames:
                del self.usernames[websocket]

    def set_username(self, websocket: WebSocket, username: str):
        if websocket in self.active_connections:
            self.usernames[websocket] = username

    def get_username(self, websocket: WebSocket) -> Optional[str]:
        return self.usernames.get(websocket)

    async def broadcast_json(self, obj: dict, exclude: Optional[WebSocket] = None):
        """Send a JSON-serializable object to all active connections as a JSON string.
        Optionally exclude a websocket (e.g., do not send typing presence back to origin).
        """
        import json
        payload = json.dumps(obj)
        for connection in self.active_connections:
            if exclude is not None and connection is exclude:
                continue
            try:
                await connection.send_text(payload)
            except Exception as e:
                print(f"Error broadcasting JSON to a client: {e}")

    async def broadcast(self, message: str):
        # Send the message to every open tab
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to a client: {e}")

# Initialize the manager
manager = ConnectionManager()
# --------------------------------------------------

# Initialize OpenAI client
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    client = OpenAI(api_key=api_key)
    print("✓ OpenAI client initialized")
except Exception as e:
    print(f"✗ OpenAI initialization failed: {e}")
    client = None

# Initialize thread pool for blocking DB operations
executor = ThreadPoolExecutor(max_workers=5)

# Enable CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return JSONResponse({
        "status": "running",
        "message": "ReplyChallenge API is live (Multiplayer Mode)",
        "endpoints": {
            "websocket": "ws://localhost:8000/ws",
            "health": "/health"
        }
    })

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "database": "connected",
        "openai": "initialized" if client else "not initialized",
        "active_users": len(manager.active_connections)
    })

@app.on_event("startup")
async def startup_event():
    """Verify database connection on startup"""
    print("\n" + "="*50)
    print("APPLICATION STARTUP (MULTIPLAYER MODE)")
    print("="*50)
    try:
        verify_database_connection()
    except Exception as e:
        print(f"⚠ Warning: Database verification failed on startup: {e}")
    print("="*50 + "\n")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 1. Connect user to the "Room" instead of just accepting
    await manager.connect(websocket)
    
    # 2. Hardcode Session ID for Shared History (Hackathon Logic)
    # Using a single ID means all users contribute to the same chat history
    session_id = "hackathon_public_room"
    
    print(f"\n🔗 New Multiplayer Connection. Total Users: {len(manager.active_connections)}")

    # Send session history to the newly connected client so they start with
    # the existing conversation state. We only send to this websocket.
    try:
        history = get_session_history(session_id)
        import json
        # Sort history by created_at if available
        history_sorted = sorted(history, key=lambda r: r.get("created_at") or "") if history else []
        for row in history_sorted:
            # send the user prompt first
            prompt = row.get("prompt")
            if prompt is not None:
                await websocket.send_text(json.dumps({"type": "message", "text": prompt, "username": row.get("username"), "request_id": row.get("id"), "created_at": row.get("created_at")}))
            # if we have an AI response, send that too referencing the same id
            response = row.get("response")
            if response is not None:
                await websocket.send_text(json.dumps({"type": "ai", "text": response, "request_id": row.get("id"), "created_at": row.get("updated_at") or row.get("created_at")}))
    except Exception as e:
        print(f"⚠ Failed to load session history for new connection: {e}")

    try:
        while True:
            # 3. Receive User Input
            data = await websocket.receive_text()
            print(f"📥 User Input: {data[:100]}...")

            # Try to parse structured JSON messages from clients. If JSON has a
            # 'type' field we treat it as a structured event (join, typing, etc.)
            import json
            parsed = None
            try:
                parsed = json.loads(data)
            except Exception:
                parsed = None

            # If this is a typing presence event, broadcast but DO NOT forward to AI
            if isinstance(parsed, dict) and parsed.get("type") == "typing":
                # ensure we have username & state
                username = parsed.get("username")
                is_typing = bool(parsed.get("isTyping"))
                # Update our server side mapping if a username is set on this ws
                if username:
                    manager.set_username(websocket, username)

                # Broadcast a structured typing presence event to other clients
                # exclude origin so the sender doesn't receive their own typing events
                await manager.broadcast_json({"type": "typing", "username": username, "isTyping": is_typing}, exclude=websocket)
                # never forward typing events to the AI
                continue

            # If this is a join event, register username and broadcast user.joined
            if isinstance(parsed, dict) and parsed.get("type") == "join":
                username = parsed.get("username")
                if username:
                    manager.set_username(websocket, username)
                    await manager.broadcast_json({"type": "user.joined", "username": username})
                continue

            # If parsed JSON looks like a real chat message (has 'text'), use it
            # else treat incoming raw strings as regular message text.

            # Decide whether this is a text message to process or something else
            # If the incoming payload is JSON with 'text' use it; otherwise treat
            # the raw `data` string as the message text.
            if isinstance(parsed, dict) and (parsed.get("text") or parsed.get("message")):
                message_text = str(parsed.get("text") or parsed.get("message") or "").strip()
                username = parsed.get("username") or manager.get_username(websocket) or "unknown"
            else:
                # treat raw string as a full message (e.g., plain text messages)
                message_text = str(data).strip()
                username = manager.get_username(websocket) or "unknown"

            # Create a DB entry for this user message so we can update it later
            # with the AI response. Insert in the DB before broadcasting so
            # other clients get a stable request_id to reference.
            db_row = None
            try:
                db_row = create_request_entry(prompt=message_text, session_id=session_id, username=username)
            except Exception as e:
                print(f"⚠ Failed to create DB entry for prompt: {e}")

            request_id = None
            if db_row and isinstance(db_row, dict):
                request_id = db_row.get("id")

            # Broadcast the message as a structured JSON event so frontends render it
            # as a chat bubble immediately and can link to the DB record. Do NOT
            # send the message back to the originating websockets (they already
            # have a local echo). This prevents duplicates appearing on the sender.
            await manager.broadcast_json({"type": "message", "text": message_text, "username": username, "request_id": request_id}, exclude=websocket)

            if not client:
                error_msg = "OpenAI client not initialized"
                print(f"✗ {error_msg}")
                await manager.broadcast_json({"type": "system", "text": error_msg})
                continue
            
            # Only call the AI if this message explicitly targets a persona
            # either via parsed 'targetPersona' or an @mention at the start.
            target_persona = None
            if isinstance(parsed, dict):
                target_persona = parsed.get("targetPersona")

            if not target_persona:
                # look for leading @persona syntax in the text (e.g. "@Athena hello")
                mention_match = None
                try:
                    import re

                    mention_match = re.match(r"^@([A-Za-z0-9_-]+)\s+(.+)$", message_text)
                except Exception:
                    mention_match = None

                if mention_match:
                    target_persona = mention_match.group(1)
                    # update message_text to be the content only when calling AI
                    message_text_for_ai = mention_match.group(2) or ""
                else:
                    message_text_for_ai = message_text
            else:
                message_text_for_ai = message_text

            # If no target persona is present, we do not call the AI.
            if not target_persona:
                print("ℹ️  No target persona detected — skipping OpenAI call for this message")
                continue

            try:
                # 5. Call OpenAI API
                print(f"🤖 Calling OpenAI API for persona: {target_persona}...")
                # NOTE: We keep the minimal call shape. You may want to inject
                # persona-specific system prompts or different models per persona.
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": message_text_for_ai}]
                )
                
                ai_text = completion.choices[0].message.content
                tokens = completion.usage.total_tokens
                full_metadata = completion.model_dump()
                
                print(f"✓ OpenAI Response received ({tokens} tokens)")

                # 6. Save to Supabase (Background Thread) — update the row we
                # created earlier with AI response and tokens, or fallback to
                # the legacy logger if we don't have a request_id.
                print(f"💾 Saving AI response to database...")
                loop = __import__('asyncio').get_event_loop()
                if request_id:
                    await loop.run_in_executor(
                        executor,
                        update_request_response,
                        request_id,
                        ai_text,
                        tokens,
                        full_metadata,
                    )
                else:
                    # fallback unless supabase is down — preserves previous behaviour
                    await loop.run_in_executor(
                        executor,
                        log_chat_to_db,
                        message_text,
                        ai_text,
                        tokens,
                        session_id,
                        full_metadata,
                    )

                # 7. BROADCAST AI RESPONSE (So everyone sees the answer)
                print(f"📤 Broadcasting response ({len(ai_text)} chars)")
                # Broadcast AI response and reference the original request_id where possible
                await manager.broadcast_json({"type": "ai", "text": ai_text, "request_id": request_id})

            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                print(f"✗ {error_msg}")
                await manager.broadcast_json({"type": "system", "text": error_msg})

    except WebSocketDisconnect:
        username = manager.get_username(websocket)
        manager.disconnect(websocket)
        # Broadcast user.left event so clients can update presence
        if username:
            await manager.broadcast_json({"type": "user.left", "username": username})
        print(f"🔌 Client disconnected. Remaining: {len(manager.active_connections)}")
    except Exception as e:
        print(f"✗ WebSocket Error: {e}")
        manager.disconnect(websocket)