import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchSettings, updateSettings } from "../api/client";

export function Settings() {
  const qc = useQueryClient();
  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: () => fetchSettings().then((r) => r.data),
  });

  const [keywords, setKeywords] = useState("");
  const [maxLeads, setMaxLeads] = useState(100);
  const [collectHour, setCollectHour] = useState(3);
  const [igEnabled, setIgEnabled] = useState(true);
  const [ytEnabled, setYtEnabled] = useState(true);

  useEffect(() => {
    if (settings) {
      setKeywords((settings.keywords || []).join(", "));
      setMaxLeads(settings.max_leads_per_day);
      setCollectHour(settings.collect_hour);
      setIgEnabled(settings.instagram_enabled);
      setYtEnabled(settings.youtube_enabled);
    }
  }, [settings]);

  const save = useMutation({
    mutationFn: () => updateSettings({
      keywords: keywords.split(",").map((k) => k.trim()).filter(Boolean),
      max_leads_per_day: maxLeads,
      collect_hour: collectHour,
      instagram_enabled: igEnabled,
      youtube_enabled: ytEnabled,
    }),
    onSuccess: () => qc.invalidateQueries(["settings"]),
  });

  return (
    <div className="p-6 max-w-lg mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-gray-800">Configurações</h1>
      <div className="bg-white rounded-xl border p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Keywords de busca (separadas por vírgula)</label>
          <textarea value={keywords} onChange={(e) => setKeywords(e.target.value)}
                    rows={4} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Máx. leads/dia</label>
            <input type="number" value={maxLeads} onChange={(e) => setMaxLeads(Number(e.target.value))}
                   className="border rounded-lg px-3 py-2 text-sm w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hora da coleta (0-23)</label>
            <input type="number" min={0} max={23} value={collectHour}
                   onChange={(e) => setCollectHour(Number(e.target.value))}
                   className="border rounded-lg px-3 py-2 text-sm w-full" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Plataformas ativas</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={igEnabled} onChange={(e) => setIgEnabled(e.target.checked)} />
              Instagram
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={ytEnabled} onChange={(e) => setYtEnabled(e.target.checked)} />
              YouTube
            </label>
          </div>
        </div>
        <button onClick={() => save.mutate()}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
          {save.isPending ? "Salvando..." : "Salvar configurações"}
        </button>
        {save.isSuccess && <p className="text-sm text-green-600 text-center">Salvo com sucesso!</p>}
      </div>
    </div>
  );
}
