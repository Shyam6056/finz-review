const BASE = "http://127.0.0.1:8000";

async function handle(res) {
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  get: (path) => fetch(BASE + path).then(handle),
  post: (path, body) =>
    fetch(BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle),
  patch: (path, body) =>
    fetch(BASE + path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle),
  upload: (path, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(BASE + path, { method: "POST", body: fd }).then(handle);
  },
};
