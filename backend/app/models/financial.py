from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    order_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    payment_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(primary_key=True)
    settlement_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    payment_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
    )
    settlement_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(primary_key=True)
    refund_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    payment_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    order_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    refund_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


class Fee(Base):
    __tablename__ = "fees"

    id: Mapped[int] = mapped_column(primary_key=True)
    fee_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    payment_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    fee_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class Adjustment(Base):
    __tablename__ = "adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    adjustment_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    payment_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    adjustment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )