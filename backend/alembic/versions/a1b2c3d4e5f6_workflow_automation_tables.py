"""workflow automation: extend workflows, add workflow_instances

Revision ID: a1b2c3d4e5f6
Revises: f3a1c8d92e10
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f3a1c8d92e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("workflows", sa.Column("category", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("organization_id", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("version", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("status", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("is_template", sa.Boolean(), nullable=True))
    op.add_column("workflows", sa.Column("template_slug", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("created_by", sa.String(), nullable=True))
    op.add_column("workflows", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_workflows_category"), "workflows", ["category"], unique=False)
    op.create_index(op.f("ix_workflows_template_slug"), "workflows", ["template_slug"], unique=False)
    op.create_foreign_key("fk_workflows_created_by", "workflows", "users", ["created_by"], ["id"])

    op.create_table(
        "workflow_instances",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("current_node_id", sa.String(), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("wait_until", sa.DateTime(), nullable=True),
        sa.Column("campaign_id", sa.String(), nullable=True),
        sa.Column("contact_id", sa.String(), nullable=True),
        sa.Column("agent_id", sa.String(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["campaign_contacts.id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_instances_status"), "workflow_instances", ["status"], unique=False)
    op.create_index(op.f("ix_workflow_instances_workflow_id"), "workflow_instances", ["workflow_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_instances_workflow_id"), table_name="workflow_instances")
    op.drop_index(op.f("ix_workflow_instances_status"), table_name="workflow_instances")
    op.drop_table("workflow_instances")
    op.drop_constraint("fk_workflows_created_by", "workflows", type_="foreignkey")
    op.drop_index(op.f("ix_workflows_template_slug"), table_name="workflows")
    op.drop_index(op.f("ix_workflows_category"), table_name="workflows")
    op.drop_column("workflows", "updated_at")
    op.drop_column("workflows", "created_by")
    op.drop_column("workflows", "template_slug")
    op.drop_column("workflows", "is_template")
    op.drop_column("workflows", "status")
    op.drop_column("workflows", "version")
    op.drop_column("workflows", "organization_id")
    op.drop_column("workflows", "category")
