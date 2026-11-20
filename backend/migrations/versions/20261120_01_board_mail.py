"""Record accepted board messages for safe client retries."""
from alembic import op
import sqlalchemy as sa

revision = '20261120_01'
down_revision = '20261104_01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('board_mail_receipts',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('request_id', sa.String(36), primary_key=True),
        sa.Column('journal_id', sa.Integer(), sa.ForeignKey('training_journals.id'), nullable=False))


def downgrade():
    op.drop_table('board_mail_receipts')
