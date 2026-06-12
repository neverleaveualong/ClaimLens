"""add claim parser status columns

Revision ID: 7f0b6d3c9a21
Revises: 43989b4b3b37
Create Date: 2026-06-12 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "7f0b6d3c9a21"
down_revision: str | None = "43989b4b3b37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE claims ADD COLUMN IF NOT EXISTS parser_method VARCHAR(50)")
    op.execute("ALTER TABLE claims ADD COLUMN IF NOT EXISTS parser_status VARCHAR(50)")
    op.execute("ALTER TABLE claim_elements ADD COLUMN IF NOT EXISTS parser_method VARCHAR(50)")
    op.execute("ALTER TABLE claim_elements ADD COLUMN IF NOT EXISTS parser_status VARCHAR(50)")


def downgrade() -> None:
    op.execute("ALTER TABLE claim_elements DROP COLUMN IF EXISTS parser_status")
    op.execute("ALTER TABLE claim_elements DROP COLUMN IF EXISTS parser_method")
    op.execute("ALTER TABLE claims DROP COLUMN IF EXISTS parser_status")
    op.execute("ALTER TABLE claims DROP COLUMN IF EXISTS parser_method")
