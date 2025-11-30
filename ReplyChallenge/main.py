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
    add_memory,
    find_similar_memories,
    get_session_history,
    add_fact,
    get_facts_for_user,
    upsert_fact,
    delete_fact,
    update_fact,
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


@app.get("/api/facts")
async def api_get_facts(username: Optional[str] = None, user_id: Optional[str] = None):
    """Return facts for a user either by username or user_id."""
    try:
        facts = get_facts_for_user(user_id, username)
        # If the backend returns an empty list it might mean either no facts
        # exist or the database/table isn't present. To help operators, return
        # a friendly payload and let the UI decide how to present it.
        if isinstance(facts, list) and len(facts) == 0:
            return JSONResponse({"ok": True, "data": [], "note": "no facts found or facts table missing"})
        return JSONResponse({"ok": True, "data": facts})
    except Exception as e:
        # Unexpected errors should be reported but keep the response JSON
        # friendly rather than returning raw DB exceptions.
        return JSONResponse({"ok": False, "error": "Internal server error fetching facts"}, status_code=500)


@app.delete("/api/facts/{fact_id}")
async def api_delete_fact(fact_id: str):
    try:
        result = delete_fact(fact_id)
        return JSONResponse({"ok": True, "result": getattr(result, 'data', None)})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.patch("/api/facts/{fact_id}")
