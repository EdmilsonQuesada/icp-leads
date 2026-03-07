import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createSearch, searchApify, fetchSearchJobs } from "../api/client";

const STATUS_PT = { queued: "Na fila", running: "Executando...", done: "Concluído", error: "Erro" };
const STATUS_COLOR = {
  queued:  "bg-gray-100 text-gray-600",
  running: "bg-blue-100 text-blue-700",
  done:    "bg-green-100 text-green-700",
  error:   "bg-red-100 text-red-600",
};

function timeAgo(dateStr) {
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
  if (diff < 60) return `${diff}s atrás`;
  if (diff < 3600) return `${Math.floor(diff / 60)}min atrás`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
  return `${Math.floor(diff / 86400)}d atrás`;
}

export function SearchPage() {
  const qc = useQueryClient();
  const [keywords, setKeywords] = useState("constelação familiar, constelação sistêmica");
  const [platforms, setPlatforms] = useState({ instagram: true, youtube: true });
  const [method, setMethod] = useState("apify"); // "apify" ou "instagrapi"
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const { data: jobs = [] } = useQuery({
    queryKey: ["search-jobs"],
    queryFn: () => fetchSearchJobs().then((r) => r.data),
    refetchInterval: (query) =>
      query.state.data?.some?.((j) => j.status === "queued" || j.status === "running") ? 3000 : false,
  });

  const handleSearch = async () => {
    const kws = keywords.split(",").map((k) => k.trim()).filter(Boolean);
    const plts = Object.entries(platforms).filter(([, v]) => v).map(([k]) => k);

    setLoading(true);
    setStatus(null);

    try {
      let res;

      if (method === "apify") {
        // Novo endpoint Apify
        res = await searchApify({
          hashtags: kws,
          platforms: plts,
          max_posts: 50,
        });
      } else {
        // Legacy instagrapi endpoint
        res = await createSearch({ keywords: kws, platforms: plts });
      }

      setStatus(
        `✅ Job #${res.data.job_id} criado! Os leads serão coletados em breve.`
      );
      qc.invalidateQueries(["search-jobs"]);
    } catch (e) {
      console.error("Search error:", e);
      setStatus("❌ Erro ao criar job de busca. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-lg space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Nova Busca</h1>

      <div className="bg-white rounded-xl border p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Keywords (separadas por vírgula)</label>
          <textarea value={keywords} onChange={(e) => setKeywords(e.target.value)}
                    rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Método de Coleta
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                checked={method === "apify"}
                onChange={() => setMethod("apify")}
              />
              🚀 Apify (Recomendado - sem bloqueios)
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                checked={method === "instagrapi"}
                onChange={() => setMethod("instagrapi")}
              />
              📸 Instagrapi (Legacy)
            </label>
          </div>
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
        <button onClick={handleSearch} disabled={loading}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed">
          {loading ? "⏳ Criando job..." : "🔍 Iniciar Busca"}
        </button>
        {status && (
          <p className={`text-sm ${status.startsWith("✅") ? "text-green-600" : "text-red-500"}`}>
            {status}
          </p>
        )}
      </div>

      {jobs.length > 0 && (
        <div className="bg-white rounded-xl border p-5 space-y-3">
          <h2 className="font-semibold text-gray-700">Histórico de Buscas</h2>
          <div className="space-y-2">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between text-sm border rounded-lg px-3 py-2">
                <div className="flex-1 min-w-0">
                  <p className="text-gray-700 truncate font-medium">
                    {(job.keywords || []).join(", ")}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {(job.platforms || []).join(", ")} · {timeAgo(job.created_at)}
                    {job.leads_found != null && job.status === "done" && (
                      <span className="ml-1 text-green-600 font-medium">· {job.leads_found} leads</span>
                    )}
                  </p>
                </div>
                <span className={`ml-3 shrink-0 px-2 py-0.5 rounded-full text-xs font-semibold ${STATUS_COLOR[job.status] || STATUS_COLOR.queued}`}>
                  {STATUS_PT[job.status] ?? job.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
