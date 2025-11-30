import { MessageBubble } from "./MessageBubble";
import { useEffect, useRef } from "react";

export function MessageList({
  messages,
  messagesContainerRef,
  typingUsers = new Set(),
}: any) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // When new messages arrive, scroll the container to the bottom so the
  // latest message is visible. We use a tiny timeout/requestAnimationFrame so
  // the DOM update completes before measuring/scrolling.
  useEffect(() => {
    const container = messagesContainerRef?.current as HTMLElement | null;
    const bottomEl = bottomRef.current;
    if (!container) return;

    // Use a micro task to avoid racing with render
    const t = requestAnimationFrame(() => {
      try {
        if (bottomEl) {
          bottomEl.scrollIntoView({ behavior: "smooth", block: "end" });
        } else {
          // fallback: scroll to full height
          container.scrollTop = container.scrollHeight;
        }
      } catch (e) {
        // ignore scroll failures
      }
    });

    return () => cancelAnimationFrame(t);
  }, [messages, messagesContainerRef]);
  return (
    <div
      ref={messagesContainerRef}
      className="bg-blue-500 flex-1 overflow-y-auto p-4 space-y-4"
    >
      {messages.map((msg: any) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {/* bottom sentinel used for auto-scrolling */}
      <div ref={bottomRef} />
      {/* Show a concise typing indicator in the message area */}
      {typingUsers.size > 0 && (
        <div className="px-4 py-2 text-sm text-gray-400 italic">
          {(() => {
            const names = Array.from(typingUsers || []);
            if (names.length === 1) return `${names[0]} is typing...`;
            if (names.length === 2)
              return `${names[0]} and ${names[1]} are typing...`;
            return `${names.slice(0, 2).join(", ")} and ${
              names.length - 2
            } others are typing...`;
          })()}
        </div>
      )}
    </div>
  );
}
