"""Persist assistant interview plan steps and check-ins."""
from alembic import op
import sqlalchemy as sa

revision = '20261124_03'
down_revision = '20261124_02'
branch_labels = None
depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table('assistant_interview_plans'):
        op.create_table(
            'assistant_interview_plans',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
            sa.Column('report_id', sa.Integer(), sa.ForeignKey('ai_feedbacks.id', ondelete='SET NULL')),
            sa.Column('kind', sa.String(16), nullable=False),
            sa.Column('steps', sa.JSON(), nullable=False),
            sa.Column('completed', sa.JSON(), nullable=False),
        )
        op.create_index('ix_assistant_interview_plans_user_id', 'assistant_interview_plans', ['user_id'])


def downgrade():
    op.drop_table('assistant_interview_plans')
