const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000/api/v1";

/*
|--------------------------------------------------------------------------
| Dashboard
|--------------------------------------------------------------------------
*/

export async function getDashboardAnalytics() {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/summary`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch dashboard analytics"
    );
  }

  return response.json();
}

export async function getExceptionTrends() {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/exception-trends`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch exception trends"
    );
  }

  return response.json();
}

/*
|--------------------------------------------------------------------------
| Exceptions
|--------------------------------------------------------------------------
*/

export async function getExceptions({
  page = 1,
  pageSize = 100,
  status = null,
  severity = null,
  exceptionType = null,
} = {}) {
  const params = new URLSearchParams();

  params.set("page", page);
  params.set("page_size", pageSize);

  if (status && status !== "ALL") {
    params.set("status", status);
  }

  if (severity && severity !== "ALL") {
    params.set("severity", severity);
  }

  if (exceptionType && exceptionType !== "ALL") {
    params.set(
      "exception_type",
      exceptionType
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/exceptions?${params.toString()}`
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        "Failed to fetch exceptions"
    );
  }

  return response.json();
}

export async function getExceptionDetails(
  exceptionId
) {
  if (!exceptionId) {
    throw new Error(
      "Exception ID is required"
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/exceptions/${encodeURIComponent(
      exceptionId
    )}`
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        "Failed to fetch exception details"
    );
  }

  return response.json();
}

export async function getInvestigationHistory(
  exceptionId
) {
  if (!exceptionId) {
    throw new Error(
      "Exception ID is required"
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/exceptions/${encodeURIComponent(
      exceptionId
    )}/investigations`
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        "Failed to fetch investigation history"
    );
  }

  return response.json();
}

/*
|--------------------------------------------------------------------------
| AI Investigation
|--------------------------------------------------------------------------
*/

export async function investigateException(
  exceptionId
) {
  if (!exceptionId) {
    throw new Error(
      "Exception ID is required"
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/exceptions/${encodeURIComponent(
      exceptionId
    )}/investigate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        errorData?.detail ||
        "Failed to investigate exception"
    );
  }

  return response.json();
}

/*
|--------------------------------------------------------------------------
| Human Review
|--------------------------------------------------------------------------
*/

export async function reviewException(
  exceptionId,
  review
) {
  if (!exceptionId) {
    throw new Error(
      "Exception ID is required"
    );
  }

  if (!review) {
    throw new Error(
      "Review data is required"
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/exceptions/${encodeURIComponent(
      exceptionId
    )}/review`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(review),
    }
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        errorData?.detail ||
        "Failed to submit human review"
    );
  }

  return response.json();
}

/*
|--------------------------------------------------------------------------
| Reconciliation Runs
|--------------------------------------------------------------------------
*/

export async function getReconciliationRuns() {
  const response = await fetch(
    `${API_BASE_URL}/reconciliation-runs`
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        "Failed to fetch reconciliation runs"
    );
  }

  return response.json();
}

export async function getReconciliationRunDetails(
  runId
) {
  if (!runId) {
    throw new Error(
      "Run ID is required"
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/reconciliation-runs/${encodeURIComponent(
      runId
    )}`
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
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
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => null);

    throw new Error(
      errorData?.detail?.message ||
        errorData?.detail ||
        "Failed to run reconciliation"
    );
  }

  return response.json();
}