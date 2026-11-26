"""Store account-scoped assistant learning labels."""
from alembic import op
import sqlalchemy as sa

revision = '20261124_02'
down_revision = '20261124_01'
branch_labels = None
depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table('assistant_profiles'):
        op.create_table(
            'assistant_profiles',
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('labels', sa.JSON(), nullable=False),
        )


def downgrade():
    op.drop_table('assistant_profiles')
