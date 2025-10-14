import { API_BASE } from "./config";

export async function apiFetch<T = any>(path: string, init?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export async function buildIndexAPI(pdfFiles: File[], indexName: string): Promise<any> {
  const formData = new FormData();
  
  // Append files to FormData
  pdfFiles.forEach((file) => {
    formData.append("files", file, file.name); // Backend expects "files" as the key
  });

  // Append index name
  formData.append("index_name", indexName);

  try {
    const response = await apiFetch("/api/build_index", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json;
      throw new Error(error.detail || "Failed to build index");
    }

    return await response.json; // Return the response to the caller
  } catch (error) {
    console.error("Error calling buildIndexAPI:", error);
    throw error; // Propagate the error to the caller
  }
}