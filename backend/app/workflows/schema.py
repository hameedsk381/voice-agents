"""
Workflow definition schema v1 (JSON stored in Workflow.definition).

Designed for in-app builder first (JSON editor), visual canvas later.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    START = "start"
    CONDITION = "condition"
    VOICE_CALL = "voice_call"
    WAIT = "wait"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    WEBHOOK = "webhook"
    DB_QUERY = "db_query"
    HITL_APPROVAL = "hitl_approval"
    ESCALATE = "escalate"
    AGENT_TASK = "agent_task"
    FORK = "fork"
    JOIN = "join"
    END = "end"


class ConditionOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"


class ConditionRule(BaseModel):
    field: str
    op: ConditionOperator = ConditionOperator.EQ
    value: Any = None


class WorkflowNode(BaseModel):
    id: str
    type: NodeType
    label: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    next: Optional[str] = None
    on_true: Optional[str] = None
    on_false: Optional[str] = None


class WorkflowDefinitionV1(BaseModel):
    version: str = "1"
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    entry: str
    nodes: List[WorkflowNode]

    @field_validator("nodes")
    @classmethod
    def require_unique_ids(cls, nodes: List[WorkflowNode]) -> List[WorkflowNode]:
        ids = [n.id for n in nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Workflow node ids must be unique")
        return nodes

    def node_map(self) -> Dict[str, WorkflowNode]:
        return {n.id: n for n in self.nodes}

    def validate_graph(self) -> None:
        nm = self.node_map()
        if self.entry not in nm:
            raise ValueError(f"Entry node '{self.entry}' not found")
        for node in self.nodes:
            for ref in (node.next, node.on_true, node.on_false):
                if ref and ref not in nm:
                    raise ValueError(f"Node '{node.id}' references unknown node '{ref}'")


class StepResult(BaseModel):
    """Internal engine output after executing one node."""

    status: str  # continue | waiting | completed | failed
    next_node_id: Optional[str] = None
    message: Optional[str] = None
    context_patch: Dict[str, Any] = Field(default_factory=dict)
    wait_until: Optional[str] = None  # ISO datetime
