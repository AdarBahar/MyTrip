"""Enhance stops management

Revision ID: 003_enhance_stops_management
Revises: 002_add_trip_date_management
Create Date: 2025-08-21 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003_enhance_stops_management'
down_revision = '387c1b35ca98'
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced stops management fields"""
    
    # Create the new StopType enum
    stop_type_enum = sa.Enum(
        'ACCOMMODATION', 'FOOD', 'ATTRACTION', 'ACTIVITY', 'SHOPPING', 
        'GAS', 'TRANSPORT', 'SERVICES', 'NATURE', 'CULTURE', 'NIGHTLIFE', 'OTHER',
        name='stoptype'
    )
    stop_type_enum.create(op.get_bind())
    
    # Add new columns to stops table
    op.add_column('stops', sa.Column('stop_type', stop_type_enum, nullable=False, server_default='OTHER'))
    op.add_column('stops', sa.Column('arrival_time', sa.Time(), nullable=True))
    op.add_column('stops', sa.Column('departure_time', sa.Time(), nullable=True))
    op.add_column('stops', sa.Column('duration_minutes', sa.Integer(), nullable=True))
    op.add_column('stops', sa.Column('booking_info', sa.JSON(), nullable=True))
    op.add_column('stops', sa.Column('contact_info', sa.JSON(), nullable=True))
    op.add_column('stops', sa.Column('cost_info', sa.JSON(), nullable=True))
    op.add_column('stops', sa.Column('priority', sa.Integer(), nullable=False, server_default='3'))
    
    # Add check constraint for priority values (1-5)
    op.create_check_constraint(
        'ck_stop_priority_range',
        'stops',
        'priority >= 1 AND priority <= 5'
    )
    
    # Add check constraint for duration_minutes (positive values)
    op.create_check_constraint(
        'ck_stop_duration_positive',
        'stops',
        'duration_minutes IS NULL OR duration_minutes > 0'
    )


def downgrade():
    """Remove enhanced stops management fields"""
    
    # Drop check constraints
    op.drop_constraint('ck_stop_duration_positive', 'stops', type_='check')
    op.drop_constraint('ck_stop_priority_range', 'stops', type_='check')
    
    # Drop columns
    op.drop_column('stops', 'priority')
    op.drop_column('stops', 'cost_info')
    op.drop_column('stops', 'contact_info')
    op.drop_column('stops', 'booking_info')
    op.drop_column('stops', 'duration_minutes')
    op.drop_column('stops', 'departure_time')
    op.drop_column('stops', 'arrival_time')
    op.drop_column('stops', 'stop_type')
    
    # Drop the enum type
    sa.Enum(name='stoptype').drop(op.get_bind())
