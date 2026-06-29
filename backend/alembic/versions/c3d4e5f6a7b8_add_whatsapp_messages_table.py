"""add whatsapp_messages table for workflow WhatsApp steps

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_instance_id", sa.String(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("to_phone", sa.String(), nullable=False),
        sa.Column("template", sa.String(), nullable=True),
        sa.Column("message_body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("provider_message_sid", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workflow_instance_id"], ["workflow_instances.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_whatsapp_messages_workflow_instance_id"),
        "whatsapp_messages",
        ["workflow_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_whatsapp_messages_organization_id"),
        "whatsapp_messages",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_whatsapp_messages_organization_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_workflow_instance_id"), table_name="whatsapp_messages")
    op.drop_table("whatsapp_messages")
