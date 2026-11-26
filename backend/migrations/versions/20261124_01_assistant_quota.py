"""Attribute assistant model usage to its account."""
from alembic import op
import sqlalchemy as sa

revision = '20261124_01'
down_revision = '20261120_01'
branch_labels = None
depends_on = None

TABLES = ('classroom_api_usage', 'classroom_credit_usage')


def upgrade():
    inspector = sa.inspect(op.get_bind())
    for table in TABLES:
        if 'assistant_user_id' in {column['name'] for column in inspector.get_columns(table)}:
            continue
        op.add_column(table, sa.Column('assistant_user_id', sa.Integer(), nullable=True))
        op.create_index(f'ix_{table}_assistant_user_id', table, ['assistant_user_id'])


def downgrade():
    for table in reversed(TABLES):
        op.drop_index(f'ix_{table}_assistant_user_id', table_name=table)
        op.drop_column(table, 'assistant_user_id')
