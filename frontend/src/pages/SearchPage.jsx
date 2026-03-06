import { useState } from "react";
import { createSearch } from "../api/client";

export function SearchPage() {
  const [keywords, setKeywords] = useState("constelação familiar, constelação sistêmica");
  const [platforms, setPlatforms] = useState({ instagram: true, youtube: true });
  const [status, setStatus] = useState(null);

  const handleSearch = async () => {
    const kws = keywords.split(",").map((k) => k.trim()).filter(Boolean);
    const plts = Object.entries(platforms).filter(([, v]) => v).map(([k]) => k);
    try {
      const res = await createSearch({ keywords: kws, platforms: plts });
      setStatus(`Job #${res.data.job_id} criado com sucesso! Os leads serão processados em breve.`);
    } catch (e) {
      setStatus("Erro ao criar job de busca.");
    }
  };

  return (
    <div className="p-6 max-w-lg space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Nova Busca</h1>
      <div className="bg-white rounded-xl border p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Keywords (separadas por vírgula)</label>
          <textarea value={keywords} onChange={(e) => setKeywords(e.target.value)}
                    rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Plataformas</label>
          <div className="flex gap-4">
            {["instagram", "youtube"].map((p) => (
              <label key={p} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={platforms[p]}
                       onChange={(e) => setPlatforms({ ...platforms, [p]: e.target.checked })} />
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </label>
            ))}
          </div>
        </div>
        <button onClick={handleSearch}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
          🔍 Iniciar Busca
        </button>
        {status && <p className="text-sm text-green-600">{status}</p>}
      </div>
    </div>
  );
}
