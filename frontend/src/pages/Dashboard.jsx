import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, CheckCircle2, RefreshCw, ShieldAlert } from "lucide-react";

import { getDashboardAnalytics, runReconciliation } from "../services/api.js";

function percent(value) {
  return `${((Number(value) || 0) * 100).toFixed(1)}%`;
}

function number(value) {
  return Number(value || 0).toLocaleString("en-IN");
}

function currency(value) {
  return `INR ${Number(value || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function Dashboard() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);
  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);

  const loadDashboard = useCallback(async () => {
    try {
      setError(null);
      setAnalytics(await getDashboardAnalytics());
    } catch (err) {
      setError(err?.message || "Failed to load dashboard analytics.");
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  async function handleRunReconciliation() {
    try {
      setRunning(true);
      setError(null);
      setRunResult(await runReconciliation());
      await loadDashboard();
    } catch (err) {
      setError(err?.message || "Failed to run reconciliation.");
    } finally {
      setRunning(false);
    }
  }

  if (!analytics && !error) {
    return <div className="state-card">Loading reconciliation intelligence...</div>;
  }

  if (!analytics) {
    return (
      <div className="state-card error-state">
        <ShieldAlert size={36} />
        <div><h2>Unable to load dashboard</h2><p>{error}</p><button className="secondary-button" onClick={loadDashboard}>Try again</button></div>
      </div>
    );
  }

  const { transactions = {}, financials = {}, exceptions = {} } = analytics;
  const completedRun = runResult?.run;

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="eyebrow">OPERATIONS OVERVIEW</div>
          <h1>Reconciliation Intelligence</h1>
          <p>Monitor settlement health, financial exposure, and investigation workload.</p>
        </div>
        <div className="page-actions">
          <button className="icon-button" aria-label="Refresh dashboard" onClick={loadDashboard} disabled={running}><RefreshCw size={17} /></button>
          <button className="primary-button" onClick={handleRunReconciliation} disabled={running}>{running ? "Running reconciliation..." : "Run reconciliation"}</button>
        </div>
      </div>

      {error && <div className="alert-card alert-danger"><AlertTriangle size={19} /><span>{error}</span></div>}

      {completedRun && (
        <div className="alert-card alert-success run-notice">
          <CheckCircle2 size={20} />
          <div><strong>Reconciliation completed</strong><span>{number(completedRun.matched_records)} matched · {number(completedRun.exception_count)} exceptions</span></div>
          <button className="secondary-button" onClick={() => navigate(`/runs/${completedRun.run_id}`)}>View run</button>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card"><span>Financial exposure</span><h2>{currency(financials.total_difference)}</h2><small>Absolute unresolved variance</small></div>
        <div className="stat-card"><span>Open exceptions</span><h2>{number(exceptions.open)}</h2><small>{number(exceptions.high_severity)} high · {number(exceptions.critical_severity)} critical</small></div>
        <div className="stat-card"><span>Match rate</span><h2>{percent(transactions.match_rate)}</h2><small>{number(transactions.matched)} of {number(transactions.total)} transactions</small></div>
        <div className="stat-card"><span>Resolution rate</span><h2>{percent(exceptions.resolution_rate)}</h2><small>{number(exceptions.resolved)} resolved</small></div>
      </div>

      <div className="content-grid">
        <section className="panel-card">
          <div className="panel-header"><div><h2>Reconciliation health</h2><p>Current matching outcomes.</p></div><button className="secondary-button" onClick={() => navigate("/runs")}>View runs</button></div>
          <div className="severity-grid">
            <div className="severity-item"><span>Matched</span><strong>{number(transactions.matched)}</strong></div>
            <div className="severity-item"><span>Amount mismatch</span><strong>{number(transactions.amount_mismatch)}</strong></div>
            <div className="severity-item"><span>Missing settlement</span><strong>{number(transactions.missing_settlement)}</strong></div>
            <div className="severity-item"><span>Total expected</span><strong>{currency(financials.total_expected_amount)}</strong></div>
          </div>
        </section>
        <section className="panel-card">
          <div className="panel-header"><div><h2>Exception queue</h2><p>Prioritize unresolved settlement risk.</p></div><button className="secondary-button" onClick={() => navigate("/exceptions?status=OPEN")}>Review exceptions</button></div>
          <div className="summary-list">
            <div><span>Open</span><strong className="text-warning">{number(exceptions.open)}</strong></div>
            <div><span>Escalated</span><strong className="text-danger">{number(exceptions.escalated)}</strong></div>
            <div><span>Resolved</span><strong className="text-success">{number(exceptions.resolved)}</strong></div>
            <div className="summary-total"><span>Total exceptions</span><strong>{number(exceptions.total)}</strong></div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Dashboard;
