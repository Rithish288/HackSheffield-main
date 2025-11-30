export function ChatHeader({
  connectionStatus,
  currentPersona,
  onOpenPersonaPicker,
  personaImage,
}: any) {
  return (
    <div className="flex justify-between items-center bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 h-16 sm:h-20 text-white px-2 sm:px-6 lg:px-8 shadow-lg">
      <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
        <img
          className="h-8 sm:h-14 lg:h-16 drop-shadow-lg"
          src="Images/odyssey_boat.png"
        />
        <div className="text-sm sm:text-lg lg:text-xl font-bold bg-linear-to-r from-blue-300 to-cyan-300 bg-clip-text text-transparent">
          Odyssey Chat
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 lg:gap-5 shrink-0">
        {/* single-user app: no user selector */}

        <button
          onClick={onOpenPersonaPicker}
          className="flex items-center gap-2 sm:gap-2 px-3 sm:px-3 lg:px-4 py-2 sm:py-2 bg-linear-to-r from-blue-600 to-blue-700 text-white rounded-full border border-blue-500 hover:from-blue-700 hover:to-blue-800 transition-all shadow-md hover:shadow-lg transform hover:scale-105"
        >
          {personaImage && (
            <img
              src={personaImage}
              alt={currentPersona}
              className="w-6 h-6 sm:w-7 sm:h-7 rounded-full border-2 border-white shadow-sm shrink-0"
            />
          )}
          <span className="text-xs sm:text-xs lg:text-sm font-semibold whitespace-nowrap">
            {currentPersona}
          </span>
        </button>

        <div className="text-xs sm:text-sm flex items-center gap-1.5 sm:gap-2">
          <div
            className={
              connectionStatus === "connected"
                ? "w-2 h-2 rounded-full bg-green-400 animate-pulse shadow-lg shadow-green-400/50"
                : connectionStatus === "error"
                ? "w-2 h-2 rounded-full bg-red-400 shadow-lg shadow-red-400/50"
                : "w-2 h-2 rounded-full bg-gray-400"
            }
          />
          <span className="hidden sm:inline text-gray-300 font-medium">
            {connectionStatus}
          </span>
        </div>
      </div>
    </div>
  );
}
