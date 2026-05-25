"""add email_messages table for workflow email steps

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_instance_id", sa.String(), nullable=True),
        sa.Column("to_address", sa.String(), nullable=False),
        sa.Column("template", sa.String(), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body_preview", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("provider_id", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workflow_instance_id"], ["workflow_instances.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_messages_workflow_instance_id"),
        "email_messages",
        ["workflow_instance_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_email_messages_workflow_instance_id"), table_name="email_messages")
    op.drop_table("email_messages")
