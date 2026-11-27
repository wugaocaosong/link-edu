"""Repair assistant turn columns when an earlier merge was stamped prematurely."""
from alembic import op
import sqlalchemy as sa


revision = '20261127_01'
down_revision = '20261126_01'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    for table in ('classroom_api_usage', 'classroom_credit_usage'):
        if not inspector.has_table(table):
            continue
        columns = {column['name'] for column in inspector.get_columns(table)}
        if 'assistant_turn' not in columns:
            op.add_column(table, sa.Column('assistant_turn', sa.String(64), nullable=True))
        inspector = sa.inspect(connection)
        indexes = {index['name'] for index in inspector.get_indexes(table)}
        index_name = f'ix_{table}_assistant_turn'
        if index_name not in indexes:
            op.create_index(index_name, table, ['assistant_turn'])


def downgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    for table in ('classroom_credit_usage', 'classroom_api_usage'):
        if not inspector.has_table(table):
            continue
        columns = {column['name'] for column in inspector.get_columns(table)}
        index_name = f'ix_{table}_assistant_turn'
        if index_name in {index['name'] for index in inspector.get_indexes(table)}:
            op.drop_index(index_name, table_name=table)
        if 'assistant_turn' in columns:
            op.drop_column(table, 'assistant_turn')
        inspector = sa.inspect(connection)
