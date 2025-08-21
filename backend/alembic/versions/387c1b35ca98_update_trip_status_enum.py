"""update_trip_status_enum

Revision ID: 387c1b35ca98
Revises: 001
Create Date: 2025-08-21 12:44:00.033300

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '387c1b35ca98'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update existing trips with empty status to 'active'
    op.execute("UPDATE trips SET status = 'active' WHERE status = '' OR status IS NULL")

    # Alter the enum to include new values
    # Note: MySQL doesn't support ALTER TYPE for ENUMs, so we need to recreate the column
    op.execute("ALTER TABLE trips MODIFY COLUMN status ENUM('draft', 'active', 'completed', 'archived') NOT NULL DEFAULT 'active'")


def downgrade() -> None:
    # Revert to original enum values
    op.execute("ALTER TABLE trips MODIFY COLUMN status ENUM('active', 'archived') NOT NULL DEFAULT 'active'")