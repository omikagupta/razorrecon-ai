const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export async function getDashboardAnalytics() {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/analytics`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard analytics");
  }

  return response.json();
}

export async function getExceptions() {
  const response = await fetch(
    `${API_BASE_URL}/exceptions`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch exceptions");
  }

  return response.json();
}

export async function getReconciliationRuns() {
  const response = await fetch(
    `${API_BASE_URL}/reconciliation-runs`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch reconciliation runs");
  }

  return response.json();
}