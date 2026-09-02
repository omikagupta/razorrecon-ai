
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getDashboardAnalytics,
  runReconciliation,
} from "../services/api.js";

function Dashboard() {
  const navigate = useNavigate();

  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setError(null);

        const data = await getDashboardAnalytics();
        setAnalytics(data);
      } catch (err) {
        setError(
          err?.message || "Failed to load dashboard analytics."
        );
      }
    }

    loadDashboard();
  }, []);

  async function handleRunReconciliation() {
    try {
      setRunning(true);
      setError(null);
      setRunResult(null);

      const result = await runReconciliation();

      setRunResult(result);

      // Refresh dashboard analytics after reconciliation
      const updatedAnalytics =
        await getDashboardAnalytics();

      setAnalytics(updatedAnalytics);
    } catch (err) {
      setError(
        err?.message || "Failed to run reconciliation."
      );
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

  const transactions = analytics.transactions || {};
  const financials = analytics.financials || {};
  const exceptions = analytics.exceptions || {};

  const completedRun = runResult?.run || null;

  return (
    <div>
      {/* Page Header */}
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

      {/* Reconciliation Success */}
      {completedRun && (
        <div className="placeholder-card">
          <div className="section-header">
            <div>
              <h2>Reconciliation Completed</h2>

              <p>
                Run {completedRun.run_id} completed
                successfully.
              </p>
            </div>

            <span
              className={`badge status-${String(
                completedRun.status || ""
              ).toLowerCase()}`}
            >
              {completedRun.status || "COMPLETED"}
            </span>
          </div>

          <div className="severity-grid">
            <div className="severity-item">
              <span>Total Records</span>
              <strong>
                {completedRun.total_records ?? 0}
              </strong>
            </div>

            <div className="severity-item">
              <span>Matched</span>
              <strong>
                {completedRun.matched_records ?? 0}
              </strong>
            </div>

            <div className="severity-item">
              <span>Exceptions</span>
              <strong>
                {completedRun.exception_count ?? 0}
              </strong>
            </div>
          </div>

          <div
            style={{
              marginTop: "20px",
              display: "flex",
              gap: "12px",
              flexWrap: "wrap",
            }}
          >
            <button
              className="primary-button"
              onClick={() =>
                navigate(
                  `/runs/${completedRun.run_id}`
                )
              }
            >
              View Run Details
            </button>

            <button
              className="secondary-button"
              onClick={() => navigate("/exceptions")}
            >
              View Exceptions
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && analytics && (
        <div className="placeholder-card">
          <strong>Reconciliation failed</strong>

          <p>{error}</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <span>Total Exceptions</span>
          <h2>{exceptions.total ?? 0}</h2>
        </div>

        <div className="stat-card">
          <span>Open Exceptions</span>
          <h2>{exceptions.open ?? 0}</h2>
        </div>

        <div className="stat-card">
          <span>Resolution Rate</span>

          <h2>
            {(
              (exceptions.resolution_rate ?? 0) *
              100
            ).toFixed(1)}
            %
          </h2>
        </div>

        <div className="stat-card">
          <span>Financial Exposure</span>

          <h2>
            â‚¹{" "}
            {Number(
              financials.total_difference ?? 0
            ).toLocaleString("en-IN", {
              maximumFractionDigits: 2,
            })}
          </h2>
        </div>
      </div>

      {/* Transaction Overview */}
      <div className="placeholder-card">
        <h2>Transaction Overview</h2>

        <div className="severity-grid">
          <div className="severity-item">
            <span>Total Transactions</span>

            <strong>
              {transactions.total ?? 0}
            </strong>
          </div>

          <div className="severity-item">
            <span>Matched</span>

            <strong>
              {transactions.matched ?? 0}
            </strong>
          </div>

          <div className="severity-item">
            <span>Amount Mismatch</span>

            <strong>
              {transactions.amount_mismatch ?? 0}
            </strong>
          </div>

          <div className="severity-item">
            <span>Missing Settlement</span>

            <strong>
              {transactions.missing_settlement ?? 0}
            </strong>
          </div>

          <div className="severity-item">
            <span>Match Rate</span>

            <strong>
              {(
                (transactions.match_rate ?? 0) *
                100
              ).toFixed(1)}
              %
            </strong>
          </div>
        </div>
      </div>

      {/* Exception Severity Distribution */}
      <div className="placeholder-card">
        <h2>Exception Severity Distribution</h2>

        <div className="severity-grid">
          <div className="severity-item">
            <span>HIGH</span>

            <strong>
              {exceptions.high_severity ?? 0}
            </strong>
          </div>

          <div className="severity-item">
            <span>CRITICAL</span>

            <strong>
              {exceptions.critical_severity ?? 0}
            </strong>
          </div>
        </div>
      </div>

      {/* Exception Status */}
      <div className="placeholder-card">
        <h2>Exception Status</h2>

        <div className="severity-grid">
          <div className="severity-item">
            <span>OPEN</span>

            <strong>
              {exceptions.open ?? 0}
            </strong>
          </div>

          <div className="severity-item">
            <span>RESOLVED</span>

            <strong>
              {exceptions.resolved ?? 0}
            </strong>
          </div>

          <div className="severity-item">
            <span>ESCALATED</span>

            <strong>
              {exceptions.escalated ?? 0}
            </strong>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
