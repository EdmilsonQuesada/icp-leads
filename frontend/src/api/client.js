import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const fetchLeads = (params) => api.get("/leads", { params });
export const fetchLead = (id) => api.get(`/leads/${id}`);
export const fetchLeadEvents = (id) => api.get(`/leads/${id}/events`);
export const markContacted = (id) => api.patch(`/leads/${id}/contacted`);
export const archiveLead = (id) => api.delete(`/leads/${id}`);
export const createSearch = (data) => api.post("/search", data);
export const exportCsv = () => api.get("/export/csv", { responseType: "blob" });
export const exportExcel = () => api.get("/export/excel", { responseType: "blob" });
export const fetchNotifications = () => api.get("/notifications");
export const fetchSettings = () => api.get("/settings");
export const updateSettings = (data) => api.patch("/settings", data);

export default api;
