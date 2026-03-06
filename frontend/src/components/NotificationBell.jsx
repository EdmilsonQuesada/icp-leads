import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchNotifications } from "../api/client";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => fetchNotifications().then((r) => r.data),
    refetchInterval: 60000,
  });

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="relative p-2 text-gray-600 hover:text-indigo-600">
        🔔
        {notifications.length > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
            {notifications.length}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-lg border z-50">
          <div className="p-3 border-b font-semibold text-sm text-gray-700">Notificações</div>
          {notifications.length === 0 ? (
            <p className="p-4 text-sm text-gray-400">Nenhuma notificação</p>
          ) : (
            notifications.map((n, i) => (
              <div key={i} className="p-3 border-b text-sm text-gray-700 hover:bg-gray-50 last:border-0">
                {n.message}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
