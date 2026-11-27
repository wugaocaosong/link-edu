"""Merge the study and assistant migration branches."""

revision = '20261126_01'
# The assistant billing migration 20261125_01 already merges the study and
# assistant-tools branches. Continue from its descendant to avoid a second head.
down_revision = '20261125_02'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
