"""Add soft delete to stops and DELETED status to days

Revision ID: 002
Revises: 001
Create Date: 2024-10-26 12:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    """Add soft delete to stops and DELETED status to days"""

    # Add deleted_at column to stops table
    op.add_column(
        "stops", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Update DayStatus enum to include DELETED
    # First, we need to alter the enum type
    op.execute(
        "ALTER TABLE days MODIFY COLUMN status ENUM('ACTIVE', 'INACTIVE', 'DELETED') NOT NULL DEFAULT 'ACTIVE'"
    )


def downgrade():
    """Remove soft delete from stops and DELETED status from days"""

    # Remove deleted_at column from stops table
    op.drop_column("stops", "deleted_at")

    # Revert DayStatus enum to original values
    # First, update any DELETED status to INACTIVE to avoid constraint violation
    op.execute("UPDATE days SET status = 'INACTIVE' WHERE status = 'DELETED'")

    # Then alter the enum type back
    op.execute(
        "ALTER TABLE days MODIFY COLUMN status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE'"
    )
