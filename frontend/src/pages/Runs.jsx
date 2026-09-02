
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getReconciliationRuns } from "../services/api.js";

function Runs() {
  const [runs, setRuns] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    async function loadRuns() {
      try {
        setLoading(true);
        setError(null);

        const data = await getReconciliationRuns();

        setRuns(
          Array.isArray(data?.runs)
            ? data.runs
            : []
        );
      } catch (err) {
        setError(
          err?.message ||
            "Failed to load reconciliation runs."
        );
      } finally {
        setLoading(false);
      }
    }

    loadRuns();
  }, []);

  function formatDate(value) {
    if (!value) {
      return "â€”";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "â€”";
    }

    return date.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  function calculateDuration(startedAt, completedAt) {
    if (!startedAt || !completedAt) {
      return "â€”";
    }

    const start = new Date(startedAt);
    const end = new Date(completedAt);

    if (
      Number.isNaN(start.getTime()) ||
      Number.isNaN(end.getTime())
    ) {
      return "â€”";
    }

    const durationMs = end.getTime() - start.getTime();

    if (durationMs < 0) {
      return "â€”";
    }

    const durationSeconds = durationMs / 1000;

    if (durationSeconds < 1) {
      return `${durationMs} ms`;
    }

    return `${durationSeconds.toFixed(2)} s`;
  }

  function calculateExceptionRate(run) {
    const total = Number(run?.total_records || 0);
    const exceptions = Number(
      run?.exception_count || 0
    );

    if (total <= 0) {
      return "0.0%";
    }

    return `${((exceptions / total) * 100).toFixed(1)}%`;
  }

  function getStatusClass(status) {
    return String(status || "UNKNOWN")
      .toLowerCase()
      .replace(/\s+/g, "-");
  }

  function handleViewDetails(runId) {
    if (!runId) {
      return;
    }

    navigate(`/runs/${runId}`);
  }

  if (loading) {
    return (
      <div className="placeholder-card">
        <h2>Loading reconciliation runs...</h2>
        <p>
          Retrieving reconciliation processing history.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="placeholder-card">
        <h2>Unable to load reconciliation runs</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>Reconciliation Runs</h1>

          <p>
            Review historical reconciliation processing
            runs and their outcomes.
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="summary-grid">
        <div className="summary-card">
          <span>Total Runs</span>
          <strong>{runs.length}</strong>
        </div>

        <div className="summary-card">
          <span>Completed</span>
          <strong>
            {
              runs.filter(
                (run) => run?.status === "COMPLETED"
              ).length
            }
          </strong>
        </div>

        <div className="summary-card">
          <span>Total Records Processed</span>
          <strong>
            {runs.reduce(
              (total, run) =>
                total +
                Number(run?.total_records || 0),
              0
            )}
          </strong>
        </div>

        <div className="summary-card">
          <span>Total Exceptions</span>
          <strong>
            {runs.reduce(
              (total, run) =>
                total +
                Number(run?.exception_count || 0),
              0
            )}
          </strong>
        </div>
      </div>

      {/* Runs Table */}
      {runs.length === 0 ? (
        <div className="placeholder-card">
          <h2>No reconciliation runs found</h2>

          <p>
            Run a reconciliation from the dashboard to
            create your first processing run.
          </p>
        </div>
      ) : (
        <div className="table-card">
          <div className="table-header">
            <div>
              <h2>Processing History</h2>

              <span>
                {runs.length} reconciliation{" "}
                {runs.length === 1 ? "run" : "runs"}
              </span>
            </div>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Status</th>
                  <th>Total Records</th>
                  <th>Matched</th>
                  <th>Exceptions</th>
                  <th>Exception Rate</th>
                  <th>Started</th>
                  <th>Completed</th>
                  <th>Duration</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {runs.map((run) => {
                  const runId = run?.run_id;

                  return (
                    <tr key={runId || Math.random()}>
                      <td>
                        <strong>
                          {runId || "â€”"}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={`badge status-${getStatusClass(
                            run?.status
                          )}`}
                        >
                          {run?.status || "UNKNOWN"}
                        </span>
                      </td>

                      <td>
                        {Number(
                          run?.total_records || 0
                        )}
                      </td>

                      <td>
                        {Number(
                          run?.matched_records || 0
                        )}
                      </td>

                      <td>
                        {Number(
                          run?.exception_count || 0
                        )}
                      </td>

                      <td>
                        {calculateExceptionRate(run)}
                      </td>

                      <td>
                        {formatDate(run?.started_at)}
                      </td>

                      <td>
                        {formatDate(
                          run?.completed_at
                        )}
                      </td>

                      <td>
                        {calculateDuration(
                          run?.started_at,
                          run?.completed_at
                        )}
                      </td>

                      <td>
                        <button
                          type="button"
                          className="secondary-button"
                          disabled={!runId}
                          onClick={() =>
                            handleViewDetails(runId)
                          }
                        >
                          View Details â†’
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Runs;
