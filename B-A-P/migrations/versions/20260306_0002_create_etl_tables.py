"""create etl pipeline tables

Revision ID: 20260306_0002
Revises: 20260306_0001
Create Date: 2026-03-06 00:42:00.000000
"""
# mypy: disable-error-code=arg-type
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260306_0002"
down_revision: Union[str, Sequence[str], None] = "20260306_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "etl_jobs" not in table_names:
        op.create_table(
            "etl_jobs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("job_id", sa.String(length=128), nullable=False),
            sa.Column("dataset_id", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("parameters", sa.JSON(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("job_id"),
        )
        op.create_index(op.f("ix_etl_jobs_id"), "etl_jobs", ["id"], unique=False)
        op.create_index(op.f("ix_etl_jobs_job_id"), "etl_jobs", ["job_id"], unique=True)
        op.create_index(op.f("ix_etl_jobs_dataset_id"), "etl_jobs", ["dataset_id"], unique=False)

    if "processed_datasets" not in table_names:
        op.create_table(
            "processed_datasets",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dataset_id", sa.String(length=128), nullable=False),
            sa.Column("source_job_id", sa.String(length=128), nullable=False),
            sa.Column("row_count", sa.Integer(), nullable=True),
            sa.Column("column_count", sa.Integer(), nullable=True),
            sa.Column("schema", sa.JSON(), nullable=True),
            sa.Column("summary", sa.JSON(), nullable=True),
            sa.Column("records", sa.JSON(), nullable=True),
            sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("dataset_id"),
        )
        op.create_index(
            op.f("ix_processed_datasets_id"),
            "processed_datasets",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_processed_datasets_dataset_id"),
            "processed_datasets",
            ["dataset_id"],
            unique=True,
        )
        op.create_index(
            op.f("ix_processed_datasets_source_job_id"),
            "processed_datasets",
            ["source_job_id"],
            unique=False,
        )

    if "ai_insights" not in table_names:
        op.create_table(
            "ai_insights",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("insight_id", sa.String(length=128), nullable=False),
            sa.Column("dataset_id", sa.String(length=128), nullable=False),
            sa.Column("insight_type", sa.String(length=50), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("insight_id"),
        )
        op.create_index(op.f("ix_ai_insights_id"), "ai_insights", ["id"], unique=False)
        op.create_index(
            op.f("ix_ai_insights_insight_id"),
            "ai_insights",
            ["insight_id"],
            unique=True,
        )
        op.create_index(
            op.f("ix_ai_insights_dataset_id"),
            "ai_insights",
            ["dataset_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "ai_insights" in table_names:
        op.drop_index(op.f("ix_ai_insights_dataset_id"), table_name="ai_insights")
        op.drop_index(op.f("ix_ai_insights_insight_id"), table_name="ai_insights")
        op.drop_index(op.f("ix_ai_insights_id"), table_name="ai_insights")
        op.drop_table("ai_insights")

    if "processed_datasets" in table_names:
        op.drop_index(
            op.f("ix_processed_datasets_source_job_id"),
            table_name="processed_datasets",
        )
        op.drop_index(
            op.f("ix_processed_datasets_dataset_id"),
            table_name="processed_datasets",
        )
        op.drop_index(op.f("ix_processed_datasets_id"), table_name="processed_datasets")
        op.drop_table("processed_datasets")

    if "etl_jobs" in table_names:
        op.drop_index(op.f("ix_etl_jobs_dataset_id"), table_name="etl_jobs")
        op.drop_index(op.f("ix_etl_jobs_job_id"), table_name="etl_jobs")
        op.drop_index(op.f("ix_etl_jobs_id"), table_name="etl_jobs")
        op.drop_table("etl_jobs")
