const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

let authFailureHandler = null;

export function setAuthFailureHandler(handler) {
  authFailureHandler = handler;
}

export function getApiBase() {
  return API_BASE;
}

function getAccessToken() {
  return localStorage.getItem("daftar_access");
}

function getRefreshToken() {
  return localStorage.getItem("daftar_refresh");
}

export function saveTokens({ access, refresh }) {
  if (access) localStorage.setItem("daftar_access", access);
  if (refresh) localStorage.setItem("daftar_refresh", refresh);
}

export function clearTokens() {
  localStorage.removeItem("daftar_access");
  localStorage.removeItem("daftar_refresh");
}

function parseError(data) {
  if (!data) return "Request failed";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  const firstKey = Object.keys(data)[0];
  const firstValue = data[firstKey];
  if (Array.isArray(firstValue)) return firstValue[0];
  if (typeof firstValue === "string") return firstValue;
  return "Request failed";
}

async function readBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) {
    clearTokens();
    authFailureHandler?.();
    return false;
  }

  const data = await response.json();
  saveTokens({ access: data.access });
  return true;
}

export async function apiRequest(path, options = {}, retry = true) {
  const headers = new Headers(options.headers || {});
  const token = getAccessToken();
  let body = options.body;

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (body && !(body instanceof FormData) && typeof body === "object") {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body,
  });

  if (response.status === 401 && retry && !path.includes("/auth/token/")) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiRequest(path, options, false);
  }

  const data = await readBody(response);
  if (!response.ok) {
    throw new Error(parseError(data));
  }
  return data;
}
