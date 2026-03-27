import axios from "axios";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

const API = axios.create({
  baseURL: BASE_URL,
});

export const getCalendar = (year, month) => API.get(`/api/calendar/${year}/${month}`).then((r) => r.data);
export const listCalendars = () => API.get("/api/calendars").then((r) => r.data);
export const generateCalendar = (month, year) => API.post("/api/calendar/generate", { month, year }).then((r) => r.data);
export const generateAllContent = (month, year) => API.post("/api/content/generate-all", { month, year }).then((r) => r.data);
export const regenerateItem = (month, year, item_id) => API.post("/api/content/regenerate", { month, year, item_id }).then((r) => r.data);
export const updateStatus = (month, year, item_id, status) => API.patch("/api/item/status", { month, year, item_id, status }).then((r) => r.data);
export const editField = (month, year, item_id, field, value) => API.patch("/api/item/edit", { month, year, item_id, field, value }).then((r) => r.data);
export const getStats = (year, month) => API.get(`/api/stats/${year}/${month}`).then((r) => r.data);
export const generateImage = (month, year, item_id) => API.post("/api/image/generate", { month, year, item_id }).then((r) => r.data);
export const deleteCalendar = (year, month) => API.delete(`/api/calendar/${year}/${month}`).then((r) => r.data);