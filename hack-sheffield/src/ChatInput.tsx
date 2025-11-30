import React, { useState, useRef, useEffect } from "react";

export function ChatInput({
  message,
  setMessage,
  onSend,
  onTyping,
  suggestions = [],
}: any) {
  const [open, setOpen] = useState(false);
  const [filtered, setFiltered] = useState<any[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLFormElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // watch for @mention pattern — show suggestions even when only '@' is typed
  useEffect(() => {
    const match = message.match(/@([A-Za-z0-9_-]*)$/);
    if (match) {
      const q = match[1].toLowerCase();
      let list: string[];
      if (!q) {
        // show full list when user typed only '@'
        list = suggestions.slice();
      } else {
        // suggestions now can be objects with id field
        list = suggestions.filter((s: any) =>
          (s.id || s).toString().toLowerCase().startsWith(q)
        );
      }
      setFiltered(list as any[]);
      setActiveIndex(0);
      setOpen(list.length > 0);
    } else {
      setOpen(false);
    }
  }, [message, suggestions]);

  const insertSuggestion = (item: any) => {
    const name = item.id || item;
    // replace the trailing @token (including when token is empty) with the full mention + space
    const newText = message.replace(/@([A-Za-z0-9_-]*)$/, `@${name} `);
    setMessage(newText);

    setOpen(false);
    // Keep focus in the input and move caret to the end of the inserted text
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
        const len = newText.length;
        try {
          inputRef.current.setSelectionRange(len, len);
        } catch (e) {
          // ignore if unable to set selection
        }
      }
    }, 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      const sel = filtered[activeIndex];
      if (sel) insertSuggestion(sel);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <form
      ref={containerRef}
      onSubmit={(e) => {
        e.preventDefault();
        onSend(message);
        setMessage("");
      }}
      className="relative flex items-center gap-2 sm:gap-3 bg-linear-to-r from-blue-50 to-indigo-50 p-3 sm:p-4 lg:p-5 border-t-2 border-blue-200 shadow-lg"
    >
      <input
        className="flex-1 px-4 py-3 sm:px-5 sm:py-3.5 lg:px-6 lg:py-4 text-sm sm:text-base lg:text-lg rounded-full border-2 border-blue-300 focus:border-blue-500 focus:ring-2 sm:focus:ring-4 focus:ring-blue-100 transition-all shadow-sm hover:shadow-md outline-none"
        placeholder="Type a message..."
        value={message}
        onChange={(e) => {
          setMessage(e.target.value);
          if (!onTyping) return;

          // Clear previous timeout
          if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);

          // If there's any content, signal typing=true; empty content -> typing=false
          const hasContent = String(e.target.value).trim().length > 0;
          try {
            onTyping(Boolean(hasContent));
          } catch (err) {
            console.error("onTyping handler error:", err);
          }

          // After 2 seconds of inactivity, send typing=false if there is no more activity
          typingTimeoutRef.current = setTimeout(() => {
            try {
              onTyping(false);
            } catch (err) {
              console.error("onTyping handler error:", err);
            }
          }, 2000);
        }}
        ref={inputRef}
        onBlur={() => {
          // ensure we clear typing state on blur
          if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
          if (onTyping)
            try {
              onTyping(false);
            } catch {}
        }}
        onKeyDown={handleKeyDown}
        aria-autocomplete="list"
      />

      {open && (
        <div className="absolute left-3 sm:left-6 bottom-16 sm:bottom-20 bg-white rounded-xl shadow-2xl border border-gray-200 w-[calc(100%-1.5rem)] sm:w-80 max-w-md z-40 overflow-hidden">
          {filtered.map((s: any, idx: number) => (
            <div
              key={(s.id || s).toString() + idx}
              onMouseDown={(ev) => {
                // mouseDown to prevent blur before click
                ev.preventDefault();
                insertSuggestion(s);
              }}
              className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors min-h-16 ${
                idx === activeIndex
                  ? "bg-blue-50 border-l-4 border-blue-500"
                  : "hover:bg-gray-50"
              }`}
            >
              {s.image ? (
                <img
                  src={s.image}
                  alt={s.id || s}
                  className="w-10 h-10 rounded-full object-cover shadow-sm shrink-0"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-linear-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-600 font-bold shrink-0">
                  @
                </div>
              )}
              <div className="flex flex-col justify-center flex-1 min-h-10">
                <div className="font-semibold text-gray-800">{s.id || s}</div>
                {s.desc && (
                  <div className="text-xs text-gray-500 mt-0.5">{s.desc}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <button className="px-4 py-3 sm:px-6 sm:py-3.5 lg:px-8 lg:py-4 bg-linear-to-r from-blue-600 to-blue-700 text-white rounded-full font-semibold shadow-md hover:shadow-xl hover:from-blue-700 hover:to-blue-800 transition-all transform hover:scale-105 active:scale-95 text-sm sm:text-base whitespace-nowrap">
        <span className="hidden sm:inline">Send</span>
        <span className="sm:hidden">→</span>
      </button>
    </form>
  );
}
