import { Link } from "react-router-dom";

const BADGE = {
  quente: "bg-red-100 text-red-700",
  morno: "bg-yellow-100 text-yellow-700",
  frio: "bg-blue-100 text-blue-700",
  descarte: "bg-gray-100 text-gray-500",
};
const EMOJI = { quente: "🔥", morno: "🌤", frio: "❄️", descarte: "🗑" };

const STATUS_PT = {
  monitoring: "Monitorando",
  contacted: "Contatado",
  archived: "Arquivado",
  pending: "Pendente",
};

const PLATFORM_LABEL = {
  instagram: "Instagram",
  youtube: "YouTube",
};

// Ícone e cor por gênero + confiança
function GenderBadge({ gender, confidence }) {
  if (!gender || gender === "ND") return <span className="text-gray-300 text-xs">❓</span>;
  const icon = gender === "F" ? "👩" : "👨";
  const isUncertain = confidence != null && confidence < 85;
  return (
    <span title={`${gender} (${confidence ?? "?"}%)`} className={`text-xs ${isUncertain ? "opacity-60" : ""}`}>
      {isUncertain ? "⚠️" : ""}{icon}
    </span>
  );
}

export function LeadRow({ lead }) {
  return (
    <tr className="border-b hover:bg-gray-50">
      <td className="p-3">
        <div className="w-8 h-8 rounded-full bg-indigo-200 flex items-center justify-center text-sm font-bold text-indigo-700">
          {(lead.display_name || lead.username)[0].toUpperCase()}
        </div>
      </td>
      <td className="p-3">
        <div className="flex items-center gap-1.5">
          <Link to={`/leads/${lead.id}`} className="font-medium text-indigo-600 hover:underline">
            @{lead.username}
          </Link>
          <GenderBadge gender={lead.gender} confidence={lead.gender_confidence} />
        </div>
        {lead.city && <div className="text-xs text-gray-400">📍 {lead.city}</div>}
        {lead.creator_profile && (
          <div className="text-xs text-gray-400">🔍 {lead.creator_profile}</div>
        )}
      </td>
      <td className="p-3">
        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${BADGE[lead.category] || BADGE.descarte}`}>
          {EMOJI[lead.category]} {lead.score} pts
        </span>
      </td>
      <td className="p-3 text-sm text-gray-500">{PLATFORM_LABEL[lead.platform] ?? lead.platform}</td>
      <td className="p-3 text-sm text-gray-500">{STATUS_PT[lead.status] ?? lead.status}</td>
      <td className="p-3">
        <Link to={`/leads/${lead.id}`} className="text-sm text-indigo-500 hover:underline">Ver</Link>
      </td>
    </tr>
  );
}
