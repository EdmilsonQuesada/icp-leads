import { useQuery } from "@tanstack/react-query";
import { fetchLeads } from "../api/client";
import { StatCard } from "../components/StatCard";

export function Dashboard() {
  const { data: quentes } = useQuery({
    queryKey: ["leads", { category: "quente" }],
    queryFn: () => fetchLeads({ category: "quente" }).then((r) => r.data),
  });
  const { data: mornos } = useQuery({
    queryKey: ["leads", { category: "morno" }],
    queryFn: () => fetchLeads({ category: "morno" }).then((r) => r.data),
  });
  const { data: frios } = useQuery({
    queryKey: ["leads", { category: "frio" }],
    queryFn: () => fetchLeads({ category: "frio" }).then((r) => r.data),
  });
  const { data: aniversarios } = useQuery({
    queryKey: ["leads", { birthday_soon: true }],
    queryFn: () => fetchLeads({ birthday_soon: true }).then((r) => r.data),
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard emoji="🔥" label="Leads Quentes" value={quentes?.total ?? 0} color="red"    to="/leads?category=quente" />
        <StatCard emoji="🌤" label="Leads Mornos"  value={mornos?.total ?? 0}  color="yellow" to="/leads?category=morno" />
        <StatCard emoji="❄️" label="Leads Frios"   value={frios?.total ?? 0}   color="blue"   to="/leads?category=frio" />
        <StatCard emoji="🎂" label="Aniversários (7d)" value={aniversarios?.total ?? 0} color="green" to="/leads?birthday_soon=true" />
      </div>
      <div className="bg-white rounded-xl border p-5">
        <h2 className="font-semibold text-gray-700 mb-3">Início Rápido</h2>
        <p className="text-sm text-gray-500">Use o menu <strong>Leads</strong> para visualizar e gerenciar seus leads, ou <strong>Buscar</strong> para iniciar uma nova coleta.</p>
      </div>
    </div>
  );
}
