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
