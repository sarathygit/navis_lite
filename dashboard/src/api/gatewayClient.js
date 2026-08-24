const BASE_URL = import.meta.env.VITE_GATEWAY_API_URL || "http://localhost:8080";

export async function fetchTransactions() {
  const response = await fetch(`${BASE_URL}/api/gate/transactions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch transactions: ${response.status}`);
  }
  return response.json();
}

export async function checkInContainer(payload) {
  const response = await fetch(`${BASE_URL}/api/gate/check-in`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.error || "Check-in failed");
    error.details = body.details;
    error.status = response.status;
    throw error;
  }
  return body;
}

export async function checkOutContainer(containerId) {
  const response = await fetch(`${BASE_URL}/api/gate/check-out`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ containerId }),
  });
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.error || "Check-out failed");
    error.details = body.details;
    error.status = response.status;
    throw error;
  }
  return body;
}

export async function applyHold(containerId, holdType, reason) {
  const response = await fetch(`${BASE_URL}/api/gate/${containerId}/hold`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ holdType, reason }),
  });
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.error || "Applying hold failed");
    error.details = body.details;
    error.status = response.status;
    throw error;
  }
  return body;
}

export async function clearHold(containerId) {
  const response = await fetch(`${BASE_URL}/api/gate/${containerId}/hold`, {
    method: "DELETE",
  });
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.error || "Clearing hold failed");
    error.details = body.details;
    error.status = response.status;
    throw error;
  }
  return body;
}

export async function downloadEdiManifest() {
  const response = await fetch(`${BASE_URL}/api/manifest/export-edi`);
  if (!response.ok) {
    throw new Error(`Failed to export EDI manifest: ${response.status}`);
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : "baplie_manifest.edi";

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function fetchEquipment() {
  const response = await fetch(`${BASE_URL}/api/equipment`);
  if (!response.ok) {
    throw new Error(`Failed to fetch equipment: ${response.status}`);
  }
  return response.json();
}

export async function fetchWorkInstructions() {
  const response = await fetch(`${BASE_URL}/api/work-instructions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch work instructions: ${response.status}`);
  }
  return response.json();
}

export async function loadToVessel(containerId, bay, row, tier) {
  const response = await fetch(`${BASE_URL}/api/gate/load-to-vessel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ containerId, bay, row, tier }),
  });
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.error || "Load to vessel failed");
    error.details = body.details;
    error.status = response.status;
    throw error;
  }
  return body;
}
