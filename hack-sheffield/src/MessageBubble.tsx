import MarkdownIt from "markdown-it";

const md = new MarkdownIt({ html: false, linkify: true, typographer: true });

export function MessageBubble({
  message,
}: {
  message: {
    sender: string;
    loading?: boolean;
    text?: string;
    username?: string;
    targetPersona?: string;
  };
}) {
  const isMe = message.sender === "me";

  return (
    <div
      className={`flex flex-col ${
        isMe ? "items-end" : "items-start"
      } gap-1 mb-2 sm:mb-3 animate-in fade-in slide-in-from-bottom-2 duration-300`}
    >
      {message.username && (
        <span
          className={`text-xs px-2 sm:px-4 font-semibold ${
            isMe ? "text-blue-700" : "text-gray-700"
          }`}
        >
          {message.username}{" "}
          {message.targetPersona ? (
            <span className="text-xs text-purple-600 font-medium">
              → @{message.targetPersona}
            </span>
          ) : null}
        </span>
      )}

      <div
        className={`max-w-[85%] sm:max-w-[80%] lg:max-w-[75%] overflow-x-auto shadow-md transition-all duration-200 ${
          message.loading ? "animate-pulse opacity-70" : "hover:shadow-lg"
        } ${
          isMe
            ? "px-3 py-2 sm:px-4 sm:py-2.5 lg:px-5 lg:py-3 rounded-2xl rounded-tr-sm bg-linear-to-br from-blue-600 to-blue-700 text-white text-sm sm:text-base"
            : message.sender === "server"
            ? "px-3 py-3 sm:px-4 sm:py-3.5 lg:px-5 lg:py-4 rounded-2xl bg-linear-to-br from-emerald-50 to-teal-50 text-gray-800 border border-emerald-200 text-left text-sm sm:text-base"
            : "px-3 py-2 sm:px-4 sm:py-2.5 lg:px-5 lg:py-3 rounded-2xl rounded-tl-sm bg-white text-gray-900 border border-gray-200 text-sm sm:text-base"
        }`}
      >
        {message.loading ? (
          "..."
        ) : message.sender === "server" || message.sender === "ai" ? (
          <div
            className="text-left whitespace-pre-wrap"
            dangerouslySetInnerHTML={{
              __html: md.render(String(message.text || "")),
            }}
          />
        ) : (
          message.text
        )}
      </div>
    </div>
  );
}
