import { useState, useEffect, useRef } from "react";

export function useWebSocket(
  currentUser: string,
  persona: string | null = null,
  onConnectionFailed?: () => void
) {
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [messages, setMessages] = useState<any[]>([]);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const [connectedUsers, setConnectedUsers] = useState<Set<string>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);
  const nextId = useRef(1);
  const reconnectAttempts = useRef(0);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const rawUrl = "wss://unperishable-autogenous-jaycob.ngrok-free.dev/ws";

    const ws = new WebSocket(rawUrl);

    // Set a timeout to fail fast if server doesn't respond
    const connectionTimeout = setTimeout(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        console.error("Connection timeout - server may be down");
        ws.close();

        // Immediately kick out on first failure
        if (onConnectionFailed) {
          onConnectionFailed();
        }
      }
    }, 2000); // 2 second timeout for immediate feedback

    ws.addEventListener("open", () => clearTimeout(connectionTimeout));

    ws.onopen = () => {
      console.log("WebSocket connected successfully");
      setConnectionStatus("connected");
      reconnectAttempts.current = 0; // Reset on successful connection

      // Add self to connected users
      setConnectedUsers((prev) => {
        const copy = new Set(prev);
        copy.add(currentUser);
        return copy;
      });
      // announce join to the server so it can track connected users
      try {
        if (currentUser)
          ws.send(JSON.stringify({ type: "join", username: currentUser }));
      } catch (err) {
        console.error("Failed to send join event", err);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnectionStatus("error");

      // Immediately return to login on any error
      if (onConnectionFailed) {
        onConnectionFailed();
      }
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
      setConnectionStatus("disconnected");
      setConnectedUsers(new Set());

      // If connection was never established or closed abnormally, immediately kick out
      if (!event.wasClean) {
        console.error(
          "Connection failed. Server may be down. Returning to login."
        );
        if (onConnectionFailed) {
          onConnectionFailed();
        }
      }
    };

    ws.onmessage = (event) => {
      // Parse incoming data (may be JSON with metadata or plain text)
      let raw = typeof event.data === "string" ? event.data : "";
      let parsedMsg: any = null;
      try {
        parsedMsg = JSON.parse(raw);
      } catch (e) {
        parsedMsg = null;
      }

      // Handle user join/leave events
      if (parsedMsg && parsedMsg.type === "user.joined") {
        const username = parsedMsg.username;
        setConnectedUsers((prev) => {
          const copy = new Set(prev);
          copy.add(username);
          return copy;
        });
        return;
      }

      if (parsedMsg && parsedMsg.type === "user.left") {
        const username = parsedMsg.username;
        setConnectedUsers((prev) => {
          const copy = new Set(prev);
          copy.delete(username);
          return copy;
        });
        return;
      }

      // Handle typing presence quickly
      if (parsedMsg && parsedMsg.type === "typing") {
        const username = parsedMsg.username;
        const isTyping = !!parsedMsg.isTyping;
        setTypingUsers((prev) => {
          const copy = new Set(prev);
          if (isTyping) copy.add(username);
          else copy.delete(username);
          return copy;
        });
        return;
      }

      // Determine message payload fields
      let messageText = "";
      let messageSender: string | null = null;
      let messageUsername: string | null = null;
      let messageType = "server";

      if (parsedMsg && typeof parsedMsg === "object") {
        messageType = parsedMsg.type || "server";
        if (messageType === "message") {
          messageText = String(parsedMsg.text || parsedMsg.message || "");
          // If the message's username matches our currentUser, mark the
          // incoming message as 'me' so UI places it on the right side; the
          // server should already avoid echoing messages back to the origin
          // but history or other flows may still send it.
          const incomingUsername = parsedMsg.username || "unknown";
          messageSender = incomingUsername === currentUser ? "me" : incomingUsername;
          messageUsername = incomingUsername;
          // preserve any request id or created_at metadata for later use
          // (frontend components can use these fields if desired)
          parsedMsg.request_id && (parsedMsg.request_id = parsedMsg.request_id);
          parsedMsg.created_at && (parsedMsg.created_at = parsedMsg.created_at);
        } else if (messageType === "ai") {
          messageText = String(parsedMsg.text || "");
          messageSender = "ai";
          messageUsername = null;
        } else if (messageType === "system") {
          messageText = String(parsedMsg.text || "");
          messageSender = "server";
          messageUsername = null;
        } else {
          // fallback for other structured messages
          messageText = String(parsedMsg.text || parsedMsg.message || raw);
          messageSender = parsedMsg.username || "server";
          messageUsername = parsedMsg.username || null;
        }
      } else {
        // non-json fallback
        messageText = raw;
        messageSender = "server";
        messageUsername = null;
      }

      // Prefer to replace the most recent loading indicator instead of appending
      setMessages((prev) => {
        // find last index of a loading message
        let idx = -1;
        for (let i = prev.length - 1; i >= 0; --i) {
          if (prev[i] && prev[i].loading) {
            idx = i;
            break;
          }
        }

        if (idx >= 0) {
          const copy = prev.slice();
          copy[idx] = { ...copy[idx], text: messageText, loading: false };
          return copy;
        }

        // no loading placeholder found — append as a new message
        return [
          ...prev,
          {
            id: nextId.current++,
            sender: messageSender,
            text: messageText,
            username: messageUsername,
            request_id: parsedMsg?.request_id,
            created_at: parsedMsg?.created_at,
          },
        ];
      });
    };

    wsRef.current = ws;
  };

  const sendMessage = (rawText: string) => {
    const text = String(rawText || "").trim();
    if (!text) return;

    const mentionMatch = text.match(/^@([A-Za-z0-9_-]+)\s+(.+)$/);

    if (mentionMatch) {
      const targetPersona = mentionMatch[1];
      const content = mentionMatch[2] || "";

      // local echo with target info
      setMessages((prev) => [
        ...prev,
        {
          id: nextId.current++,
          text: content || `(calling ${targetPersona})`,
          sender: "me",
          username: currentUser,
          targetPersona,
        },
        { id: nextId.current++, text: "...", sender: "server", loading: true },
      ]);

      const payload = {
        text: content || "",
        username: currentUser,
        persona,
        targetPersona,
      };

      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error(
          "WebSocket not connected. State:",
          wsRef.current?.readyState
        );
        return;
      }

      try {
        wsRef.current.send(JSON.stringify(payload));
      } catch (err) {
        console.error("Failed to send websocket message:", err);
      }
      return;
    }

    // default: show locally only. AI calls should only be sent to server when
    // the message is explicitly targeted via a mention (@persona or @Name).
    setMessages((prev) => [
      ...prev,
      { id: nextId.current++, text, sender: "me", username: currentUser },
    ]);

    const payload = { text, username: currentUser, persona };

    try {
      wsRef.current?.send(JSON.stringify(payload));
    } catch (err) {
      console.error("Failed to send websocket message:", err);
    }
  };

  useEffect(() => {
    if (currentUser) {
      connect();
    }
    return () => wsRef.current?.close();
  }, [currentUser]);

  const sendTypingIndicator = (isTyping: boolean) => {
    // Send typing presence to the backend so other connected clients can
    // be notified. The backend will rebroadcast to other clients and will
    // not forward typing events to OpenAI or DB.
    try {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      wsRef.current.send(
        JSON.stringify({ type: "typing", username: currentUser, isTyping })
      );
    } catch (err) {
      console.error("Failed to send typing indicator:", err);
    }
  };

  return {
    connectionStatus,
    messages,
    typingUsers,
    connectedUsers,
    sendMessage,
    sendTypingIndicator,
  };
}
