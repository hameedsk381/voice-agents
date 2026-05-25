'use client';

import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { WorkflowNodeData } from '@/lib/workflowFlow';
import { nodeColor } from '@/lib/workflowFlow';

export function WorkflowNodeCard({ data, selected }: NodeProps) {
  const d = data as WorkflowNodeData;
  const color = nodeColor(d.nodeType);
  const isCondition = d.nodeType === 'condition';

  return (
    <div
      className={`min-w-[180px] rounded-xl border-2 px-3 py-2 shadow-md transition-all ${
        selected ? 'ring-2 ring-[var(--accent-cyan)]' : ''
      }`}
      style={{
        borderColor: color,
        background: 'var(--glass-card-bg)',
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-[var(--text-tertiary)]" />
      <p className="text-[9px] font-bold uppercase tracking-wider" style={{ color }}>
        {d.nodeType.replace('_', ' ')}
      </p>
      <p className="text-xs font-semibold text-[var(--text-primary)] mt-0.5">{d.label}</p>
      {isCondition && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            style={{ top: '40%', background: '#10B981' }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            style={{ background: '#F43F5E' }}
          />
        </>
      )}
      {!isCondition && d.nodeType !== 'end' && (
        <Handle type="source" position={Position.Bottom} className="!bg-[var(--accent-cyan)]" />
      )}
    </div>
  );
}
