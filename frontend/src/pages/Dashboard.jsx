import { useEffect, useState } from "react";
import { getDashboardAnalytics } from "../services/api.js";

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

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

  if (error) {
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

        <button className="primary-button">
          Run Reconciliation
        </button>
      </div>

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
          <h2>₹ {analytics.financial_exposure}</h2>
        </div>
      </div>

      <div className="placeholder-card">
        <h2>Exception Severity Distribution</h2>

        <div className="severity-grid">
          {Object.entries(
            analytics.severity_distribution
          ).map(([severity, count]) => (
            <div className="severity-item" key={severity}>
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