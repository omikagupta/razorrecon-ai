import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock3,
  FileWarning,
  TrendingUp,
} from "lucide-react";

import { getReconciliationRunDetails } from "../services/api.js";

function formatCurrency(value) {
  if (value === null || value === undefined || value === "") {
    return "₹0.00";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return `₹${value}`;
  }

  return `₹${number.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatDate(value) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatStatus(status) {
  if (!status) {
    return "-";
  }

  return status.replaceAll("_", " ");
}

function getStatusClass(status) {
  switch (status) {
    case "MATCHED":
      return "status-matched";

    case "AMOUNT_MISMATCH":
      return "status-mismatch";

    case "MISSING_SETTLEMENT":
      return "status-missing";

    case "CURRENCY_MISMATCH":
      return "status-currency";

    case "COMPLETED":
      return "status-completed";

    case "RUNNING":
      return "status-running";

    case "FAILED":
      return "status-failed";

    default:
      return "status-default";
  }
}

function RunDetails() {
  const { runId } = useParams();
  const navigate = useNavigate();

  const [details, setDetails] = useState(null);
  const [error, setError] = useState(null);
  const [resultFilter, setResultFilter] = useState("ALL");

  useEffect(() => {
    async function loadRunDetails() {
      try {
        setError(null);

        const data = await getReconciliationRunDetails(runId);

        setDetails(data);
      } catch (err) {
        setError(err.message);
      }
    }

    loadRunDetails();
  }, [runId]);

  const filteredResults = useMemo(() => {
    if (!details?.results) {
      return [];
    }

    if (resultFilter === "ALL") {
      return details.results;
    }

    return details.results.filter(
      (result) => result.status === resultFilter
    );
  }, [details, resultFilter]);

  if (error) {
    return (
      <div className="state-card error-state">
        <XCircle size={42} />

        <div>
          <h2>Unable to load run</h2>
          <p>{error}</p>

          <button
            className="secondary-button"
            onClick={() => navigate("/runs")}
          >
            <ArrowLeft size={17} />
            Back to Runs
          </button>
        </div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="state-card">
        <Clock3 size={38} />
        <div>
          <h2>Loading reconciliation run</h2>
          <p>Fetching run analytics and reconciliation results...</p>
        </div>
      </div>
    );
  }

  const {
    run,
    summary,
    status_distribution = {},
    results = [],
  } = details;

  const matchRate =
    run.total_records > 0
      ? ((run.matched_records / run.total_records) * 100).toFixed(1)
      : "0.0";

  const exceptionRate =
    run.total_records > 0
      ? ((run.exception_count / run.total_records) * 100).toFixed(1)
      : "0.0";

  return (
    <div className="run-details-page">

      {/* Back */}
      <button
        className="back-button"
        onClick={() => navigate("/runs")}
      >
        <ArrowLeft size={17} />
        Back to Reconciliation Runs
      </button>

      {/* Header */}
      <div className="page-header run-details-header">
        <div>
          <div className="eyebrow">
            RECONCILIATION RUN
          </div>

          <h1>{run.run_id}</h1>

          <p>
            Detailed reconciliation analysis and transaction results.
          </p>
        </div>

        <span
          className={`status-badge ${getStatusClass(run.status)}`}
        >
          {run.status}
        </span>
      </div>

      {/* Run Metadata */}
      <div className="run-meta-card">

        <div className="meta-item">
          <span>Started</span>
          <strong>{formatDate(run.started_at)}</strong>
        </div>

        <div className="meta-item">
          <span>Completed</span>
          <strong>{formatDate(run.completed_at)}</strong>
        </div>

        <div className="meta-item">
          <span>Match Rate</span>
          <strong>{matchRate}%</strong>
        </div>

        <div className="meta-item">
          <span>Exception Rate</span>
          <strong>{exceptionRate}%</strong>
        </div>

      </div>

      {/* KPI Cards */}
      <div className="stats-grid">

        <div className="stat-card">
          <div className="stat-icon">
            <FileWarning size={21} />
          </div>

          <span>Total Records</span>

          <h2>
            {run.total_records.toLocaleString("en-IN")}
          </h2>

          <small>
            Records processed
          </small>
        </div>

        <div className="stat-card success-card">
          <div className="stat-icon">
            <CheckCircle2 size={21} />
          </div>

          <span>Matched Records</span>

          <h2>
            {run.matched_records.toLocaleString("en-IN")}
          </h2>

          <small>
            {matchRate}% successfully matched
          </small>
        </div>

        <div className="stat-card warning-card">
          <div className="stat-icon">
            <AlertTriangle size={21} />
          </div>

          <span>Exceptions</span>

          <h2>
            {run.exception_count.toLocaleString("en-IN")}
          </h2>

          <small>
            {exceptionRate}% require investigation
          </small>
        </div>

        <div className="stat-card danger-card">
          <div className="stat-icon">
            <TrendingUp size={21} />
          </div>

          <span>Financial Difference</span>

          <h2>
            {formatCurrency(
              summary.total_financial_difference
            )}
          </h2>

          <small>
            Total identified variance
          </small>
        </div>

      </div>

      {/* Status Distribution */}
      <div className="content-grid">

        <div className="panel-card">
          <div className="panel-header">
            <div>
              <h2>Status Distribution</h2>
              <p>
                Breakdown of reconciliation outcomes.
              </p>
            </div>
          </div>

          <div className="distribution-list">

            {Object.entries(status_distribution).map(
              ([status, count]) => {

                const percentage =
                  run.total_records > 0
                    ? ((count / run.total_records) * 100).toFixed(1)
                    : "0.0";

                return (
                  <div
                    className="distribution-item"
                    key={status}
                  >
                    <div className="distribution-top">

                      <div className="distribution-label">
                        <span
                          className={`distribution-dot ${getStatusClass(
                            status
                          )}`}
                        />

                        <span>
                          {formatStatus(status)}
                        </span>
                      </div>

                      <strong>
                        {count.toLocaleString("en-IN")}
                      </strong>

                    </div>

                    <div className="progress-track">
                      <div
                        className={`progress-bar ${getStatusClass(
                          status
                        )}`}
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>

                    <span className="distribution-percentage">
                      {percentage}%
                    </span>
                  </div>
                );
              }
            )}

          </div>
        </div>

        {/* Summary */}
        <div className="panel-card">
          <div className="panel-header">
            <div>
              <h2>Reconciliation Summary</h2>
              <p>
                Financial and matching overview.
              </p>
            </div>
          </div>

          <div className="summary-list">

            <div>
              <span>Total Results</span>
              <strong>
                {summary.total_results}
              </strong>
            </div>

            <div>
              <span>Matched</span>
              <strong className="text-success">
                {summary.matched}
              </strong>
            </div>

            <div>
              <span>Amount Mismatch</span>
              <strong className="text-warning">
                {summary.amount_mismatch}
              </strong>
            </div>

            <div>
              <span>Missing Settlement</span>
              <strong className="text-danger">
                {summary.missing_settlement}
              </strong>
            </div>

            <div>
              <span>Currency Mismatch</span>
              <strong>
                {summary.currency_mismatch}
              </strong>
            </div>

            <div className="summary-total">
              <span>Total Financial Difference</span>
              <strong>
                {formatCurrency(
                  summary.total_financial_difference
                )}
              </strong>
            </div>

          </div>
        </div>

      </div>

      {/* Results */}
      <div className="panel-card results-panel">

        <div className="panel-header results-header">

          <div>
            <h2>Transaction Results</h2>

            <p>
              {filteredResults.length.toLocaleString("en-IN")}{" "}
              records displayed
            </p>
          </div>

          <select
            value={resultFilter}
            onChange={(event) =>
              setResultFilter(event.target.value)
            }
            className="result-filter"
          >
            <option value="ALL">All Results</option>
            <option value="MATCHED">Matched</option>
            <option value="AMOUNT_MISMATCH">
              Amount Mismatch
            </option>
            <option value="MISSING_SETTLEMENT">
              Missing Settlement
            </option>
            <option value="CURRENCY_MISMATCH">
              Currency Mismatch
            </option>
          </select>

        </div>

        <div className="table-wrapper">

          <table className="professional-table">

            <thead>
              <tr>
                <th>Transaction</th>
                <th>Status</th>
                <th>Expected</th>
                <th>Actual</th>
                <th>Difference</th>
                <th>Match Method</th>
                <th>Confidence</th>
              </tr>
            </thead>

            <tbody>

              {filteredResults.length === 0 ? (
                <tr>
                  <td
                    colSpan="7"
                    className="empty-table"
                  >
                    No reconciliation results found.
                  </td>
                </tr>
              ) : (
                filteredResults.map((result) => (

                  <tr key={result.transaction_id}>

                    <td>
                      <strong className="transaction-id">
                        {result.transaction_id}
                      </strong>
                    </td>

                    <td>
                      <span
                        className={`status-badge ${getStatusClass(
                          result.status
                        )}`}
                      >
                        {formatStatus(result.status)}
                      </span>
                    </td>

                    <td>
                      {formatCurrency(
                        result.expected_amount
                      )}
                    </td>

                    <td>
                      {formatCurrency(
                        result.actual_amount
                      )}
                    </td>

                    <td>
                      <span
                        className={
                          Number(result.difference) > 0
                            ? "difference-negative"
                            : "difference-zero"
                        }
                      >
                        {formatCurrency(
                          result.difference
                        )}
                      </span>
                    </td>

                    <td>
                      <span className="match-method">
                        {result.match_method || "-"}
                      </span>
                    </td>

                    <td>
                      {result.match_confidence !== null &&
                      result.match_confidence !== undefined
                        ? `${(
                            result.match_confidence * 100
                          ).toFixed(0)}%`
                        : "-"}
                    </td>

                  </tr>

                ))
              )}

            </tbody>

          </table>

        </div>

      </div>

    </div>
  );
}

export default RunDetails;