const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000/api/v1";

const REQUEST_TIMEOUT_MS = 15_000;

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS
  );

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...options.headers,
      },
    });
    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(
        payload?.detail?.message ||
          payload?.detail ||
          `Request failed (${response.status}).`
      );
    }

    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The request timed out. Please try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

function exceptionPath(params) {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 20),
  });

  if (params.status && params.status !== "ALL") query.set("status", params.status);
  if (params.severity && params.severity !== "ALL") query.set("severity", params.severity);
  if (params.exceptionType && params.exceptionType !== "ALL") {
    query.set("exception_type", params.exceptionType);
  }

  return `/exceptions?${query}`;
}

function requiredId(value, label) {
  if (!value) throw new Error(`${label} is required`);
  return encodeURIComponent(value);
}

export const getDashboardAnalytics = () => request("/dashboard/summary");
export const getExceptionTrends = () => request("/dashboard/exception-trends");
export const getExceptions = (params = {}) => request(exceptionPath(params));
export const getReconciliationRuns = () => request("/reconciliation-runs");
export const runReconciliation = () => request("/reconciliation-runs", {
  method: "POST",
});

export function getExceptionDetails(exceptionId) {
  return request(`/exceptions/${requiredId(exceptionId, "Exception ID")}`);
}

export function getInvestigationHistory(exceptionId) {
  return request(`/exceptions/${requiredId(exceptionId, "Exception ID")}/investigations`);
}

export function investigateException(exceptionId) {
  return request(`/exceptions/${requiredId(exceptionId, "Exception ID")}/investigate`, {
    method: "POST",
  });
}

export function reviewException(exceptionId, review) {
  if (!review) throw new Error("Review data is required");

  return request(`/exceptions/${requiredId(exceptionId, "Exception ID")}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(review),
  });
}

export function getReconciliationRunDetails(runId) {
  return request(`/reconciliation-runs/${requiredId(runId, "Run ID")}`);
}
