"""repair missing payment tax amount column

Revision ID: d7e4a1b9c2f0
Revises: bac534284855
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d7e4a1b9c2f0"
down_revision: Union[str, Sequence[str], None] = "bac534284855"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Repair databases stamped by the earlier no-op migration."""
    op.execute(
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS "
        "tax_amount NUMERIC(18, 2) NOT NULL DEFAULT 0.00"
    )


def downgrade() -> None:
    """Leave the compatibility column in place on downgrade."""
