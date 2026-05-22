from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260520_01"
down_revision = "20260407_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("sessions", sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    op.drop_column("sessions", "pinned")
    op.drop_column("sessions", "title")
