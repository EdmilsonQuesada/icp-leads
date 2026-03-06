export function FilterBar({ filters, onChange }) {
  return (
    <div className="flex flex-wrap gap-3 p-4 bg-white rounded-xl border">
      <select value={filters.category || ""} onChange={(e) => onChange({ ...filters, category: e.target.value || undefined })}
              className="border rounded px-3 py-1.5 text-sm">
        <option value="">Todas categorias</option>
        <option value="quente">🔥 Quente</option>
        <option value="morno">🌤 Morno</option>
        <option value="frio">❄️ Frio</option>
        <option value="descarte">🗑 Descarte</option>
      </select>
      <select value={filters.platform || ""} onChange={(e) => onChange({ ...filters, platform: e.target.value || undefined })}
              className="border rounded px-3 py-1.5 text-sm">
        <option value="">Todas plataformas</option>
        <option value="instagram">Instagram</option>
        <option value="youtube">YouTube</option>
      </select>
      <input type="text" placeholder="Filtrar por cidade..."
             value={filters.city || ""} onChange={(e) => onChange({ ...filters, city: e.target.value || undefined })}
             className="border rounded px-3 py-1.5 text-sm" />
      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={!!filters.birthday_soon}
               onChange={(e) => onChange({ ...filters, birthday_soon: e.target.checked || undefined })} />
        🎂 Aniversário próximo
      </label>
    </div>
  );
}
