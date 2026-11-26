"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('telegram_id', sa.BigInteger(), nullable=True),
    sa.Column('display_name', sa.String(length=128), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('photo_url', sa.String(length=512), nullable=True),
    sa.Column('birth_year', sa.Integer(), nullable=True),
    sa.Column('resting_hr', sa.Integer(), nullable=True),
    sa.Column('max_hr', sa.Integer(), nullable=True),
    sa.Column('zone2_low', sa.Integer(), nullable=True),
    sa.Column('zone2_high', sa.Integer(), nullable=True),
    sa.Column('share_bpm', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    op.create_table('meetings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=140), nullable=False),
    sa.Column('topic', sa.String(length=2000), nullable=False),
    sa.Column('host_id', sa.Integer(), nullable=False),
    sa.Column('starts_at', sa.DateTime(), nullable=False),
    sa.Column('duration_min', sa.Integer(), nullable=False),
    sa.Column('activity', sa.Enum('bike', 'treadmill', 'walk', 'run', 'any', name='activity'), nullable=False),
    sa.Column('visibility', sa.Enum('public', 'private', name='visibility'), nullable=False),
    sa.Column('invite_code', sa.String(length=32), nullable=True),
    sa.Column('voice_link', sa.String(length=512), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['host_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_meetings_invite_code', 'meetings', ['invite_code'], unique=False)

    op.create_table('attendances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('meeting_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(), nullable=False),
    sa.Column('left_at', sa.DateTime(), nullable=True),
    sa.Column('samples', sa.Integer(), nullable=False),
    sa.Column('avg_hr', sa.Double(), nullable=True),
    sa.Column('tracked_seconds', sa.Double(), nullable=False),
    sa.Column('zone2_seconds', sa.Double(), nullable=False),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('meeting_id', 'user_id')
    )


def downgrade() -> None:
    op.drop_table('attendances')
    op.drop_index('ix_meetings_invite_code', table_name='meetings')

    op.drop_table('meetings')
    op.drop_index('ix_users_telegram_id', table_name='users')

    op.drop_table('users')
    # Postgres keeps enum types after dropping the tables that use them.
    sa.Enum(name='visibility').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='activity').drop(op.get_bind(), checkfirst=True)
