"""Add password_hash field to users table

Revision ID: 011_add_user_password
Revises: 010_add_user_settings
Create Date: 2024-10-13 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011_add_user_password'
down_revision = '010_add_user_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_hash column to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove password_hash column from users table
    op.drop_column('users', 'password_hash')
