import axios from "axios";

const BASE_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

const API = axios.create({
  baseURL: BASE_URL,
});

// Arayüzde seçilen markanın ID'sini otomatik alır (Yoksa 1 yani FieldPie sayar)
const getBrandId = () => {
  const id = localStorage.getItem("selectedBrandId");
  return id ? Number(id) : 1;
};

export const getBrands = () => API.get("/api/brands").then((r) => r.data);
export const getBrand = (id) => API.get(`/api/brands/${id}`).then((r) => r.data);
export const updateBrand = (id, data) => API.put(`/api/brands/${id}`, data).then((r) => r.data);
export const deleteBrand = (id) => API.delete(`/api/brands/${id}`).then((r) => r.data);
export const duplicateBrand = (id) => API.post(`/api/brands/${id}/duplicate`).then((r) => r.data);
export const createBrand = (brandData) => API.post("/api/brands", brandData).then((r) => r.data);

// Tüm isteklere ?brand_id= parametresini otomatik ekliyoruz
export const getCalendar = (year, month) => API.get(`/api/calendar/${year}/${month}?brand_id=${getBrandId()}`).then((r) => r.data);
export const listCalendars = () => API.get(`/api/calendars?brand_id=${getBrandId()}`).then((r) => r.data);
export const generateCalendar = (month, year) => API.post("/api/calendar/generate", { month, year, brand_id: getBrandId() }).then((r) => r.data);
export const generateAllContent = (month, year) => API.post("/api/content/generate-all", { month, year, brand_id: getBrandId() }).then((r) => r.data);
export const regenerateItem = (month, year, item_id) => API.post("/api/content/regenerate", { month, year, item_id }).then((r) => r.data);
export const updateStatus = (month, year, item_id, status) => API.patch("/api/item/status", { month, year, item_id, status }).then((r) => r.data);
export const editField = (month, year, item_id, field, value) => API.patch("/api/item/edit", { month, year, item_id, field, value }).then((r) => r.data);
export const getStats = (year, month) => API.get(`/api/stats/${year}/${month}?brand_id=${getBrandId()}`).then((r) => r.data);
export const generateImage = (month, year, item_id) => API.post("/api/image/generate", { month, year, item_id }).then((r) => r.data);
export const deleteCalendar = (year, month) => API.delete(`/api/calendar/${year}/${month}?brand_id=${getBrandId()}`).then((r) => r.data);
export const uploadLogo = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/api/upload-logo", formData, { headers: { "Content-Type": "multipart/form-data" } }).then(r => r.data);
};
export const assessBrand = (data) => API.post("/api/brands/assess", data).then(r => r.data);