
import { useEffect, useMemo, useState } from "react";
import { getExceptions } from "../services/api.js";

function Exceptions() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");

  useEffect(() => {
    async function loadExceptions() {
      try {
        const result = await getExceptions();
        setData(result);
      } catch (err) {
        setError(err.message);
      }
    }

    loadExceptions();
  }, []);

  const exceptions = data?.exceptions || [];

  const filteredExceptions = useMemo(() => {
    return exceptions.filter((exception) => {
      const matchesStatus =
        statusFilter === "ALL" ||
        exception.status === statusFilter;

      const matchesSeverity =
        severityFilter === "ALL" ||
        exception.severity === severityFilter;

      const matchesType =
        typeFilter === "ALL" ||
        exception.exception_type === typeFilter;

      return matchesStatus && matchesSeverity && matchesType;
    });
  }, [exceptions, statusFilter, severityFilter, typeFilter]);

  const summary = useMemo(() => {
    return {
      total: exceptions.length,

      open: exceptions.filter(
        (exception) => exception.status === "OPEN"
      ).length,

      resolved: exceptions.filter(
        (exception) => exception.status === "RESOLVED"
      ).length,

      highRisk: exceptions.filter(
        (exception) =>
          exception.severity === "HIGH" ||
          exception.severity === "CRITICAL"
      ).length,
    };
  }, [exceptions]);

  const exceptionTypes = useMemo(() => {
    return [
      ...new Set(
        exceptions.map((exception) => exception.exception_type)
      ),
    ];
  }, [exceptions]);

  if (error) {
    return (
      <div className="placeholder-card">
        <h2>Unable to load exceptions</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="placeholder-card">
        Loading exceptions...
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>Exceptions</h1>
          <p>
            Review financial reconciliation exceptions requiring
            investigation.
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-grid">
        <div className="summary-card">
          <span>Total Exceptions</span>
          <strong>{summary.total}</strong>
        </div>

        <div className="summary-card">
          <span>Open</span>
          <strong>{summary.open}</strong>
        </div>

        <div className="summary-card">
          <span>Resolved</span>
          <strong>{summary.resolved}</strong>
        </div>

        <div className="summary-card">
          <span>High Risk</span>
          <strong>{summary.highRisk}</strong>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-card">
        <div className="filter-group">
          <label>Status</label>

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value)
            }
          >
            <option value="ALL">All</option>
            <option value="OPEN">Open</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Severity</label>

          <select
            value={severityFilter}
            onChange={(event) =>
              setSeverityFilter(event.target.value)
            }
          >
            <option value="ALL">All</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Exception Type</label>

          <select
            value={typeFilter}
            onChange={(event) =>
              setTypeFilter(event.target.value)
            }
          >
            <option value="ALL">All</option>

            {exceptionTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results */}
      <div className="table-card">
        <div className="table-header">
          <h2>Exception Records</h2>

          <span>
            Showing {filteredExceptions.length} of{" "}
            {exceptions.length}
          </span>
        </div>

        <table>
          <thead>
            <tr>
              <th>Exception ID</th>
              <th>Transaction</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {filteredExceptions.length === 0 ? (
              <tr>
                <td colSpan="5">
                  No exceptions match the selected filters.
                </td>
              </tr>
            ) : (
              filteredExceptions.map((exception) => (
                <tr key={exception.exception_id}>
                  <td>{exception.exception_id}</td>

                  <td>{exception.transaction_id}</td>

                  <td>{exception.exception_type}</td>

                  <td>
                    <span
                      className={`badge severity-${(
                        exception.severity || ""
                      ).toLowerCase()}`}
                    >
                      {exception.severity}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`badge status-${(
                        exception.status || ""
                      ).toLowerCase()}`}
                    >
                      {exception.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Exceptions;
