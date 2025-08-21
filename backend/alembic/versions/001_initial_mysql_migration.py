"""Initial MySQL migration

Revision ID: 001
Revises:
Create Date: 2025-01-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', name='userstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create trips table
    op.create_table('trips',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('destination', sa.String(255), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', name='tripstatus'), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.String(26), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', 'created_by', name='uq_trip_slug_creator')
    )

    # Create trip_members table
    op.create_table('trip_members',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('trip_id', sa.String(26), nullable=False),
        sa.Column('user_id', sa.String(26), nullable=True),
        sa.Column('invited_email', sa.String(255), nullable=True),
        sa.Column('role', sa.Enum('OWNER', 'EDITOR', 'VIEWER', name='tripmemberrole'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PENDING', 'REMOVED', name='tripmemberstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trip_id', 'user_id', name='uq_trip_member_user'),
        sa.UniqueConstraint('trip_id', 'invited_email', name='uq_trip_member_email')
    )

    # Create places table
    op.create_table('places',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('owner_type', sa.Enum('USER', 'TRIP', 'SYSTEM', name='ownertype'), nullable=False),
        sa.Column('owner_id', sa.String(26), nullable=False),
        sa.Column('provider_place_id', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('lat', sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column('lon', sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create days table
    op.create_table('days',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('trip_id', sa.String(26), nullable=False),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', name='daystatus'), nullable=False),
        sa.Column('rest_day', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.JSON(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('seq > 0', name='ck_day_seq_positive'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create stops table
    op.create_table('stops',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('day_id', sa.String(26), nullable=False),
        sa.Column('trip_id', sa.String(26), nullable=False),
        sa.Column('place_id', sa.String(26), nullable=False),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.Column('kind', sa.Enum('START', 'VIA', 'END', name='stopkind'), nullable=False),
        sa.Column('fixed', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('seq > 0', name='ck_stop_seq_positive'),
        sa.CheckConstraint("(kind != 'start') OR (seq = 1 AND fixed = true)", name='ck_stop_start_constraints'),
        sa.CheckConstraint("(kind != 'end') OR (fixed = true)", name='ck_stop_end_fixed'),
        sa.ForeignKeyConstraint(['day_id'], ['days.id'], ),
        sa.ForeignKeyConstraint(['place_id'], ['places.id'], ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('day_id', 'seq', name='uq_stop_day_seq')
    )

    # Create route_versions table
    op.create_table('route_versions',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('day_id', sa.String(26), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('profile_used', sa.String(50), nullable=True),
        sa.Column('total_km', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('total_min', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('geometry_wkt', sa.Text(), nullable=True),
        sa.Column('geojson', sa.JSON(), nullable=True),
        sa.Column('totals', sa.JSON(), nullable=True),
        sa.Column('stop_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(26), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['day_id'], ['days.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('day_id', 'version', name='uq_route_version_day_version')
    )
    op.create_index('ix_route_version_active', 'route_versions', ['day_id'], unique=False)

    # Create route_legs table
    op.create_table('route_legs',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('route_version_id', sa.String(26), nullable=False),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.Column('distance_km', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('duration_min', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('geometry_wkt', sa.Text(), nullable=True),
        sa.Column('geojson', sa.JSON(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['route_version_id'], ['route_versions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route_version_id', 'seq', name='uq_route_leg_version_seq')
    )

    # Create pins table
    op.create_table('pins',
        sa.Column('id', sa.String(26), nullable=False),
        sa.Column('trip_id', sa.String(26), nullable=False),
        sa.Column('place_id', sa.String(26), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('lat', sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column('lon', sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['place_id'], ['places.id'], ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('pins')
    op.drop_table('route_legs')
    op.drop_index('ix_route_version_active', table_name='route_versions')
    op.drop_table('route_versions')
    op.drop_table('stops')
    op.drop_table('days')
    op.drop_table('places')
    op.drop_table('trip_members')
    op.drop_table('trips')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')