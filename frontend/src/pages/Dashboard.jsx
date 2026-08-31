
import { useEffect, useState } from "react";
import {
  getDashboardAnalytics,
  runReconciliation,
} from "../services/api.js";

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);
  const [running, setRunning] = useState(false);
  const [runMessage, setRunMessage] = useState(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await getDashboardAnalytics();
        setAnalytics(data);
      } catch (err) {
        setError(err.message);
      }
    }

    loadDashboard();
  }, []);

  async function handleRunReconciliation() {
    try {
      setRunning(true);
      setError(null);
      setRunMessage(null);

      const result = await runReconciliation();

      setRunMessage(
        `Reconciliation completed: ${result.run.run_id}`
      );

      // Refresh dashboard analytics
      const updatedAnalytics =
        await getDashboardAnalytics();

      setAnalytics(updatedAnalytics);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  if (error && !analytics) {
    return (
      <div className="placeholder-card">
        <h2>Unable to load dashboard</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="placeholder-card">
        Loading reconciliation intelligence...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Reconciliation Intelligence</h1>
          <p>
            Monitor financial reconciliation operations and
            investigate transaction exceptions.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={handleRunReconciliation}
          disabled={running}
        >
          {running
            ? "Running Reconciliation..."
            : "Run Reconciliation"}
        </button>
      </div>

      {runMessage && (
        <div className="placeholder-card">
          <strong>{runMessage}</strong>
        </div>
      )}

      {error && (
        <div className="placeholder-card">
          <strong>Reconciliation failed</strong>
          <p>{error}</p>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <span>Total Exceptions</span>
          <h2>{analytics.total_exceptions}</h2>
        </div>

        <div className="stat-card">
          <span>Open Exceptions</span>
          <h2>{analytics.open_exceptions}</h2>
        </div>

        <div className="stat-card">
          <span>Resolution Rate</span>
          <h2>
            {(analytics.resolution_rate * 100).toFixed(1)}%
          </h2>
        </div>

        <div className="stat-card">
          <span>Financial Exposure</span>
          <h2>
            â‚¹ {analytics.financial_exposure}
          </h2>
        </div>
      </div>

      <div className="placeholder-card">
        <h2>Exception Severity Distribution</h2>

        <div className="severity-grid">
          {Object.entries(
            analytics.severity_distribution
          ).map(([severity, count]) => (
            <div
              className="severity-item"
              key={severity}
            >
              <span>{severity}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
