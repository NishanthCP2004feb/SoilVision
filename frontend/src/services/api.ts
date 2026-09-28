import type { AiSuggestions, Analysis, ApiResponse, ChatResponse, HistoryItem, Recommendation } from "../types/api";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
let token = localStorage.getItem("soil_token") ?? "";
export const session = {
  get: () => token,
  set: (value: string) => { token = value; localStorage.setItem("soil_token", value); },
  clear: () => { token = ""; localStorage.removeItem("soil_token"); },
};

async function request<T>(path: string, init: RequestInit = {}): Promise<ApiResponse<T>> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  const body = await response.json() as ApiResponse<T> & { detail?: string };
  if (!response.ok) throw new Error(typeof body.error === "string" ? body.error : body.detail ?? body.message ?? "Request failed");
  return body;
}

export const api = {
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () =>
    request<{ message: string }>("/auth/logout", { method: "POST" }),
  analyze: (file: File) => {
    const form = new FormData();
    form.append("upload", file);
    return request<Analysis>("/soil/analyze", { method: "POST", body: form });
  },
  explanation: async (analysisId: string) => {
    const response = await fetch(`${baseUrl}/soil/analyses/${analysisId}/explanation`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Model explanation is unavailable");
    return response.blob();
  },
  addProperty: (analysisId: string, name: string, value: number, unit: string) =>
    request<{ id: string }>(`/soil/analyses/${analysisId}/properties`, {
      method: "POST",
      body: JSON.stringify({ name, value, unit, source: "USER_PROVIDED" }),
    }),
  recommend: (soil_type: string, season: string, properties: unknown[] = []) =>
    request<Recommendation[]>("/recommendations", {
      method: "POST",
      body: JSON.stringify({ soil_type, season, properties }),
    }),
  history: () => request<HistoryItem[]>("/soil/analyses"),
  aiSuggestions: (soil_type: string, season: string, properties: unknown[] = []) =>
    request<AiSuggestions>("/ai-suggestions", {
      method: "POST",
      body: JSON.stringify({ soil_type, season, properties }),
    }),
  analysisDetail: (id: string) => request<Record<string, unknown>>(`/soil/analyses/${id}`),
  crops: () => request<unknown[]>("/crops"),
  chat: (message: string, language: string, analysisContext?: unknown, conversationHistory?: unknown[]) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        language,
        analysis_context: analysisContext ?? null,
        conversation_history: conversationHistory ?? [],
      }),
    }),
  chatLanguages: () => request<Record<string, string>>("/chat/languages"),
  health: () => request<Record<string, unknown>>("/health"),
};
