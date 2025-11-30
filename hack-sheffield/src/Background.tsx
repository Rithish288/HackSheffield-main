import { useState, useRef } from "react";
import zeusImg from "../Images/zeus.jpeg";
import athenaImg from "../Images/athena.jpeg";
import hermesImg from "../Images/hermes.png";
import { ChatHeader } from "./ChatHeader";
import { MessageList } from "./MessageList.tsx";
import { ChatInput } from "./ChatInput";
import { useWebSocket } from "./WebSocket";
import LoginPrompt from "./LoginPrompt";
import { UserList } from "./UserList";

export function Background() {
  const [currentUsername, setCurrentUsername] = useState("");
  const [usernameSubmitted, setUsernameSubmitted] = useState(false);
  const [currentPersona] = useState("AI Descriptions");
  const [showPersonaPicker, setShowPersonaPicker] = useState(false);
  const [message, setMessage] = useState("");
  const [connectionError, setConnectionError] = useState("");
  const messagesContainerRef = useRef(null);

  const personas = [
    {
      id: "Zeus",
      name: "Zeus — General AI",
      desc: "General assistant with broad knowledge",
      image: zeusImg,
    },
    {
      id: "Athena",
      name: "Athena — Researcher",
      desc: "Careful, detailed explanations",
      image: athenaImg,
    },
    {
      id: "Hermes",
      name: "Hermes — Quick replies",
      desc: "Short, fast answers",
      image: hermesImg,
    },
  ];

  const getPersonaImage = (id: string) => {
    return personas.find((p) => p.id === id)?.image || "";
  };

  // Handler to logout user when connection fails
  const handleConnectionFailed = () => {
    console.log("Connection failed - logging out user");
    setUsernameSubmitted(false);
    setConnectionError("Server is not up. Please try again later.");
  };

  // Only initialize WebSocket after username is submitted
  const shouldConnect = Boolean(usernameSubmitted && currentUsername.trim());
  const {
    connectionStatus,
    messages,
    typingUsers,
    connectedUsers,
    sendMessage,
    sendTypingIndicator,
  } = useWebSocket(
    shouldConnect ? currentUsername : "",
    currentPersona,
    handleConnectionFailed
  );

  // Show reusable LoginPrompt until the user provides a username
  if (!usernameSubmitted || !currentUsername.trim()) {
    return (
      <LoginPrompt
        username={currentUsername}
        onChange={(v) => setCurrentUsername(v)}
        onSubmit={() => {
          setConnectionError(""); // Clear error on new attempt
          setUsernameSubmitted(true);
        }}
        errorMessage={connectionError}
      />
    );
  }

  return (
    <div className="flex justify-center items-center min-h-screen bg-linear-to-br from-blue-100 via-indigo-50 to-purple-100 p-2 sm:p-4">
      <div className="rounded-xl sm:rounded-2xl lg:rounded-3xl max-w-6xl w-full h-screen sm:h-[95vh] flex flex-row bg-white shadow-2xl overflow-hidden">
        {/* Main chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatHeader
            connectionStatus={connectionStatus}
            currentPersona={currentPersona}
            onOpenPersonaPicker={() => setShowPersonaPicker(true)}
            personaImage={getPersonaImage(currentPersona)}
          />

          {showPersonaPicker && (
            <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200 p-4">
              <div className="bg-white rounded-2xl p-4 sm:p-6 lg:p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl transform animate-in zoom-in-95 duration-200">
                <h3 className="text-xl sm:text-2xl lg:text-3xl font-bold text-center mb-2 bg-linear-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  AI Personas
                </h3>
                <p className="text-center text-sm sm:text-base text-gray-600 mb-4 sm:mb-6 lg:mb-8">
                  Choose an AI to mention with @name
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 lg:gap-6">
                  {personas.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        // Close the picker without changing persona
                        setShowPersonaPicker(false);
                      }}
                      className="flex flex-col items-center p-6 rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:bg-linear-to-br hover:from-blue-50 hover:to-indigo-50 transition-all transform hover:scale-105 hover:shadow-lg group"
                    >
                      <img
                        src={p.image}
                        alt={p.id}
                        className="w-28 h-28 rounded-full mb-4 object-cover shadow-md group-hover:shadow-xl transition-shadow"
                      />
                      <div className="font-bold text-lg text-center text-gray-800 group-hover:text-blue-600 transition-colors">
                        {p.id}
                      </div>
                      <div className="text-sm text-gray-600 text-center mt-2 leading-relaxed">
                        {p.desc}
                      </div>
                    </button>
                  ))}
                </div>
                <div className="mt-4 sm:mt-6 lg:mt-8 text-center">
                  <button
                    onClick={() => setShowPersonaPicker(false)}
                    className="px-5 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base bg-gray-200 text-gray-700 font-semibold rounded-full hover:bg-gray-300 transition-all shadow-md hover:shadow-lg"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          <MessageList
            messages={messages}
            messagesContainerRef={messagesContainerRef}
            typingUsers={typingUsers}
          />

          <ChatInput
            message={message}
            setMessage={setMessage}
            onSend={sendMessage}
            onTyping={sendTypingIndicator}
            suggestions={personas}
          />
        </div>

        {/* User list sidebar */}
        <UserList users={connectedUsers} currentUser={currentUsername} />
      </div>
    </div>
  );
}
