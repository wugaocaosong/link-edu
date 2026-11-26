"""Record one trial grant for each account without resetting usage."""
from alembic import op
import sqlalchemy as sa

revision = '20261125_02'
down_revision = '20261125_01'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if not sa.inspect(connection).has_table('assistant_trial_grants'):
        op.create_table('assistant_trial_grants',
                        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
                        sa.Column('amount_cents', sa.Integer(), nullable=False))
    grants = sa.table('assistant_trial_grants', sa.column('user_id', sa.Integer()), sa.column('amount_cents', sa.Integer()))
    users = sa.table('users', sa.column('id', sa.Integer()))
    existing = sa.select(grants.c.user_id).where(grants.c.user_id == users.c.id).exists()
    connection.execute(grants.insert().from_select(['user_id', 'amount_cents'],
                       sa.select(users.c.id, sa.literal(200)).where(~existing)))


def downgrade():
    op.drop_table('assistant_trial_grants')
