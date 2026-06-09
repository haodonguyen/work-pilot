"""add automation event dedupe key

Revision ID: 20260609_0002
Revises: 20260609_0001
Create Date: 2026-06-09 00:00:01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260609_0002"
down_revision: Union[str, None] = "20260609_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("automation_events", sa.Column("dedupe_key", sa.String(length=320), nullable=True))
    op.create_index("uq_automation_events_dedupe_key", "automation_events", ["dedupe_key"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_automation_events_dedupe_key", table_name="automation_events")
    op.drop_column("automation_events", "dedupe_key")
