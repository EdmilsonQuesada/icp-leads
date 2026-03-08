import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchLeads, exportCsv, exportExcel } from "../api/client";
import { LeadRow } from "../components/LeadRow";
import { FilterBar } from "../components/FilterBar";

const PAGE_SIZE = 50;

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function LeadList() {
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(1);

  // Inicializa filtros a partir de query params da URL (ex: vindo do Dashboard)
  const [filters, setFilters] = useState(() => {
    const init = {};
    if (searchParams.get("category")) init.category = searchParams.get("category");
    if (searchParams.get("platform")) init.platform = searchParams.get("platform");
    if (searchParams.get("status"))   init.status   = searchParams.get("status");
    if (searchParams.get("birthday_soon") === "true") init.birthday_soon = true;
    return init;
  });

  function handleFilterChange(newFilters) {
    setFilters(newFilters);
    setPage(1);
  }

  const queryParams = { ...filters, skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE };
  const { data, isLoading } = useQuery({
    queryKey: ["leads", queryParams],
    queryFn: () => fetchLeads(queryParams).then((r) => r.data),
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

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
      <FilterBar filters={filters} onChange={handleFilterChange} />
      {isLoading ? (
        <p className="text-gray-500">Carregando...</p>
      ) : (
        <>
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

          {totalPages > 1 && (
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>
                Página {page} de {totalPages} &nbsp;·&nbsp; {data?.total} leads no total
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 border rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  ← Anterior
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 border rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Próxima →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
