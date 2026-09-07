const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export function getToken() {
  return localStorage.getItem("aprg_token");
}

export function setSession(token, user) {
  localStorage.setItem("aprg_token", token);
  localStorage.setItem("aprg_user", JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem("aprg_token");
  localStorage.removeItem("aprg_user");
}

export function getUser() {
  const raw = localStorage.getItem("aprg_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    clearSession();
    return null;
  }
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatErrorDetail(error.detail || error.message || "Request failed"));
  }
  return response.json();
}

function formatErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const location = Array.isArray(item?.loc) ? item.loc.join(".") : "";
        return [location, item?.msg].filter(Boolean).join(": ") || JSON.stringify(item);
      })
      .join("\n");
  }
  if (detail && typeof detail === "object") return detail.msg || JSON.stringify(detail);
  return "Request failed";
}

function filenameFromDisposition(disposition) {
  const match = disposition?.match(/filename="?([^"]+)"?/i);
  return match?.[1] || null;
}

async function download(path, fallbackName) {
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Download failed");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filenameFromDisposition(response.headers.get("Content-Disposition")) || fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export const api = {
  register: (payload) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: async (email, password) => {
    const body = new URLSearchParams({ username: email, password });
    return request("/auth/login", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
  },
  projects: () => request("/projects"),
  createProject: (payload) => request("/projects", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (id, payload) => request(`/projects/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  project: (id) => request(`/projects/${id}`),
  upload: (id, form) => request(`/projects/${id}/files`, { method: "POST", body: form }),
  generate: (id) => request(`/projects/${id}/generate`, { method: "POST" }),
  job: (projectId, jobId) => request(`/projects/${projectId}/jobs/${jobId}`),
  editChapter: (id, payload) => request(`/projects/${id}/chapters`, { method: "PUT", body: JSON.stringify(payload) }),
  regenerateChapter: (id, payload) => request(`/projects/${id}/chapters/regenerate`, { method: "POST", body: JSON.stringify(payload) }),
  uploadKnowledge: (form) => request("/admin/knowledge-base", { method: "POST", body: form }),
  downloadReport: (projectId, fileId, filename) => download(`/projects/${projectId}/download/${fileId}`, filename)
};
