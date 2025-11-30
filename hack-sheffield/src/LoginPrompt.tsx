import React from "react";

export interface LoginPromptProps {
  username: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  errorMessage?: string;
}

export function LoginPrompt({
  username,
  onChange,
  onSubmit,
  errorMessage,
}: LoginPromptProps) {
  return (
    <div className="flex justify-center items-center h-screen bg-linear-to-r from-[#809DF2] to-[#FFFFFF]">
      <div className="bg-white rounded-lg p-8 max-w-md w-full shadow-lg">
        <h2 className="text-2xl font-bold mb-6 text-center">Join Chat</h2>
        {errorMessage && (
          <div className="mb-4 p-3 bg-red-100 border-2 border-red-500 rounded-lg text-red-700 font-semibold text-center">
            {errorMessage}
          </div>
        )}
        <input
          type="text"
          placeholder="Enter your username"
          value={username}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && username.trim()) onSubmit();
          }}
          className="w-full px-4 py-3 border-2 border-blue-500 rounded-lg mb-4 text-lg focus:outline-none focus:border-blue-700"
        />
        <button
          onClick={() => {
            if (username.trim()) onSubmit();
          }}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
        >
          Join
        </button>
      </div>
    </div>
  );
}

export default LoginPrompt;
