"""create datasets table

Revision ID: 20260306_0001
Revises:
Create Date: 2026-03-06 00:08:00.000000
"""
# mypy: disable-error-code=arg-type
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260306_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "datasets" not in table_names:
        op.create_table(
            "datasets",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dataset_id", sa.String(length=128), nullable=False),
            sa.Column("name", sa.String(length=256), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("file_path", sa.String(length=1024), nullable=False),
            sa.Column("file_type", sa.String(length=32), nullable=False),
            sa.Column("source", sa.String(length=256), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("row_count", sa.Integer(), nullable=True),
            sa.Column("column_count", sa.Integer(), nullable=True),
            sa.Column("file_size", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("dataset_id"),
        )
        op.create_index(op.f("ix_datasets_dataset_id"), "datasets", ["dataset_id"], unique=True)
        op.create_index(op.f("ix_datasets_id"), "datasets", ["id"], unique=False)
        return

    existing_columns = {column["name"] for column in inspector.get_columns("datasets")}

    _add_column_if_missing(existing_columns, "dataset_id", sa.Column("dataset_id", sa.String(length=128), nullable=False, server_default=""))
    _add_column_if_missing(existing_columns, "name", sa.Column("name", sa.String(length=256), nullable=False, server_default=""))
    _add_column_if_missing(existing_columns, "description", sa.Column("description", sa.Text(), nullable=True))
    _add_column_if_missing(existing_columns, "file_path", sa.Column("file_path", sa.String(length=1024), nullable=False, server_default=""))
    _add_column_if_missing(existing_columns, "file_type", sa.Column("file_type", sa.String(length=32), nullable=False, server_default=""))
    _add_column_if_missing(existing_columns, "source", sa.Column("source", sa.String(length=256), nullable=True))
    _add_column_if_missing(existing_columns, "created_by", sa.Column("created_by", sa.String(length=128), nullable=False, server_default="system"))
    _add_column_if_missing(existing_columns, "created_at", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")))
    _add_column_if_missing(existing_columns, "updated_at", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")))
    _add_column_if_missing(existing_columns, "status", sa.Column("status", sa.String(length=50), nullable=True, server_default="uploaded"))
    _add_column_if_missing(existing_columns, "metadata", sa.Column("metadata", sa.JSON(), nullable=True))
    _add_column_if_missing(existing_columns, "row_count", sa.Column("row_count", sa.Integer(), nullable=True, server_default="0"))
    _add_column_if_missing(existing_columns, "column_count", sa.Column("column_count", sa.Integer(), nullable=True, server_default="0"))
    _add_column_if_missing(existing_columns, "file_size", sa.Column("file_size", sa.Integer(), nullable=True, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "datasets" in inspector.get_table_names():
        op.drop_index(op.f("ix_datasets_id"), table_name="datasets")
        op.drop_index(op.f("ix_datasets_dataset_id"), table_name="datasets")
        op.drop_table("datasets")


def _add_column_if_missing(existing_columns: set[str], name: str, column: sa.Column[object]) -> None:
    if name not in existing_columns:
        op.add_column("datasets", column)
