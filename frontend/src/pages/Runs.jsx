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
        const data = await getReconciliationRuns();
        setRuns(data.runs || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadRuns();
  }, []);

  if (loading) {
    return (
      <div className="placeholder-card">
        Loading reconciliation runs...
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
      <div className="page-header">
        <div>
          <h1>Reconciliation Runs</h1>
          <p>
            Historical reconciliation processing runs.
          </p>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="placeholder-card">
          <h2>No reconciliation runs found</h2>
          <p>
            Run a reconciliation from the dashboard to see
            processing history here.
          </p>
        </div>
      ) : (
        <div className="table-card">
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Status</th>
                  <th>Total Records</th>
                  <th>Matched</th>
                  <th>Exceptions</th>
                  <th>Started At</th>
                </tr>
              </thead>

              <tbody>
                {runs.map((run) => (
                  <tr
                    key={run.run_id}
                    className="clickable-row"
                    onClick={() =>
                      navigate(`/runs/${run.run_id}`)
                    }
                  >
                    <td>{run.run_id}</td>

                    <td>
                      <span
                        className={`status-badge status-${run.status.toLowerCase()}`}
                      >
                        {run.status}
                      </span>
                    </td>

                    <td>{run.total_records}</td>

                    <td>{run.matched_records}</td>

                    <td>{run.exception_count}</td>

                    <td>
                      {run.started_at
                        ? new Date(
                            run.started_at
                          ).toLocaleString()
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Runs;