"""Track assistant usage by turn; add separate membership and points ledgers."""
from alembic import op
import sqlalchemy as sa

revision = '20261125_01'
down_revision = ('20261124_04', '20261123_01')
branch_labels = None
depends_on = None

USAGE_TABLES = ('classroom_api_usage', 'classroom_credit_usage')


def upgrade():
    inspector = sa.inspect(op.get_bind())
    for table in USAGE_TABLES:
        if 'assistant_turn' not in {column['name'] for column in inspector.get_columns(table)}:
            op.add_column(table, sa.Column('assistant_turn', sa.String(64), nullable=True))
            op.create_index(f'ix_{table}_assistant_turn', table, ['assistant_turn'])
    if not inspector.has_table('assistant_memberships'):
        op.create_table('assistant_memberships',
                        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
                        sa.Column('points', sa.Integer(), nullable=False),
                        sa.Column('plus_until', sa.DateTime()), sa.Column('last_check_in', sa.Date()))
    if not inspector.has_table('assistant_point_entries'):
        op.create_table('assistant_point_entries',
                        sa.Column('id', sa.Integer(), primary_key=True),
                        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
                        sa.Column('change', sa.Integer(), nullable=False),
                        sa.Column('reason', sa.String(20), nullable=False),
                        sa.Column('created_at', sa.DateTime(), nullable=False))
        op.create_index('ix_assistant_point_entries_user_id', 'assistant_point_entries', ['user_id'])


def downgrade():
    op.drop_table('assistant_point_entries')
    op.drop_table('assistant_memberships')
    for table in USAGE_TABLES:
        op.drop_index(f'ix_{table}_assistant_turn', table_name=table)
        op.drop_column(table, 'assistant_turn')
