import { useQuery } from "@tanstack/react-query";
import { fetchCities } from "../api/client";

const hasActiveFilters = (filters) =>
  Object.values(filters).some((v) => v !== undefined && v !== "" && v !== false);

export function FilterBar({ filters, onChange }) {
  const { data: cities = [] } = useQuery({
    queryKey: ["cities"],
    queryFn: () => fetchCities().then((r) => r.data),
    staleTime: 60_000, // cache 60s
  });

  return (
    <div className="flex flex-wrap gap-3 p-4 bg-white rounded-xl border items-center">
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

      <select value={filters.status || ""} onChange={(e) => onChange({ ...filters, status: e.target.value || undefined })}
              className="border rounded px-3 py-1.5 text-sm">
        <option value="">Todos status</option>
        <option value="monitoring">Monitorando</option>
        <option value="contacted">Contatado</option>
        <option value="archived">Arquivado</option>
      </select>

      {/* Dropdown dinâmico de cidades */}
      <select value={filters.city || ""} onChange={(e) => onChange({ ...filters, city: e.target.value || undefined })}
              className="border rounded px-3 py-1.5 text-sm">
        <option value="">Todas cidades</option>
        {cities.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>

      {/* Filtro de gênero */}
      <select value={filters.gender || ""} onChange={(e) => onChange({ ...filters, gender: e.target.value || undefined })}
              className="border rounded px-3 py-1.5 text-sm">
        <option value="">Todos gêneros</option>
        <option value="F">👩 Feminino</option>
        <option value="M">👨 Masculino</option>
        <option value="ND">❓ Não definido</option>
      </select>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={!!filters.birthday_soon}
               onChange={(e) => onChange({ ...filters, birthday_soon: e.target.checked || undefined })} />
        🎂 Aniversário próximo
      </label>

      {hasActiveFilters(filters) && (
        <button onClick={() => onChange({})}
                className="ml-auto text-xs text-gray-400 hover:text-red-500 border rounded px-2 py-1.5 hover:border-red-300 transition-colors">
          ✕ Limpar filtros
        </button>
      )}
    </div>
  );
}
