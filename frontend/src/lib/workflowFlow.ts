/**
 * Convert workflow definition v1 <-> React Flow nodes/edges for the visual builder.
 */
import type { Node, Edge } from "@xyflow/react";

export type WorkflowNodeData = {
  label: string;
  nodeType: string;
  config: Record<string, unknown>;
  onTrue?: string;
  onFalse?: string;
};

const TYPE_COLORS: Record<string, string> = {
  condition: "#8B5CF6",
  voice_call: "#00D4AA",
  wait: "#F59E0B",
  email: "#6366F1",
  whatsapp: "#22C55E",
  sms: "#F97316",
  webhook: "#06B6D4",
  db_query: "#A855F7",
  hitl_approval: "#E11D48",
  escalate: "#F43F5E",
  agent_task: "#14B8A6",
  fork: "#8B5CF6",
  join: "#8B5CF6",
  qa_node: "#FACC15",
  end: "#52526B",
};

const COL_W = 220;
const ROW_H = 100;

export function nodeColor(type: string): string {
  return TYPE_COLORS[type] || "#8B8B9E";
}

export function definitionToFlow(definition: Record<string, unknown>): {
  nodes: Node<WorkflowNodeData>[];
  edges: Edge[];
} {
  const nodes = (definition.nodes as Array<Record<string, unknown>>) || [];
  const positions =
    (definition.canvas as { positions?: Record<string, { x: number; y: number }> })?.positions ||
    {};

  const flowNodes: Node<WorkflowNodeData>[] = nodes.map((n, i) => {
    const id = String(n.id);
    const type = String(n.type);
    const pos = positions[id] || { x: (i % 3) * COL_W, y: Math.floor(i / 3) * ROW_H };
    return {
      id,
      type: "workflowNode",
      position: pos,
      data: {
        label: String(n.label || id),
        nodeType: type,
        config: (n.config as Record<string, unknown>) || {},
        onTrue: n.on_true as string | undefined,
        onFalse: n.on_false as string | undefined,
      },
    };
  });

  const edges: Edge[] = [];
  for (const n of nodes) {
    const id = String(n.id);
    if (n.next) {
      edges.push({
        id: `${id}->${n.next}`,
        source: id,
        target: String(n.next),
        label: "next",
      });
    }
    if (n.on_true) {
      edges.push({
        id: `${id}-true->${n.on_true}`,
        source: id,
        target: String(n.on_true),
        sourceHandle: "true",
        label: "yes",
        style: { stroke: "#10B981" },
      });
    }
    if (n.on_false) {
      edges.push({
        id: `${id}-false->${n.on_false}`,
        source: id,
        target: String(n.on_false),
        sourceHandle: "false",
        label: "no",
        style: { stroke: "#F43F5E" },
      });
    }
  }

  return { nodes: flowNodes, edges };
}

export function flowToDefinition(
  nodes: Node<WorkflowNodeData>[],
  edges: Edge[],
  meta: { name?: string; description?: string; category?: string; entry?: string }
): Record<string, unknown> {
  const positions: Record<string, { x: number; y: number }> = {};
  const nodeDefs = nodes.map((fn) => {
    positions[fn.id] = fn.position;
    const outgoing = edges.filter((e) => e.source === fn.id);
    let next: string | undefined;
    let on_true: string | undefined;
    let on_false: string | undefined;

    for (const e of outgoing) {
      if (e.sourceHandle === "true") on_true = e.target;
      else if (e.sourceHandle === "false") on_false = e.target;
      else if (!next || e.label === "next") next = e.target;
    }

    const def: Record<string, unknown> = {
      id: fn.id,
      type: fn.data.nodeType,
      label: fn.data.label,
      config: fn.data.config || {},
    };
    if (next) def.next = next;
    if (on_true) def.on_true = on_true;
    if (on_false) def.on_false = on_false;
    return def;
  });

  const entry =
    meta.entry ||
    nodeDefs.find((n) => n.type === "condition")?.id ||
    nodeDefs[0]?.id ||
    "start";

  return {
    version: "1",
    name: meta.name,
    description: meta.description,
    category: meta.category,
    entry,
    nodes: nodeDefs,
    canvas: { positions },
  };
}

export const NODE_TYPE_OPTIONS = [
  { value: "condition", label: "Condition" },
  { value: "voice_call", label: "Voice call" },
  { value: "wait", label: "Wait" },
  { value: "email", label: "Email" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "sms", label: "SMS" },
  { value: "webhook", label: "Webhook" },
  { value: "db_query", label: "DB query" },
  { value: "hitl_approval", label: "Approval (HITL)" },
  { value: "escalate", label: "Escalate" },
  { value: "agent_task", label: "Agent task" },
  { value: "fork", label: "Fork" },
  { value: "join", label: "Join" },
  { value: "qa_node", label: "QA Check" },
  { value: "end", label: "End" },
];
