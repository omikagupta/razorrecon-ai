"""add tax amount to payments

Revision ID: bac534284855
Revises: c451329fa386
Create Date: 2026-09-03 14:31:56.805514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bac534284855'
down_revision: Union[str, Sequence[str], None] = 'c451329fa386'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
