"""Add participant allocation and versioned experiment attempts."""
from alembic import op
import sqlalchemy as sa

revision = '20261123_01'
down_revision = '20261120_01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('study_participants',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tenant_id', sa.Integer, sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('code', sa.String(8), nullable=False), sa.Column('experience', sa.Boolean, nullable=False),
        sa.Column('arm', sa.String(16), nullable=False), sa.Column('first_form', sa.String(1), nullable=False),
        sa.UniqueConstraint('tenant_id', 'user_id'), sa.UniqueConstraint('tenant_id', 'code'),
        if_not_exists=True)
    op.create_table('study_attempts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('participant_id', sa.Integer, sa.ForeignKey('study_participants.id'), nullable=False),
        sa.Column('stage', sa.String(12), nullable=False), sa.Column('number', sa.Integer, nullable=False),
        sa.Column('previous_id', sa.Integer, sa.ForeignKey('study_attempts.id')),
        sa.Column('clip', sa.String(32), nullable=False, unique=True),
        sa.Column('session_id', sa.Integer, sa.ForeignKey('classrooms.session_id'), unique=True),
        sa.Column('created', sa.DateTime, nullable=False), sa.Column('finished', sa.DateTime),
        sa.Column('version', sa.String(40), nullable=False), sa.Column('assessment', sa.JSON),
        sa.Column('reflection', sa.JSON), sa.Column('packet', sa.JSON), sa.Column('issued', sa.JSON),
        sa.Column('goal', sa.Text), sa.Column('anomaly', sa.Text),
        sa.UniqueConstraint('participant_id', 'stage', 'number'), if_not_exists=True)


def downgrade():
    op.drop_table('study_attempts')
    op.drop_table('study_participants')
