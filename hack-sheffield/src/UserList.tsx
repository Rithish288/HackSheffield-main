export function UserList({
  users,
  currentUser,
}: {
  users: Set<string>;
  currentUser: string;
}) {
  const userArray = Array.from(users).sort();

  return (
    <div className="hidden lg:flex flex-col w-64 bg-linear-to-b from-slate-50 to-gray-100 border-l border-gray-200 shadow-inner">
      <div className="p-4 border-b border-gray-300 bg-white">
        <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wide flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Online Users ({userArray.length})
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {userArray.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">
            No users connected
          </div>
        ) : (
          userArray.map((user) => (
            <div
              key={user}
              className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                user === currentUser
                  ? "bg-blue-100 border-2 border-blue-400 shadow-sm"
                  : "bg-white border border-gray-200 hover:border-blue-300 hover:shadow-md"
              }`}
            >
              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-md">
                  {user.charAt(0).toUpperCase()}
                </div>
                <div className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-green-500 border-2 border-white"></div>
              </div>

              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-800 text-sm truncate">
                  {user}
                  {user === currentUser && (
                    <span className="ml-2 text-xs text-blue-600 font-normal">
                      (You)
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500">Active now</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
