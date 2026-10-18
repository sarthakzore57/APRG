const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000/api" : "https://gaai-aprg-backend-0xoy.onrender.com/api");

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

export async function checkServerHealth(timeoutMs = 6000) {
  const rootUrl = API_URL.replace(/\/api\/?$/, "");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${rootUrl}/health`, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timer);
    return res.ok;
  } catch {
    clearTimeout(timer);
    return false;
  }
}

export function warmupBackend() {
  const rootUrl = API_URL.replace(/\/api\/?$/, "");
  fetch(`${rootUrl}/health`, { method: "GET", cache: "no-store" }).catch(() => {});
}

async function request(path, options = {}) {
  const { maxRetries = (options.method === "POST" && !path.startsWith("/auth/") ? 0 : 2), timeoutMs = 120000, onRetry, ...fetchOptions } = options;
  let attempt = 0;

  while (attempt <= maxRetries) {
    attempt++;
    const headers = new Headers(fetchOptions.headers || {});
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (fetchOptions.body && !(fetchOptions.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${API_URL}${path}`, {
        ...fetchOptions,
        headers,
        signal: fetchOptions.signal || controller.signal,
      });
      clearTimeout(timeoutId);

      // Render edge proxy returns 502/503/504 while spinning up free instances
      if ([502, 503, 504].includes(response.status) && attempt <= maxRetries) {
        if (onRetry) onRetry(attempt, maxRetries);
        await new Promise((r) => setTimeout(r, 2500));
        continue;
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(formatErrorDetail(error.detail || error.message || "Request failed"));
      }
      return await response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      const isNetworkOrTimeout =
        err.name === "AbortError" ||
        err.message === "Failed to fetch" ||
        err.message.toLowerCase().includes("networkerror");

      if (isNetworkOrTimeout && attempt <= maxRetries) {
        if (onRetry) onRetry(attempt, maxRetries);
        await new Promise((r) => setTimeout(r, 3000));
        continue;
      }

      if (err.name === "AbortError") {
        throw new Error("Request timed out. The free Render backend may still be spinning up; please wait a moment and try again.");
      }
      if (err.message === "Failed to fetch" || err.message.toLowerCase().includes("networkerror")) {
        throw new Error("Unable to connect to the backend server. The cloud server may be waking up from sleep (Render free tier), or check your network.");
      }
      throw err;
    }
  }
}

function formatErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const location = Array.isArray(item?.loc) ? item.loc.join(".") : "";
        if (location.includes("project_id")) {
          return "Please save your project details on Page 1 (Project Specs) first before attaching materials or running generation.";
        }
        return [location, item?.msg].filter(Boolean).join(": ") || JSON.stringify(item);
      })
      .join("\n");
  }
  if (detail && typeof detail === "object") {
    if (detail.loc && Array.isArray(detail.loc) && detail.loc.join(".").includes("project_id")) {
      return "Please save your project details on Page 1 (Project Specs) first before attaching materials or running generation.";
    }
    return detail.msg || JSON.stringify(detail);
  }
  return "Request failed";
}

function validateProjectId(id) {
  const num = Number(id);
  if (!id || isNaN(num) || num <= 0 || !Number.isInteger(num)) {
    throw new Error("Please save your project specification sheet on Page 1 first before proceeding.");
  }
  return num;
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
  register: (payload, options = {}) => {
    const cleanPayload = {
      ...payload,
      email: (payload.email || "").trim().toLowerCase(),
      full_name: (payload.full_name || "").trim(),
    };
    return request("/auth/register", { method: "POST", body: JSON.stringify(cleanPayload), ...options });
  },
  login: async (email, password, options = {}) => {
    const cleanEmail = (email || "").trim().toLowerCase();
    const cleanPassword = (password || "").trim();
    const body = new URLSearchParams({ username: cleanEmail, password: cleanPassword });
    return request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
      timeoutMs: 120000,
      maxRetries: 2,
      ...options,
    });
  },
  resetPassword: (payload, options = {}) => {
    const cleanPayload = {
      email: (payload.email || "").trim().toLowerCase(),
      new_password: (payload.new_password || payload.password || "").trim(),
    };
    return request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(cleanPayload),
      timeoutMs: 120000,
      maxRetries: 2,
      ...options,
    });
  },
  projects: () => request("/projects"),
  templates: () => request("/projects/templates"),
  createProject: (payload) => request("/projects", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (id, payload) => request(`/projects/${validateProjectId(id)}`, { method: "PUT", body: JSON.stringify(payload) }),
  project: (id) => request(`/projects/${validateProjectId(id)}`),
  upload: (id, form) => request(`/projects/${validateProjectId(id)}/files`, { method: "POST", body: form }),
  generate: (id) => request(`/projects/${validateProjectId(id)}/generate`, { method: "POST", timeoutMs: 180000 }),
  job: (projectId, jobId) => request(`/projects/${validateProjectId(projectId)}/jobs/${jobId}`),
  editChapter: (id, payload) => request(`/projects/${validateProjectId(id)}/chapters`, { method: "PUT", body: JSON.stringify(payload) }),
  uploadKnowledge: (form) => request("/admin/knowledge-base", { method: "POST", body: form }),
  adminKnowledgeBase: () => request("/admin/knowledge-base"),
  deleteKnowledge: (id) => request(`/admin/knowledge-base/${id}`, { method: "DELETE" }),
  adminStats: () => request("/admin/stats"),
  adminProjects: () => request("/admin/projects"),
  downloadReport: (projectId, fileId, filename) => download(`/projects/${validateProjectId(projectId)}/download/${fileId}`, filename)
};