async def api_update_fact(fact_id: str, payload: dict):
    try:
        result = update_fact(fact_id, payload)
        return JSONResponse({"ok": True, "result": getattr(result, 'data', None)})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

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

    try:
        # helper: lightweight regex-based fact extraction (MVP)
        def parse_date_string(s: str):
            from datetime import datetime
            s = s.strip()
            # common formats to try
            fmts = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%B %d, %Y",
                "%b %d, %Y",
                "%d %B %Y",
                "%d %b %Y",
                "%B %d",
                "%b %d",
            ]
            for f in fmts:
                try:
                    dt = datetime.strptime(s, f)
                    # if format didn't include year (e.g. '%B %d') we leave year as-is
                    return dt.date().isoformat()
                except Exception:
                    continue
            return None

        def extract_facts_from_text(text: str):
            import re
            candidates = []

            # basic birthday patterns
            # examples: "my birthday is July 29, 1993", "I was born on 29/07/1993"
            patterns = [
                r"(?:my )?birthday is (?:on )?([A-Za-z0-9,\-\s]+)",
                r"(?:i was )?born on ([A-Za-z0-9,\-/\s]+)",
                r"birthday: (\d{4}-\d{2}-\d{2})",
                r"born (?:on )?([A-Za-z0-9,\-/\s]+)",
            ]

            for p in patterns:
                m = re.search(p, text, re.I)
                if m:
                    raw = m.group(1).strip()
                    norm = parse_date_string(raw)
                    candidates.append({
                        "type": "birthday",
                        "value": raw,
                        "normalized": norm,
                        "confidence": 0.95,  # regex-derived high precision
                        "source": "regex",
                    })

            # Additional simple facts (name/intro) — e.g. "I'm Alice" or "I am Alice"
            m = re.search(r"^i(?:'| )?m\s+([A-Z][a-zA-Z\-']+)", text, re.I)
            if m:
                name = m.group(1)
                candidates.append({
                    "type": "name",
                    "value": name,
                    "normalized": name,
                    "confidence": 0.8,
                    "source": "regex",
                })

            return candidates

        def is_explicit_save(text: str) -> bool:
            """Detect explicit user intent to save/remember info.
            Match phrases like 'remember that', 'please remember', 'save my', 'don't forget'.
            """
            import re
            checks = [
                r"\bremember that\b",
                r"\bplease remember\b",
                r"\bsave my\b",
                r"\bdon't forget\b",
                r"\bdo not forget\b",
                r"\bremember my\b",
                r"\bstore my\b",
                r"\bcan you remember\b",
            ]
            t = text.lower()
            for c in checks:
                if re.search(c, t):
                    return True
            return False

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
                # do not echo typing events back to the origin websocket
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

            # Create DB entry for the user message (requests table). This
            # returns a request_id we can use to update later when the AI reply
            # arrives and also to link the message to stored records.
            request_row = None
            try:
                request_row = create_request_entry(prompt=message_text, session_id=session_id, username=username)
            except Exception as e:
                print(f"⚠ Failed to create request entry: {e}")

            request_id = request_row.get("id") if request_row and isinstance(request_row, dict) else None

            # run a lightweight extractor for structured facts (MVP) and persist
            try:
                extracted = extract_facts_from_text(message_text)
                explicit_save = is_explicit_save(message_text)
                for f in extracted:
                    # only persist structured facts if the user explicitly asked us
                    # to remember/save them (privacy-first behaviour)
                    if explicit_save:
                        try:
                            upsert_fact(None, username, request_id, f["type"], f["value"], f.get("normalized"), f.get("confidence"), {"source": f.get("source")})
                            print(f"✓ Explicitly saved fact {f['type']}={f['value']} for {username}")
                            # Confirm to the origin that we saved the fact
                            try:
                                await websocket.send_text(json.dumps({"type": "system", "text": f"Saved: {f['type']} = {f['value']}"}))
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"⚠ Failed to persist fact: {e}")
                    else:
                        # If not explicit, we only extract candidates but do not
                        # persist them as stored user facts (MVP privacy choice).
                        print(f"ℹ️ Detected candidate fact but not saving (no explicit save): {f['type']}={f['value']}")
            except Exception as e:
                print(f"⚠ Fact extraction failed: {e}")

            # Broadcast the message as a structured JSON event so frontends render it
            # as a chat bubble immediately. Do not send back to the origin (the
            # sender already has a local echo).
            await manager.broadcast_json({"type": "message", "text": message_text, "username": username, "request_id": request_id}, exclude=websocket)

            if not client:
                error_msg = "OpenAI client not initialized"
                print(f"✗ {error_msg}")
                await manager.broadcast_json({"type": "system", "text": error_msg})
                continue
            
            try:
                # Determine if this message should reach an AI persona. We only
                # call the AI when the message explicitly targets a persona via
                # parsed.targetPersona or a leading @mention. This avoids sending
                # unrelated chat to OpenAI.
                target_persona = None
                if isinstance(parsed, dict):
                    target_persona = parsed.get("targetPersona")

                message_text_for_ai = message_text
                if not target_persona:
                    # look for leading @persona syntax
                    try:
                        import re

                        m = re.match(r"^@([A-Za-z0-9_-]+)\s+(.+)$", message_text)
                        if m:
                            target_persona = m.group(1)
                            message_text_for_ai = m.group(2) or ""
                    except Exception:
                        m = None

                if not target_persona:
                    print("ℹ️  No target persona detected — skipping OpenAI call for this message")
                    # We'll still optionally persist the user's message to memory,
                    # but we won't call the OpenAI API.
                    # Persist a memory embedding for this message (best effort)
                    try:
                        if client and message_text_for_ai:
                            emb = client.embeddings.create(model="text-embedding-3-small", input=message_text_for_ai)
                            embedding_vector = emb.data[0].embedding if hasattr(emb.data[0], 'embedding') else emb.data[0]['embedding']
                            # don't block: run in executor
                            loop = __import__('asyncio').get_event_loop()
                            loop.run_in_executor(executor, add_memory, message_text_for_ai, embedding_vector, None)
                    except Exception as e:
                        print(f"⚠️ Memory embedding failed: {e}")
                    continue

                # 5. Before calling the AI, compute an embedding of the query and
                # search the memory table for similar items to provide context.
                memories = []
                embedding_vector = None
                try:
                    emb = client.embeddings.create(model="text-embedding-3-small", input=message_text_for_ai)
                    embedding_vector = emb.data[0].embedding if hasattr(emb.data[0], 'embedding') else emb.data[0]['embedding']
                    # find similar memories (best effort)
                    memories = find_similar_memories(embedding_vector, match_count=5)
                except Exception as e:
                    print(f"⚠️ Warning computing/querying embeddings: {e}")

                # Construct a system prompt block containing the relevant memories
                memory_context = ""
                if memories:
                    memory_lines = []
                    for m in memories:
                        similarity = m.get("similarity")
                        content = m.get("content")
                        memory_lines.append(f"- ({similarity:.3f}) {content}")
                    memory_context = "Relevant memories:\n" + "\n".join(memory_lines)

                # also include structured facts (birthdays, name, etc.) if present
                try:
                    facts = get_facts_for_user(None, username)
                except Exception:
                    facts = []

                fact_context = ""
                if facts:
                    fact_lines = []
                    for f in facts:
                        ft = f.get("fact_type")
                        val = f.get("value")
                        norm = f.get("normalized_value")
                        fact_lines.append(f"- {ft}: {val}" + (f" (normalized: {norm})" if norm else ""))
                    fact_context = "Known facts about the user:\n" + "\n".join(fact_lines)

                # 6. Call OpenAI API with memory context included as a system message
                print(f"🤖 Calling OpenAI API for persona: {target_persona}...")
                messages_for_ai = []
                # prefer to place structured facts first so the AI can act on them
                if fact_context:
                    messages_for_ai.append({"role": "system", "content": fact_context})
                if memory_context:
                    messages_for_ai.append({"role": "system", "content": memory_context})
                messages_for_ai.append({"role": "user", "content": message_text_for_ai})

                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages_for_ai
                )
                
                ai_text = completion.choices[0].message.content
                tokens = completion.usage.total_tokens
                full_metadata = completion.model_dump()
                
                print(f"✓ OpenAI Response received ({tokens} tokens)")

                # 6. Save response to DB and persist memory for the user's message
                print(f"💾 Saving AI response to database and storing memory...")
                loop = __import__('asyncio').get_event_loop()

                # Update the requests row that we created earlier with the AI response
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
                    # fallback to legacy logger
                    await loop.run_in_executor(
                        executor,
                        log_chat_to_db,
                        message_text,
                        ai_text,
                        tokens,
                        session_id,
                        full_metadata,
                    )

                # Persist the user's message as a memory vector for future recall
                try:
                    if embedding_vector:
                        await loop.run_in_executor(executor, add_memory, message_text_for_ai, embedding_vector, None)
                except Exception as e:
                    print(f"⚠️ Failed to persist memory: {e}")

                # 7. BROADCAST AI RESPONSE (So everyone sees the answer)
                print(f"📤 Broadcasting response ({len(ai_text)} chars)")
                await manager.broadcast_json({"type": "ai", "text": ai_text, "request_id": request_id, "username": target_persona})

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