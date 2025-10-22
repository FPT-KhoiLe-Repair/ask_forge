import { API_BASE } from "../../lib/config";

export async function apiFetch<T = any>(path: string, init?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

// LƯU Ý: KHÔNG set 'Content-Type' khi gửi FormData
export async function buildIndexAPI(pdfFiles: File[], indexName: string) {
  const formData = new FormData();
  pdfFiles.forEach((file) => formData.append("files", file, file.name));
  formData.append("index_name", indexName);
  return apiFetch("/api/build_index", { method: "POST", body: formData });
}

export async function addToIndexAPI(pdfFiles: File[], indexName: string) {
  const formData = new FormData();
  pdfFiles.forEach((file) => formData.append("files", file, file.name));
  formData.append("index_name", indexName);
  return apiFetch("/api/add_to_index", { method: "POST", body: formData });
}