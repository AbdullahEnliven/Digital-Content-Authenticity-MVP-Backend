from alembic import op
import sqlalchemy as sa

revision = "20260327_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "uploaded_contents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("upload_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_uploaded_contents_id"), "uploaded_contents", ["id"], unique=False)
    op.create_index(op.f("ix_uploaded_contents_sha256_hash"), "uploaded_contents", ["sha256_hash"], unique=False)
    op.create_index(op.f("ix_uploaded_contents_user_id"), "uploaded_contents", ["user_id"], unique=False)

    op.create_table(
        "metadata_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_id", sa.Integer(), sa.ForeignKey("uploaded_contents.id"), nullable=False),
        sa.Column("file_format", sa.String(length=50), nullable=True),
        sa.Column("creation_timestamp", sa.String(length=100), nullable=True),
        sa.Column("device_info", sa.String(length=255), nullable=True),
        sa.Column("compression_indicators", sa.String(length=255), nullable=True),
        sa.Column("consistency_score", sa.Float(), nullable=False),
        sa.Column("raw_metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("content_id"),
    )
    op.create_index(op.f("ix_metadata_results_id"), "metadata_results", ["id"], unique=False)

    op.create_table(
        "verifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content_id", sa.Integer(), sa.ForeignKey("uploaded_contents.id"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("final_trust_score", sa.Float(), nullable=True),
        sa.Column("trust_classification", sa.String(length=50), nullable=True),
        sa.Column("verification_status", sa.String(length=50), nullable=True),
        sa.Column("reasoning_summary", sa.String(length=1000), nullable=True),
        sa.Column("file_integrity_valid", sa.Boolean(), nullable=False),
        sa.Column("share_token", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_verifications_content_id"), "verifications", ["content_id"], unique=False)
    op.create_index(op.f("ix_verifications_id"), "verifications", ["id"], unique=False)
    op.create_index(op.f("ix_verifications_user_id"), "verifications", ["user_id"], unique=False)
    op.create_unique_constraint("uq_verifications_share_token", "verifications", ["share_token"])

    op.create_table(
        "ai_analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("verification_id", sa.Integer(), sa.ForeignKey("verifications.id"), nullable=False),
        sa.Column("ai_probability", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("verification_id"),
    )
    op.create_index(op.f("ix_ai_analysis_results_id"), "ai_analysis_results", ["id"], unique=False)

    op.create_table(
        "trust_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("verification_id", sa.Integer(), sa.ForeignKey("verifications.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("trust_level", sa.String(length=50), nullable=False),
        sa.Column("reasoning", sa.String(length=1000), nullable=False),
        sa.Column("rule_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("verification_id"),
    )
    op.create_index(op.f("ix_trust_scores_id"), "trust_scores", ["id"], unique=False)

    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("verification_id", sa.Integer(), sa.ForeignKey("verifications.id"), nullable=False),
        sa.Column("verification_code", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("shareable_link", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("verification_code"),
        sa.UniqueConstraint("verification_id"),
    )
    op.create_index(op.f("ix_certificates_id"), "certificates", ["id"], unique=False)

    op.create_table(
        "verification_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("verification_id", sa.Integer(), sa.ForeignKey("verifications.id"), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("event", sa.String(length=255), nullable=False),
        sa.Column("details", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_verification_logs_id"), "verification_logs", ["id"], unique=False)
    op.create_index(op.f("ix_verification_logs_verification_id"), "verification_logs", ["verification_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_verification_logs_verification_id"), table_name="verification_logs")
    op.drop_index(op.f("ix_verification_logs_id"), table_name="verification_logs")
    op.drop_table("verification_logs")
    op.drop_index(op.f("ix_certificates_id"), table_name="certificates")
    op.drop_table("certificates")
    op.drop_index(op.f("ix_trust_scores_id"), table_name="trust_scores")
    op.drop_table("trust_scores")
    op.drop_index(op.f("ix_ai_analysis_results_id"), table_name="ai_analysis_results")
    op.drop_table("ai_analysis_results")
    op.drop_constraint("uq_verifications_share_token", "verifications", type_="unique")
    op.drop_index(op.f("ix_verifications_user_id"), table_name="verifications")
    op.drop_index(op.f("ix_verifications_id"), table_name="verifications")
    op.drop_index(op.f("ix_verifications_content_id"), table_name="verifications")
    op.drop_table("verifications")
    op.drop_index(op.f("ix_metadata_results_id"), table_name="metadata_results")
    op.drop_table("metadata_results")
    op.drop_index(op.f("ix_uploaded_contents_user_id"), table_name="uploaded_contents")
    op.drop_index(op.f("ix_uploaded_contents_sha256_hash"), table_name="uploaded_contents")
    op.drop_index(op.f("ix_uploaded_contents_id"), table_name="uploaded_contents")
    op.drop_table("uploaded_contents")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
