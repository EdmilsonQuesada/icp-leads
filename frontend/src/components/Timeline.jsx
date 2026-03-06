const ICONS = {
  comment: "💬", like: "❤️", birthday_soon: "🎂",
  score_change: "📈", enriched: "✨",
};

export function Timeline({ events = [] }) {
  if (!events.length) return <p className="text-gray-400 text-sm">Nenhum evento registrado.</p>;
  return (
    <div className="space-y-3">
      {events.map((event) => (
        <div key={event.id} className="flex gap-3 items-start">
          <span className="text-lg">{ICONS[event.event_type] || "📌"}</span>
          <div className="flex-1">
            <p className="text-sm text-gray-700">{event.description}</p>
            <p className="text-xs text-gray-400">{new Date(event.created_at).toLocaleDateString("pt-BR")}</p>
          </div>
          {event.score_delta !== 0 && (
            <span className={`text-sm font-semibold ${event.score_delta > 0 ? "text-green-600" : "text-red-500"}`}>
              {event.score_delta > 0 ? "+" : ""}{event.score_delta}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
