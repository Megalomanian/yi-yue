export async function api(path, options = {}) {
  const token = sessionStorage.getItem("iy-token");
  const headers = { ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    options = { ...options, body: JSON.stringify(options.body) };
  }
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (response.status === 401 && path != "/auth/login") {
      sessionStorage.removeItem("iy-token");
      window.dispatchEvent(new Event("iy-session-expired"));
    }
    throw new Error(body.message || `请求失败（${response.status}）`);
  }
  if (options.download) return response.blob();
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}
export async function download(path, name) {
  const blob = await api(path, { download: true });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export const post = (path, body = {}) => api(path, { method: "POST", body });
