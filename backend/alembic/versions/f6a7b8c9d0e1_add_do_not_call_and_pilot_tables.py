"""add do_not_call and pilot_applications tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "do_not_call",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_do_not_call_organization_id"), "do_not_call", ["organization_id"], unique=False)
    op.create_index(op.f("ix_do_not_call_phone"), "do_not_call", ["phone"], unique=False)

    op.create_table(
        "pilot_applications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("volume", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("use_case", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True, server_default="new"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pilot_applications")
    op.drop_index(op.f("ix_do_not_call_phone"), table_name="do_not_call")
    op.drop_index(op.f("ix_do_not_call_organization_id"), table_name="do_not_call")
    op.drop_table("do_not_call")
