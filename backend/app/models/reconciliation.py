from datetime import datetime,UTC
from decimal import Decimal

from sqlalchemy import DateTime, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    total_records: Mapped[int] = mapped_column(default=0)
    matched_records: Mapped[int] = mapped_column(default=0)
    exception_count: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
       default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id: Mapped[int] = mapped_column(primary_key=True)

    run_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    expected_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    actual_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    difference: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    match_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    match_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)

    exception_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    exception_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)

    exception_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    evidence_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_table: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    source_record_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
       default=lambda: datetime.now(UTC),
        nullable=False,
    )
class Investigation(Base):
    """
    Persisted record of an AI-assisted exception investigation.

    Multiple investigations may exist for the same exception,
    allowing investigation history and comparison over time.
    """

    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True)

    investigation_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    exception_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    investigation_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    ai_provider_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    evidence_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    deterministic_analysis: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    ai_analysis: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    fallback_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

class HumanReview(Base):
    __tablename__ = "human_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)

    exception_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    reviewer: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
      default=lambda: datetime.now(UTC),
        nullable=False,
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    transaction_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    actor: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    previous_state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    new_state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
