const BASE_URL = import.meta.env.VITE_DECKING_ENGINE_API_URL || "http://localhost:8000";

export async function fetchYardState() {
  const response = await fetch(`${BASE_URL}/api/yard`);
  if (!response.ok) {
    throw new Error(`Failed to fetch yard state: ${response.status}`);
  }
  const body = await response.json();
  return body.slots;
}

export async function fetchAlerts(sinceId = 0) {
  const response = await fetch(`${BASE_URL}/api/alerts?sinceId=${sinceId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch alerts: ${response.status}`);
  }
  return response.json();
}

export async function fetchEfficiencyIndex() {
  const response = await fetch(`${BASE_URL}/api/yard/efficiency-index`);
  if (!response.ok) {
    throw new Error(`Failed to fetch efficiency index: ${response.status}`);
  }
  return response.json();
}

export async function fetchVesselState() {
  const response = await fetch(`${BASE_URL}/api/vessel`);
  if (!response.ok) {
    throw new Error(`Failed to fetch vessel state: ${response.status}`);
  }
  const body = await response.json();
  return body.slots;
}

export async function fetchVesselStability() {
  const response = await fetch(`${BASE_URL}/api/vessel/stability`);
  if (!response.ok) {
    throw new Error(`Failed to fetch vessel stability: ${response.status}`);
  }
  return response.json();
}
