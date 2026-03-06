import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchLeads, exportCsv, exportExcel } from "../api/client";
import { LeadRow } from "../components/LeadRow";
import { FilterBar } from "../components/FilterBar";

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function LeadList() {
  const [filters, setFilters] = useState({});
  const { data, isLoading } = useQuery({
    queryKey: ["leads", filters],
    queryFn: () => fetchLeads(filters).then((r) => r.data),
  });

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">
          Leads {data ? `(${data.total})` : ""}
        </h1>
        <div className="flex gap-2">
          <button onClick={() => exportCsv().then((r) => downloadBlob(r.data, "leads.csv"))}
                  className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">📤 CSV</button>
          <button onClick={() => exportExcel().then((r) => downloadBlob(r.data, "leads.xlsx"))}
                  className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">📊 Excel</button>
        </div>
      </div>
      <FilterBar filters={filters} onChange={setFilters} />
      {isLoading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : (
        <div className="bg-white rounded-xl border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="p-3 text-left w-10"></th>
                <th className="p-3 text-left">Usuário</th>
                <th className="p-3 text-left">Score</th>
                <th className="p-3 text-left">Fonte</th>
                <th className="p-3 text-left">Status</th>
                <th className="p-3 text-left">Ação</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((lead) => <LeadRow key={lead.id} lead={lead} />)}
            </tbody>
          </table>
          {data?.items.length === 0 && (
            <p className="text-center text-gray-400 py-8">Nenhum lead encontrado</p>
          )}
        </div>
      )}
    </div>
  );
}
