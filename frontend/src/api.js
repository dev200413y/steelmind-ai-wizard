import axios from 'axios';

const API_BASE = 'http://localhost:8000';
export { API_BASE };

export const runQuery = async (formData) => {
  const response = await axios.post(`${API_BASE}/diagnose`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const runVoiceQuery = async (formData) => {
  const response = await axios.post(`${API_BASE}/voice`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const submitFeedback = async (feedback) => {
  const fd = new FormData();
  Object.keys(feedback).forEach(key => {
      fd.append(key, feedback[key]);
  });
  return axios.post(`${API_BASE}/feedback`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const checkHealth = async () => {
  return axios.get(`${API_BASE}/health`);
};

export const getHistory = async () => {
  const response = await axios.get(`${API_BASE}/history`);
  return response.data;
};

// ── Live Dashboard APIs ──────────────────────────────────────
export const getLiveSensors = async () => {
  const response = await axios.get(`${API_BASE}/api/live/sensors`);
  return response.data;
};

export const getLiveAlerts = async (severity, area, limit = 50) => {
  const params = { limit };
  if (severity) params.severity = severity;
  if (area) params.area = area;
  const response = await axios.get(`${API_BASE}/api/live/alerts`, { params });
  return response.data;
};

export const getEquipmentFleet = async () => {
  const response = await axios.get(`${API_BASE}/api/equipment/fleet`);
  return response.data;
};

export const createTicket = async (payload) => {
  const fd = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null) fd.append(key, value);
  });
  const response = await axios.post(`${API_BASE}/api/tickets`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
