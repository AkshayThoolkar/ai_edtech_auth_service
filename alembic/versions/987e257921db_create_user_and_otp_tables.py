"""create_user_and_otp_tables

Revision ID: 987e257921db
Revises: 
Create Date: 2025-06-08 19:18:09.009325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '987e257921db'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    op.create_index('idx_user_google_id', 'users', ['google_id'], unique=True)
    op.create_index('idx_user_active_verified', 'users', ['is_active', 'is_verified'])
    
    # Create otps table
    op.create_table(
        'otps',
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('otp_code', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('email')
    )
    
    # Create indexes for otps table
    op.create_index('idx_otp_email', 'otps', ['email'])
    op.create_index('idx_otp_expires_at', 'otps', ['expires_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop otps table and its indexes
    op.drop_index('idx_otp_expires_at', table_name='otps')
    op.drop_index('idx_otp_email', table_name='otps')
    op.drop_table('otps')
    
    # Drop users table and its indexes
    op.drop_index('idx_user_active_verified', table_name='users')
    op.drop_index('idx_user_google_id', table_name='users')
    op.drop_index('idx_user_email', table_name='users')
    op.drop_table('users')
