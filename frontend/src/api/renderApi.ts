// frontend/src/api/renderApi.ts
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export interface RenderPayload {
  remera_path: string;
  capas: any[];
  fuente: string;
  blur: number;
  opacidad: number;
  width: number;
  height: number;
}

export const renderMockup = async (payload: RenderPayload) => {
  const { data } = await api.post('/render', payload);
  return data;
};

export const exportMockup = async (payload: RenderPayload) => {
  const { data } = await api.post('/export', payload);
  return data;
};

export const listFonts = async () => {
  const { data } = await api.get('/fonts');
  return data.fonts as { name: string; path: string }[];
};