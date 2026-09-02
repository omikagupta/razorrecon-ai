
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getExceptionDetails,
  investigateException,
  reviewException,
} from "../services/api.js";

function ExceptionDetails() {
  const { exceptionId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const [investigating, setInvestigating] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [reviewMessage, setReviewMessage] = useState(null);

  useEffect(() => {
    async function loadException() {
      try {
        setError(null);

        const result = await getExceptionDetails(exceptionId);
        setData(result);
      } catch (err) {
        setError(
          err?.message || "Failed to load exception details."
        );
      }
    }

    loadException();
  }, [exceptionId]);

  async function handleInvestigation() {
    try {
      setInvestigating(true);
      setError(null);
      setReviewMessage(null);

      const result = await investigateException(exceptionId);

      setData((previous) => ({
        ...previous,
        intelligence: {
          ...previous?.intelligence,
          investigation: result,
        },
      }));
    } catch (err) {
      setError(
        err?.message || "Investigation failed."
      );
    } finally {
      setInvestigating(false);
    }
  }

  async function handleReview(action) {
    try {
      setReviewing(true);
      setError(null);
      setReviewMessage(null);

      const result = await reviewException(
        exceptionId,
        {
          action,
          reviewer: "ops_user",
          reason: `Exception ${action.toLowerCase()}d after investigation.`,
        }
      );

      setReviewMessage(
        result?.message ||
          `Exception ${action.toLowerCase()}d successfully.`
      );

      // Reload the exception so status, review history,
      // and audit timeline stay synchronized with backend.
      const updatedData =
        await getExceptionDetails(exceptionId);

      setData(updatedData);
    } catch (err) {
      setError(
        err?.message || "Failed to submit review."
      );
    } finally {
      setReviewing(false);
    }
  }

  function formatDate(value) {
    if (!value) {
      return "â€”";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  function formatConfidence(value) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "â€”";
    }

    const numericValue = Number(value);

    if (Number.isNaN(numericValue)) {
      return value;
    }

    const percentage =
      numericValue <= 1
        ? numericValue * 100
        : numericValue;

    return `${percentage.toFixed(1)}%`;
  }

  if (error && !data) {
    return (
      <div className="placeholder-card">
        <h2>Unable to load exception</h2>

        <p>{error}</p>

        <button
          className="secondary-button"
          onClick={() => navigate("/exceptions")}
        >
          â† Back to Exceptions
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="placeholder-card">
        Loading exception intelligence...
      </div>
    );
  }

  const exception = data.exception || {};
  const intelligence = data.intelligence || {};

  const evidence = Array.isArray(data.evidence)
    ? data.evidence
    : [];

  const humanReviews = Array.isArray(
    data.human_reviews
  )
    ? data.human_reviews
    : [];

  const auditLogs = Array.isArray(data.audit_logs)
    ? data.audit_logs
    : [];

  const investigation =
    intelligence.investigation ||
    intelligence;

  const aiAnalysis =
    investigation?.ai_analysis ||
    intelligence?.ai_analysis ||
    null;

  const deterministicAnalysis =
    investigation?.deterministic_analysis ||
    intelligence?.deterministic_analysis ||
    {};

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div>
          <button
            className="secondary-button"
            onClick={() => navigate("/exceptions")}
          >
            â† Back to Exceptions
          </button>

          <h1>Exception Details</h1>

          <p>
            Investigate the reconciliation exception,
            review evidence, and make an operational
            decision.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={handleInvestigation}
          disabled={investigating}
        >
          {investigating
            ? "Investigating..."
            : "Run AI Investigation"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="placeholder-card">
          <strong>Operation failed</strong>

          <p>{error}</p>
        </div>
      )}

      {/* Exception Overview */}
      <div className="details-grid">
        <div className="detail-card">
          <span>Exception ID</span>

          <strong>
            {exception.exception_id || "â€”"}
          </strong>
        </div>

        <div className="detail-card">
          <span>Transaction ID</span>

          <strong>
            {exception.transaction_id || "â€”"}
          </strong>
        </div>

        <div className="detail-card">
          <span>Exception Type</span>

          <strong>
            {exception.exception_type || "â€”"}
          </strong>
        </div>

        <div className="detail-card">
          <span>Severity</span>

          <strong>
            <span
              className={`badge severity-${String(
                exception.severity || ""
              ).toLowerCase()}`}
            >
              {exception.severity || "UNKNOWN"}
            </span>
          </strong>
        </div>

        <div className="detail-card">
          <span>Status</span>

          <strong>
            <span
              className={`badge status-${String(
                exception.status || ""
              ).toLowerCase()}`}
            >
              {exception.status || "UNKNOWN"}
            </span>
          </strong>
        </div>

        <div className="detail-card">
          <span>Confidence</span>

          <strong>
            {formatConfidence(
              exception.confidence
            )}
          </strong>
        </div>
      </div>

      {/* Description */}
      <div className="placeholder-card">
        <h2>Exception Summary</h2>

        <p>
          {exception.description ||
            "No exception description available."}
        </p>

        <small>
          Created:{" "}
          {formatDate(exception.created_at)}
        </small>
      </div>

      {/* Intelligence */}
      <div className="placeholder-card">
        <div className="section-header">
          <div>
            <h2>Investigation Intelligence</h2>

            <p>
              Deterministic analysis followed by
              AI-assisted investigation.
            </p>
          </div>

          {investigation?.investigation_mode && (
            <span className="badge">
              {investigation.investigation_mode}
            </span>
          )}
        </div>

        {aiAnalysis ? (
          <div className="intelligence-grid">
            <div className="intelligence-card">
              <span>Root Cause</span>

              <strong>
                {aiAnalysis.root_cause || "â€”"}
              </strong>
            </div>

            <div className="intelligence-card">
              <span>Risk Level</span>

              <strong>
                {aiAnalysis.risk_level || "â€”"}
              </strong>
            </div>

            <div className="intelligence-card">
              <span>Confidence</span>

              <strong>
                {formatConfidence(
                  aiAnalysis.confidence
                )}
              </strong>
            </div>

            <div className="intelligence-card">
              <span>Recommended Action</span>

              <strong>
                {aiAnalysis.recommended_action ||
                  "â€”"}
              </strong>
            </div>

            <div className="intelligence-card full-width">
              <span>Investigation Summary</span>

              <p>
                {aiAnalysis.summary || "â€”"}
              </p>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <strong>
              No AI investigation available yet.
            </strong>

            <p>
              Run an AI investigation to generate
              root cause analysis, risk assessment,
              confidence, and recommendations.
            </p>
          </div>
        )}
      </div>

      {/* Deterministic Analysis */}
      <div className="placeholder-card">
        <h2>Deterministic Analysis</h2>

        {Object.keys(
          deterministicAnalysis
        ).length === 0 ? (
          <div className="empty-state">
            No deterministic analysis available.
          </div>
        ) : (
          <div className="analysis-list">
            {Object.entries(
              deterministicAnalysis
            ).map(([key, value]) => (
              <div
                className="analysis-row"
                key={key}
              >
                <span>{key}</span>

                <strong>
                  {typeof value === "object"
                    ? JSON.stringify(value)
                    : String(value)}
                </strong>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Evidence */}
      <div className="placeholder-card">
        <div className="section-header">
          <div>
            <h2>Evidence</h2>

            <p>
              Records used to support the investigation.
            </p>
          </div>

          <span>
            {evidence.length} evidence record
            {evidence.length !== 1
              ? "s"
              : ""}
          </span>
        </div>

        {evidence.length === 0 ? (
          <div className="empty-state">
            No evidence records available.
          </div>
        ) : (
          <div className="evidence-list">
            {evidence.map((item) => (
              <div
                className="evidence-item"
                key={item.id}
              >
                <div>
                  <strong>
                    {item.evidence_type ||
                      "Evidence"}
                  </strong>

                  <p>
                    {item.description ||
                      "No description available."}
                  </p>
                </div>

                <div>
                  <small>
                    Source:{" "}
                    {item.source_table || "â€”"}
                  </small>

                  <small>
                    Record:{" "}
                    {item.source_record_id || "â€”"}
                  </small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Human Decision */}
      <div className="placeholder-card">
        <div className="section-header">
          <div>
            <h2>Operational Decision</h2>

            <p>
              Review the investigation and record
              the final operational decision.
            </p>
          </div>

          <span
            className={`badge status-${String(
              exception.status || ""
            ).toLowerCase()}`}
          >
            {exception.status || "UNKNOWN"}
          </span>
        </div>

        {reviewMessage && (
          <div className="empty-state">
            <strong>{reviewMessage}</strong>
          </div>
        )}

        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            marginTop: "20px",
          }}
        >
          <button
            className="primary-button"
            disabled={reviewing}
            onClick={() =>
              handleReview("APPROVE")
            }
          >
            {reviewing
              ? "Submitting..."
              : "Approve"}
          </button>

          <button
            className="secondary-button"
            disabled={reviewing}
            onClick={() =>
              handleReview("REJECT")
            }
          >
            Reject
          </button>

          <button
            className="secondary-button"
            disabled={reviewing}
            onClick={() =>
              handleReview("ESCALATE")
            }
          >
            Escalate
          </button>
        </div>
      </div>

      {/* Human Reviews */}
      <div className="placeholder-card">
        <h2>Human Review History</h2>

        {humanReviews.length === 0 ? (
          <div className="empty-state">
            No human reviews have been submitted.
          </div>
        ) : (
          <div className="timeline">
            {humanReviews.map((review) => (
              <div
                className="timeline-item"
                key={review.id}
              >
                <strong>
                  {review.action}
                </strong>

                <span>
                  Reviewer:{" "}
                  {review.reviewer}
                </span>

                <p>
                  {review.reason}
                </p>

                <small>
                  {formatDate(
                    review.created_at
                  )}
                </small>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Audit Timeline */}
      <div className="placeholder-card">
        <h2>Audit Timeline</h2>

        {auditLogs.length === 0 ? (
          <div className="empty-state">
            No audit events available.
          </div>
        ) : (
          <div className="timeline">
            {auditLogs.map((log) => (
              <div
                className="timeline-item"
                key={log.id}
              >
                <strong>
                  {log.action}
                </strong>

                <span>
                  {log.previous_state
                    ? `${log.previous_state} â†’ ${log.new_state}`
                    : log.new_state || "â€”"}
                </span>

                <p>
                  {log.reason ||
                    `Action performed by ${
                      log.actor || "system"
                    }.`}
                </p>

                <small>
                  {formatDate(
                    log.created_at
                  )}
                </small>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ExceptionDetails;
