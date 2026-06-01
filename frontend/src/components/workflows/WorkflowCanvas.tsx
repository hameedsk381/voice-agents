'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { WorkflowNodeCard } from './WorkflowNodeCard';
import WorkflowNodeConfigPanel from './WorkflowNodeConfigPanel';
import {
  definitionToFlow,
  flowToDefinition,
  type WorkflowNodeData,
  NODE_TYPE_OPTIONS,
  nodeColor,
} from '@/lib/workflowFlow';

const nodeTypes = { workflowNode: WorkflowNodeCard } as NodeTypes;

type Props = {
  definition: Record<string, unknown>;
  name: string;
  description?: string;
  category?: string;
  onDefinitionChange: (def: Record<string, unknown>) => void;
};

export default function WorkflowCanvas({
  definition,
  name,
  description,
  category,
  onDefinitionChange,
}: Props) {
  const initial = useMemo(() => definitionToFlow(definition), [definition]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    const { nodes: n, edges: e } = definitionToFlow(definition);
    setNodes(n);
    setEdges(e);
  }, [definition, setNodes, setEdges]);

  const syncToParent = useCallback(
    (n: Node<WorkflowNodeData>[], e: Edge[]) => {
      const def = flowToDefinition(n, e, {
        name,
        description,
        category,
        entry: definition.entry as string | undefined,
      });
      onDefinitionChange(def);
    },
    [name, description, category, definition.entry, onDefinitionChange]
  );

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => {
        const next = addEdge(params, eds);
        syncToParent(nodes, next);
        return next;
      });
    },
    [nodes, setEdges, syncToParent]
  );

  const onNodesDragStop = useCallback(() => {
    syncToParent(nodes, edges);
  }, [nodes, edges, syncToParent]);

  const addNode = (type: string) => {
    const id = `${type}_${Date.now().toString(36).slice(-4)}`;
    const newNode: Node<WorkflowNodeData> = {
      id,
      type: 'workflowNode',
      position: { x: 80 + nodes.length * 40, y: 80 + nodes.length * 30 },
      data: {
        label: NODE_TYPE_OPTIONS.find((o) => o.value === type)?.label || type,
        nodeType: type,
        config: type === 'voice_call' ? { max_attempts: 3 } : type === 'wait' ? { minutes: 60 } : type === 'recorded_audio' ? { audio_url: '', audio_file: '' } : {},
      },
    };
    const nextNodes = [...nodes, newNode];
    setNodes(nextNodes);
    syncToParent(nextNodes, edges);
  };

  const selectedNode = nodes.find((n) => n.id === selectedId) ?? null;

  const handleNodeConfigUpdate = (nodeId: string, data: WorkflowNodeData) => {
    const nextNodes = nodes.map((n) =>
      n.id === nodeId ? { ...n, data } : n
    );
    setNodes(nextNodes);
    syncToParent(nextNodes, edges);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
      <div className="h-[520px] rounded-2xl border border-[var(--border-default)] overflow-hidden bg-[var(--bg-overlay)]">
        <div className="flex flex-wrap gap-1 p-2 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          {NODE_TYPE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => addNode(opt.value)}
              className="px-2 py-1 text-[10px] font-semibold rounded-md border border-[var(--border-subtle)] hover:border-[var(--accent-cyan)] text-[var(--text-secondary)]"
            >
              + {opt.label}
            </button>
          ))}
        </div>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDragStop={onNodesDragStop}
          onNodeClick={(_, n) => setSelectedId(n.id)}
          onPaneClick={() => setSelectedId(null)}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={16} color="var(--border-subtle)" />
          <Controls />
          <MiniMap
            nodeColor={(n) => {
              const t = (n.data as WorkflowNodeData)?.nodeType;
              return t ? nodeColor(t) : '#888';
            }}
          />
        </ReactFlow>
      </div>
      <WorkflowNodeConfigPanel
        node={selectedNode}
        onUpdate={handleNodeConfigUpdate}
        onClose={() => setSelectedId(null)}
      />
    </div>
  );
}
