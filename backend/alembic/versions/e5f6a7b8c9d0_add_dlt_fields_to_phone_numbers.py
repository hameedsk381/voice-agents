"""add DLT compliance fields to phone_numbers

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("phone_numbers", sa.Column("dlt_entity_id", sa.String(), nullable=True))
    op.add_column("phone_numbers", sa.Column("dlt_header", sa.String(), nullable=True))
    op.add_column("phone_numbers", sa.Column("number_series", sa.String(), nullable=True))
    op.add_column(
        "phone_numbers",
        sa.Column("dlt_status", sa.String(), nullable=True, server_default="unregistered"),
    )
    op.add_column("phone_numbers", sa.Column("consent_template_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("phone_numbers", "consent_template_id")
    op.drop_column("phone_numbers", "dlt_status")
    op.drop_column("phone_numbers", "number_series")
    op.drop_column("phone_numbers", "dlt_header")
    op.drop_column("phone_numbers", "dlt_entity_id")
