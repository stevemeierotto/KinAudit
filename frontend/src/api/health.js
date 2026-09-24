const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchHealthReady() {
  const response = await fetch(`${API_BASE_URL}/health/ready`);
  const body = await response.json();
  return { statusCode: response.status, body };
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}
