const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export async function getDashboardAnalytics() {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/summary`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard analytics");
  }

  return response.json();
}

export async function getExceptionTrends() {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/exception-trends`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch exception trends");
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

export async function getReconciliationRunDetails(runId) {
  const response = await fetch(
    `${API_BASE_URL}/reconciliation-runs/${runId}`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch reconciliation run details"
    );
  }

  return response.json();
}

export async function runReconciliation() {
  const response = await fetch(
    `${API_BASE_URL}/reconciliation-runs`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
      "Failed to run reconciliation"
    );
  }

  return response.json();
}