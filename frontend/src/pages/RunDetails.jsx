import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getReconciliationRunDetails } from "../services/api.js";

function RunDetails() {
  const { runId } = useParams();

  const [details, setDetails] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadRunDetails() {
      try {
        const data = await getReconciliationRunDetails(runId);
        setDetails(data);
      } catch (err) {
        setError(err.message);
      }
    }

    loadRunDetails();
  }, [runId]);

  if (error) {
    return (
      <div className="placeholder-card">
        <h2>Unable to load run details</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="placeholder-card">
        Loading reconciliation run details...
      </div>
    );
  }

  const { run, summary, status_distribution, results } = details;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Run Details</h1>
          <p>{run.run_id}</p>
        </div>

        <span className={`status-badge status-${run.status.toLowerCase()}`}>
          {run.status}
        </span>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Total Records</span>
          <h2>{run.total_records}</h2>
        </div>

        <div className="stat-card">
          <span>Matched Records</span>
          <h2>{run.matched_records}</h2>
        </div>

        <div className="stat-card">
          <span>Exceptions</span>
          <h2>{run.exception_count}</h2>
        </div>

        <div className="stat-card">
          <span>Financial Difference</span>
          <h2>₹ {summary.total_financial_difference}</h2>
        </div>
      </div>

      <div className="placeholder-card">
        <h2>Status Distribution</h2>

        <div className="severity-grid">
          {Object.entries(status_distribution).map(
            ([status, count]) => (
              <div className="severity-item" key={status}>
                <span>{status.replaceAll("_", " ")}</span>
                <strong>{count}</strong>
              </div>
            )
          )}
        </div>
      </div>

      <div className="table-card">
        <h2>Reconciliation Results</h2>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Status</th>
                <th>Expected</th>
                <th>Actual</th>
                <th>Difference</th>
                <th>Confidence</th>
              </tr>
            </thead>

            <tbody>
              {results.map((result) => (
                <tr key={result.transaction_id}>
                  <td>{result.transaction_id}</td>

                  <td>
                    <span className="status-badge">
                      {result.status.replaceAll("_", " ")}
                    </span>
                  </td>

                  <td>
                    ₹ {result.expected_amount ?? "-"}
                  </td>

                  <td>
                    ₹ {result.actual_amount ?? "-"}
                  </td>

                  <td>
                    ₹ {result.difference ?? "-"}
                  </td>

                  <td>
                    {result.match_confidence
                      ? `${(result.match_confidence * 100).toFixed(0)}%`
                      : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default RunDetails;