import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchLead, fetchLeadEvents, markContacted, archiveLead } from "../api/client";
import { Timeline } from "../components/Timeline";

const BADGE = { quente: "bg-red-100 text-red-700", morno: "bg-yellow-100 text-yellow-700",
                frio: "bg-blue-100 text-blue-700", descarte: "bg-gray-100 text-gray-500" };
const EMOJI = { quente: "🔥", morno: "🌤", frio: "❄️", descarte: "🗑" };

export function LeadProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: lead, isLoading } = useQuery({
    queryKey: ["lead", id],
    queryFn: () => fetchLead(id).then((r) => r.data),
  });
  const { data: events = [] } = useQuery({
    queryKey: ["lead-events", id],
    queryFn: () => fetchLeadEvents(id).then((r) => r.data),
  });

  const contacted = useMutation({
    mutationFn: () => markContacted(id),
    onSuccess: () => qc.invalidateQueries(["lead", id]),
  });
  const archive = useMutation({
    mutationFn: () => archiveLead(id),
    onSuccess: () => navigate("/leads"),
  });

  if (isLoading) return <p className="p-6 text-gray-500">Carregando...</p>;
  if (!lead) return <p className="p-6 text-red-500">Lead não encontrado.</p>;

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-5">
      <button onClick={() => navigate(-1)} className="text-sm text-indigo-500 hover:underline">← Voltar</button>
      <div className="bg-white rounded-xl border p-5 space-y-4">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-full bg-indigo-200 flex items-center justify-center text-xl font-bold text-indigo-700 shrink-0">
            {(lead.display_name || lead.username)[0].toUpperCase()}
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold">@{lead.username}</h2>
            {lead.display_name && <p className="text-sm text-gray-500">{lead.display_name}</p>}
            {lead.city && <p className="text-xs text-gray-400">📍 {lead.city}{lead.country ? `, ${lead.country}` : ""}</p>}
          </div>
          <div className={`px-3 py-1.5 rounded-full text-sm font-semibold ${BADGE[lead.category] || BADGE.descarte}`}>
            {EMOJI[lead.category]} {lead.score} pts
          </div>
        </div>
        {lead.bio && <p className="text-sm text-gray-600 italic border-l-2 border-indigo-200 pl-3">"{lead.bio}"</p>}
        <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
          {lead.followers != null && <div>👥 <b>{lead.followers.toLocaleString()}</b> seguidores</div>}
          {lead.age && <div>🎂 <b>{lead.age} anos</b></div>}
          {lead.birthdate && <div>📅 Nasc.: <b>{lead.birthdate}</b> <span className="text-xs text-gray-400">({lead.birthdate_source})</span></div>}
          <div>📱 <b className="capitalize">{lead.platform}</b></div>
          <div>Status: <b className="capitalize">{lead.status}</b></div>
        </div>
        <div className="flex gap-2 pt-1">
          {lead.status !== "contacted" && (
            <button onClick={() => contacted.mutate()} disabled={contacted.isPending}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50">
              ✉️ Marcar como Contatado
            </button>
          )}
          {lead.status !== "archived" && (
            <button onClick={() => archive.mutate()} disabled={archive.isPending}
                    className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50 text-gray-600 disabled:opacity-50">
              Arquivar
            </button>
          )}
        </div>
      </div>
      <div className="bg-white rounded-xl border p-5">
        <h3 className="font-semibold text-gray-700 mb-4">Timeline de Eventos</h3>
        <Timeline events={events} />
      </div>
    </div>
  );
}
