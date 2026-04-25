from alembic import op
import sqlalchemy as sa

revision = "20260423_0003"
down_revision = "20260330_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("daily_credit_limit", sa.Integer(), nullable=False, server_default="250"))
    op.add_column("users", sa.Column("credits_remaining", sa.Integer(), nullable=False, server_default="250"))
    op.add_column("users", sa.Column("credits_reset_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "credits_reset_date")
    op.drop_column("users", "credits_remaining")
    op.drop_column("users", "daily_credit_limit")
