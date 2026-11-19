
"""Initial schema with users, recordings, predictions.

Revision ID: 001_initial
Revises:
Create Date: 2026-11-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # Recordings table
    op.create_table(
        "recordings",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(50), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("duration_sec", sa.Float(), nullable=False),
        sa.Column("sample_rate", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hour", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("progress_stage", sa.String(100), nullable=False, server_default=""),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recordings_user_id", "recordings", ["user_id"])
    op.create_index("ix_recordings_sha256", "recordings", ["sha256"])
    op.create_index("ix_recordings_status", "recordings", ["status"])
    op.create_index("ix_recordings_created_at", "recordings", ["created_at"])
    op.create_index(
        "ix_recordings_user_created", "recordings", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_recordings_status_created", "recordings", ["status", "created_at"]
    )

    # Predictions table
    op.create_table(
        "predictions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("recording_id", sa.String(36), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("top_species", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recording_id"], ["recordings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recording_id"),
    )
    op.create_index(
        "ix_predictions_recording_id", "predictions", ["recording_id"]
    )

    # Detections table
    op.create_table(
        "detections",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("recording_id", sa.String(36), nullable=False),
        sa.Column("species_code", sa.String(50), nullable=False),
        sa.Column("species_name", sa.String(255), nullable=False),
        sa.Column("taxon", sa.String(50), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("windows_detected", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recording_id"], ["recordings.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_detections_recording_id", "detections", ["recording_id"])
    op.create_index("ix_detections_species_code", "detections", ["species_code"])
    op.create_index(
        "ix_detections_recording_species",
        "detections",
        ["recording_id", "species_code"],
    )

    # Feedback table
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("recording_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("species_code", sa.String(50), nullable=False),
        sa.Column("window_index", sa.Integer(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recording_id"], ["recordings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedback_recording_id", "feedback", ["recording_id"])
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_index(
        "ix_feedback_recording_user", "feedback", ["recording_id", "user_id"]
    )


def downgrade() -> None:
    """Drop all tables."""

    op.drop_table("feedback")
    op.drop_table("detections")
    op.drop_table("predictions")
    op.drop_table("recordings")
    op.drop_table("users")
