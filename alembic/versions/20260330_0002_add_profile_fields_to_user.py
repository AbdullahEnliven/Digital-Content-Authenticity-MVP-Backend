from alembic import op
import sqlalchemy as sa

revision = "20260330_0002"
down_revision = "20260327_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("organization", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("job_role", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "bio")
    op.drop_column("users", "job_role")
    op.drop_column("users", "organization")