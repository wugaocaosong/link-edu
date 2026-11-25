"""Add scoped assistant mistakes and tool audit."""
from alembic import op
import sqlalchemy as sa

revision = '20261124_04'
down_revision = '20261124_03'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    for name in ('assistant_mistakes', 'assistant_tool_audit'):
        if inspector.has_table(name):
            continue
        common = [
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        ]
        if name == 'assistant_mistakes':
            op.create_table(name, *common, sa.Column('question_key', sa.String(64), nullable=False),
                            sa.Column('question', sa.String(600), nullable=False),
                            sa.UniqueConstraint('user_id', 'tenant_id', 'question_key'))
        else:
            op.create_table(name, *common, sa.Column('tool', sa.String(32), nullable=False),
                            sa.Column('outcome', sa.String(24), nullable=False),
                            sa.Column('created_at', sa.DateTime(), nullable=False))
            op.create_index('ix_assistant_tool_audit_user_id', name, ['user_id'])


def downgrade():
    op.drop_table('assistant_tool_audit')
    op.drop_table('assistant_mistakes')
