"""add investigations table

Revision ID: c451329fa386
Revises: f91af069443f
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c451329fa386"
down_revision: Union[str, Sequence[str], None] = "f91af069443f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create investigations table if it does not already exist."""

    bind = op.get_bind()

    inspector = sa.inspect(bind)

    if "investigations" in inspector.get_table_names():
        return

    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "investigation_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "exception_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "investigation_mode",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "ai_provider_status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "evidence_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "deterministic_analysis",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "ai_analysis",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "fallback_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_investigations_investigation_id",
        "investigations",
        ["investigation_id"],
        unique=True,
    )

    op.create_index(
        "ix_investigations_exception_id",
        "investigations",
        ["exception_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove investigations table if it exists."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "investigations" not in inspector.get_table_names():
        return

    op.drop_index(
        "ix_investigations_exception_id",
        table_name="investigations",
    )

    op.drop_index(
        "ix_investigations_investigation_id",
        table_name="investigations",
    )

    op.drop_table("investigations")