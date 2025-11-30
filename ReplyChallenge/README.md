# ReplyChallenge — environment notes

This service expects an OpenAI API key to use the OpenAI client.

How to set it up locally

1. Create a `.env` file in the `ReplyChallenge` folder (or at repository root) with the following contents:

```
OPENAI_API_KEY=your_openai_api_key_here
```

2. If you prefer not to use a `.env` file, you can set a system environment variable instead:

macOS / zsh:

```
export OPENAI_API_KEY=your_openai_api_key_here
```

Notes
- The application will start even when `OPENAI_API_KEY` is missing, but any request that needs OpenAI will return a helpful error message.
- Use the provided `.env.example` as a template.

Behaviour notes
- The frontend may send typing updates for every keystroke (structured as `{ type: 'typing', username, isTyping }`). These typing events are handled by the server and broadcast as presence updates to other clients — they are NOT forwarded to OpenAI or saved to the database.

Persistence & history
- All incoming user messages are inserted into Supabase `requests` table immediately when received and updated with the AI response once available. This enables new clients to fetch the session history on connect and display the full chat history in real time.

Vector memory integration
- The server now computes embeddings for user messages (when AI is invoked) using OpenAI embeddings and stores them into a `memory` table (vector dimension 1536). When a message targets a persona (e.g. `@Athena do something`) the server will query similar memories using the `match_memory` RPC and include relevant memory content as context to the AI call — enabling AI agents to retain and recall past user information.

Structured facts extraction (MVP)
- A lightweight extractor scans incoming user messages for high-precision structured facts (initially birthdays and simple self-introductions like "I'm Alice").
- Extracted facts are stored in a new `facts` table (see `supabase_setup.sql`). These facts are included as a short system prompt when calling persona agents so the AI can reference them (e.g., wish the user happy birthday).
- This is a conservative, opt-in implementation intended for high-confidence facts only (regex-based first pass). Future work: LLM-powered extraction + user consent UI.

Explicit save + facts management
- Users may explicitly ask the assistant to remember something (phrases like "remember that", "please remember", "save my ...", "don't forget"). When an explicit save phrase is detected the server will persist the extracted fact and send a confirmation message back to the originating client ("Saved: birthday = 1997-11-11").
- A small REST API is exposed (`GET /api/facts?username=...`, `DELETE /api/facts/{id}`, `PATCH /api/facts/{id}`) so the frontend can present a simple UI to view and delete stored facts.

Notes
- Memory rows are inserted for targeted messages and are matched by cosine similarity via the `match_memory` function you created in SQL. Adjust the environment variables and embedding model if you prefer different sizing or models.
