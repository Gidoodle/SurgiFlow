const API_BASE = "http://127.0.0.1:8000/api";

export async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("axiom_token")}`,
    },
  });

  if (!res.ok) {
    throw new Error("API error");
  }

  return res.json();
}
