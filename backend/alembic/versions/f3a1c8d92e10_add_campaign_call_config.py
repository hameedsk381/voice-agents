"""add campaign call_config for greetings and template context

Revision ID: f3a1c8d92e10
Revises: c8e9ca82accd
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a1c8d92e10"
down_revision: Union[str, None] = "c8e9ca82accd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("call_config", sa.JSON(), nullable=True, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "call_config")
