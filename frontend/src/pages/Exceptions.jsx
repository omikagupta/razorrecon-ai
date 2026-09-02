import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { useNavigate } from "react-router-dom";

import { getExceptions } from "../services/api.js";

function Exceptions() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState("ALL");
  const [severityFilter, setSeverityFilter] =
    useState("ALL");
  const [typeFilter, setTypeFilter] =
    useState("ALL");

  const [currentPage, setCurrentPage] =
    useState(1);

  const [pageSize, setPageSize] =
    useState(10);

  useEffect(() => {
    async function loadExceptions() {
      try {
        setError(null);

        /*
         * Fetch enough records for frontend
         * filtering and pagination.
         */
        const result = await getExceptions({
          page: 1,
          pageSize: 100,
        });

        setData(result);
      } catch (err) {
        setError(
          err?.message ||
            "Failed to load exceptions."
        );
      }
    }

    loadExceptions();
  }, []);

  /*
   * Backend response:
   *
   * {
   *   total,
   *   page,
   *   page_size,
   *   pages,
   *   exceptions: [...]
   * }
   */

  const exceptions = Array.isArray(
    data?.exceptions
  )
    ? data.exceptions
    : [];

  /*
   * Available exception types
   */

  const exceptionTypes = useMemo(() => {
    return [
      ...new Set(
        exceptions
          .map(
            (exception) =>
              exception?.exception_type
          )
          .filter(Boolean)
      ),
    ].sort();
  }, [exceptions]);

  /*
   * Filtering + Search
   */

  const filteredExceptions = useMemo(() => {
    const normalizedSearch =
      search.trim().toLowerCase();

    return exceptions.filter((exception) => {
      const exceptionId = String(
        exception?.exception_id || ""
      ).toLowerCase();

      const transactionId = String(
        exception?.transaction_id || ""
      ).toLowerCase();

      const exceptionType = String(
        exception?.exception_type || ""
      );

      const status = String(
        exception?.status || ""
      );

      const severity = String(
        exception?.severity || ""
      );

      const matchesSearch =
        !normalizedSearch ||
        exceptionId.includes(
          normalizedSearch
        ) ||
        transactionId.includes(
          normalizedSearch
        );

      const matchesStatus =
        statusFilter === "ALL" ||
        status === statusFilter;

      const matchesSeverity =
        severityFilter === "ALL" ||
        severity === severityFilter;

      const matchesType =
        typeFilter === "ALL" ||
        exceptionType === typeFilter;

      return (
        matchesSearch &&
        matchesStatus &&
        matchesSeverity &&
        matchesType
      );
    });
  }, [
    exceptions,
    search,
    statusFilter,
    severityFilter,
    typeFilter,
  ]);

  /*
   * Summary
   */

  const summary = useMemo(() => {
    return {
      total: exceptions.length,

      open: exceptions.filter(
        (exception) =>
          exception?.status === "OPEN"
      ).length,

      resolved: exceptions.filter(
        (exception) =>
          exception?.status === "RESOLVED"
      ).length,

      escalated: exceptions.filter(
        (exception) =>
          exception?.status === "ESCALATED"
      ).length,

      highRisk: exceptions.filter(
        (exception) =>
          exception?.severity === "HIGH" ||
          exception?.severity === "CRITICAL"
      ).length,
    };
  }, [exceptions]);

  /*
   * Pagination
   */

  const totalPages = Math.max(
    1,
    Math.ceil(
      filteredExceptions.length / pageSize
    )
  );

  const safeCurrentPage = Math.min(
    currentPage,
    totalPages
  );

  const startIndex =
    (safeCurrentPage - 1) *
    pageSize;

  const endIndex =
    startIndex + pageSize;

  const paginatedExceptions =
    filteredExceptions.slice(
      startIndex,
      endIndex
    );

  /*
   * Reset page when filters change.
   */

  useEffect(() => {
    setCurrentPage(1);
  }, [
    search,
    statusFilter,
    severityFilter,
    typeFilter,
    pageSize,
  ]);

  /*
   * Clear filters
   */

  function clearFilters() {
    setSearch("");
    setStatusFilter("ALL");
    setSeverityFilter("ALL");
    setTypeFilter("ALL");
    setCurrentPage(1);
  }

  /*
   * Open exception details
   */

  function openException(exceptionId) {
    if (!exceptionId) {
      return;
    }

    navigate(
      `/exceptions/${exceptionId}`
    );
  }

  /*
   * Date formatting
   */

  function formatDate(value) {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (
      Number.isNaN(date.getTime())
    ) {
      return value;
    }

    return date.toLocaleString(
      "en-IN",
      {
        dateStyle: "medium",
        timeStyle: "short",
      }
    );
  }

  /*
   * Confidence formatting
   */

  function formatConfidence(value) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "—";
    }

    const numericValue = Number(value);

    if (
      Number.isNaN(numericValue)
    ) {
      return value;
    }

    const percentage =
      numericValue <= 1
        ? numericValue * 100
        : numericValue;

    return `${percentage.toFixed(
      1
    )}%`;
  }

  /*
   * Error state
   */

  if (error) {
    return (
      <div className="placeholder-card">
        <h2>
          Unable to load exceptions
        </h2>

        <p>{error}</p>
      </div>
    );
  }

  /*
   * Loading state
   */

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
            Review financial reconciliation
            exceptions requiring
            investigation.
          </p>
        </div>
      </div>

      {/* Summary Cards */}

      <div className="summary-grid">
        <div className="summary-card">
          <span>
            Total Exceptions
          </span>

          <strong>
            {summary.total}
          </strong>
        </div>

        <div className="summary-card">
          <span>Open</span>

          <strong>
            {summary.open}
          </strong>
        </div>

        <div className="summary-card">
          <span>Resolved</span>

          <strong>
            {summary.resolved}
          </strong>
        </div>

        <div className="summary-card">
          <span>High Risk</span>

          <strong>
            {summary.highRisk}
          </strong>
        </div>
      </div>

      {/* Filters */}

      <div className="filters-card">
        {/* Search */}

        <div className="filter-group search-group">
          <label>Search</label>

          <input
            type="text"
            placeholder="Exception ID or Transaction ID"
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
          />
        </div>

        {/* Status */}

        <div className="filter-group">
          <label>Status</label>

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value
              )
            }
          >
            <option value="ALL">
              All
            </option>

            <option value="OPEN">
              Open
            </option>

            <option value="RESOLVED">
              Resolved
            </option>

            <option value="ESCALATED">
              Escalated
            </option>
          </select>
        </div>

        {/* Severity */}

        <div className="filter-group">
          <label>Severity</label>

          <select
            value={severityFilter}
            onChange={(event) =>
              setSeverityFilter(
                event.target.value
              )
            }
          >
            <option value="ALL">
              All
            </option>

            <option value="CRITICAL">
              Critical
            </option>

            <option value="HIGH">
              High
            </option>

            <option value="MEDIUM">
              Medium
            </option>

            <option value="LOW">
              Low
            </option>
          </select>
        </div>

        {/* Exception Type */}

        <div className="filter-group">
          <label>
            Exception Type
          </label>

          <select
            value={typeFilter}
            onChange={(event) =>
              setTypeFilter(
                event.target.value
              )
            }
          >
            <option value="ALL">
              All
            </option>

            {exceptionTypes.map(
              (type) => (
                <option
                  key={type}
                  value={type}
                >
                  {type}
                </option>
              )
            )}
          </select>
        </div>

        {/* Clear */}

        <div className="filter-group filter-action">
          <label>&nbsp;</label>

          <button
            type="button"
            className="secondary-button"
            onClick={
              clearFilters
            }
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Results */}

      <div className="table-card">
        <div className="table-header">
          <div>
            <h2>
              Exception Records
            </h2>

            <span>
              {filteredExceptions.length ===
              0
                ? "No matching exceptions"
                : `Showing ${
                    startIndex + 1
                  }–${Math.min(
                    endIndex,
                    filteredExceptions.length
                  )} of ${
                    filteredExceptions.length
                  }`}
            </span>
          </div>

          {/* Page size */}

          <div className="page-size-control">
            <label>Rows</label>

            <select
              value={pageSize}
              onChange={(event) =>
                setPageSize(
                  Number(
                    event.target.value
                  )
                )
              }
            >
              <option value={10}>
                10
              </option>

              <option value={25}>
                25
              </option>

              <option value={50}>
                50
              </option>
            </select>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  Exception ID
                </th>

                <th>
                  Transaction
                </th>

                <th>Type</th>

                <th>
                  Severity
                </th>

                <th>Status</th>

                <th>
                  Confidence
                </th>

                <th>Created</th>
              </tr>
            </thead>

            <tbody>
              {paginatedExceptions.length ===
              0 ? (
                <tr>
                  <td
                    colSpan="7"
                    className="empty-table-cell"
                  >
                    <div className="empty-state">
                      <strong>
                        No exceptions
                        found
                      </strong>

                      <p>
                        Try changing
                        your filters
                        or search
                        criteria.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedExceptions.map(
                  (exception) => (
                    <tr
                      key={
                        exception?.exception_id ||
                        `${exception?.transaction_id}-${exception?.created_at}`
                      }
                      className="clickable-row"
                      onClick={() =>
                        openException(
                          exception?.exception_id
                        )
                      }
                      title="Open exception details"
                    >
                      <td>
                        <strong>
                          {exception?.exception_id ||
                            "—"}
                        </strong>
                      </td>

                      <td>
                        {exception?.transaction_id ||
                          "—"}
                      </td>

                      <td>
                        {exception?.exception_type ||
                          "—"}
                      </td>

                      <td>
                        <span
                          className={`badge severity-${String(
                            exception?.severity ||
                              ""
                          ).toLowerCase()}`}
                        >
                          {exception?.severity ||
                            "UNKNOWN"}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`badge status-${String(
                            exception?.status ||
                              ""
                          ).toLowerCase()}`}
                        >
                          {exception?.status ||
                            "UNKNOWN"}
                        </span>
                      </td>

                      <td>
                        {formatConfidence(
                          exception?.confidence
                        )}
                      </td>

                      <td>
                        {formatDate(
                          exception?.created_at
                        )}
                      </td>
                    </tr>
                  )
                )
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}

        {filteredExceptions.length >
          0 && (
          <div className="pagination">
            <button
              type="button"
              className="secondary-button"
              disabled={
                safeCurrentPage === 1
              }
              onClick={() =>
                setCurrentPage(
                  (page) =>
                    Math.max(
                      1,
                      page - 1
                    )
                )
              }
            >
              ← Previous
            </button>

            <span>
              Page{" "}
              {safeCurrentPage} of{" "}
              {totalPages}
            </span>

            <button
              type="button"
              className="secondary-button"
              disabled={
                safeCurrentPage ===
                totalPages
              }
              onClick={() =>
                setCurrentPage(
                  (page) =>
                    Math.min(
                      totalPages,
                      page + 1
                    )
                )
              }
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Exceptions;