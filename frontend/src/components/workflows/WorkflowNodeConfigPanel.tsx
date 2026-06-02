'use client';

import type { Node } from '@xyflow/react';
import type { WorkflowNodeData } from '@/lib/workflowFlow';

type Props = {
  node: Node<WorkflowNodeData> | null;
  onUpdate: (nodeId: string, data: WorkflowNodeData) => void;
  onClose: () => void;
};

const SUGGESTED_FIELDS = [
  'aging_days', 'outstanding_amount', 'branch_code', 'vip_no_auto_call',
  'last_call_outcome', 'call_attempts', 'customer_name', 'customer_id',
  'workflow_outcome', 'escalated_to', 'hitl_approved', 'whatsapp_sent',
  'emails_sent', 'last_condition',
];

function ConditionRulesEditor({ config, setConfigField }: { config: any; setConfigField: (key: string, value: any) => void }) {
  const rules: any[] = Array.isArray(config.rules) ? config.rules : [];
  const match = config.match || 'all';

  const updateRule = (idx: number, key: string, value: any) => {
    const newRules = [...rules];
    newRules[idx] = { ...newRules[idx], [key]: value };
    setConfigField('rules', newRules);
  };

  const addRule = () => {
    setConfigField('rules', [...rules, { field: 'outstanding_amount', op: 'gt', value: 0 }]);
  };

  const removeRule = (idx: number) => {
    const newRules = [...rules];
    newRules.splice(idx, 1);
    setConfigField('rules', newRules);
  };

  const toggleJsonMode = () => {
    setConfigField('_jsonMode', !config._jsonMode);
  };

  if (config._jsonMode) {
    return (
      <div className="space-y-2 pt-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Rules (JSON)</span>
          <button type="button" onClick={toggleJsonMode} className="text-[10px] text-[var(--accent-cyan)] hover:underline">
            Visual mode
          </button>
        </div>
        <textarea
          aria-label="Rules JSON editor"
          rows={6}
          value={JSON.stringify({ match, rules }, null, 2)}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              if (parsed.match) setConfigField('match', parsed.match);
              if (parsed.rules) setConfigField('rules', parsed.rules);
            } catch {}
          }}
          className="w-full glass-input px-2 py-1.5 text-xs font-mono"
        />
      </div>
    );
  }

  return (
    <div className="space-y-3 pt-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Condition rules</span>
        <button type="button" onClick={toggleJsonMode} className="text-[10px] text-[var(--text-tertiary)] hover:text-[var(--accent-cyan)]">
          JSON mode
        </button>
      </div>

      <label className="block space-y-1">
        <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Match condition</span>
        <select
          value={match}
          onChange={(e) => setConfigField('match', e.target.value)}
          className="w-full glass-input px-2 py-1.5 text-sm"
        >
          <option value="all">Match ALL rules (AND)</option>
          <option value="any">Match ANY rule (OR)</option>
        </select>
      </label>

      <div className="space-y-2">
        {rules.map((rule, idx) => (
          <div key={idx} className="flex flex-col gap-1 rounded-xl bg-[var(--bg-default)] p-2 border border-[var(--border-default)]">
            <div className="flex gap-1">
              <input
                list="field-suggestions"
                placeholder="Field name"
                value={rule.field || ''}
                onChange={e => updateRule(idx, 'field', e.target.value)}
                className="glass-input px-2 py-1 text-xs w-1/2"
              />
              <select
                value={rule.op || 'eq'}
                onChange={e => updateRule(idx, 'op', e.target.value)}
                className="glass-input px-1 py-1 text-xs w-1/3"
              >
                <option value="eq">==</option>
                <option value="neq">!=</option>
                <option value="gt">&gt;</option>
                <option value="gte">&gt;=</option>
                <option value="lt">&lt;</option>
                <option value="lte">&lt;=</option>
                <option value="contains">contains</option>
                <option value="in">in</option>
              </select>
              <button type="button" onClick={() => removeRule(idx)} className="text-[var(--status-error)] px-1 hover:bg-[var(--status-error-bg)] rounded">✕</button>
            </div>
            <input
              placeholder="Value"
              value={rule.value ?? ''}
              onChange={e => updateRule(idx, 'value', e.target.value)}
              className="glass-input px-2 py-1 text-xs w-full"
            />
          </div>
        ))}
        <datalist id="field-suggestions">
          {SUGGESTED_FIELDS.map(f => <option key={f} value={f} />)}
        </datalist>
        <button type="button" onClick={addRule} className="text-xs text-[var(--accent-cyan)] hover:underline mt-1">+ Add Rule</button>
      </div>
    </div>
  );
}

export default function WorkflowNodeConfigPanel({ node, onUpdate, onClose }: Props) {
  if (!node) {
    return (
      <div className="rounded-2xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-4 text-xs text-[var(--text-tertiary)]">
        Select a node on the canvas to edit its label and settings.
      </div>
    );
  }

  const d = node.data;
  const config: Record<string, any> = { ...(d.config || {}) };

  const setLabel = (label: string) => {
    onUpdate(node.id, { ...d, label });
  };

  const setConfigField = (key: string, value: unknown) => {
    onUpdate(node.id, { ...d, config: { ...config, [key]: value } });
  };

  return (
    <div className="rounded-2xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-4 space-y-4 max-h-[520px] overflow-y-auto">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)]">
          Node config
        </p>
        <button
          type="button"
          onClick={onClose}
          className="text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
        >
          Close
        </button>
      </div>
      <p className="text-[10px] text-[var(--text-tertiary)] font-mono">{node.id}</p>
      <p className="text-[10px] font-semibold text-[var(--accent-cyan)]">{d.nodeType}</p>

      <label className="block space-y-1">
        <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Label</span>
        <input
          value={d.label}
          onChange={(e) => setLabel(e.target.value)}
          className="w-full glass-input px-2 py-1.5 text-sm"
        />
      </label>

      {d.nodeType === 'voice_call' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Max attempts</span>
            <input
              type="number"
              min={1}
              max={10}
              value={Number(config.max_attempts ?? 3)}
              onChange={(e) => setConfigField('max_attempts', Number(e.target.value))}
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
        </>
      )}

      {d.nodeType === 'wait' && (
        <label className="block space-y-1">
          <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Minutes</span>
          <input
            type="number"
            min={1}
            value={Number(config.minutes ?? 60)}
            onChange={(e) => setConfigField('minutes', Number(e.target.value))}
            className="w-full glass-input px-2 py-1.5 text-sm"
          />
        </label>
      )}

      {d.nodeType === 'email' && (
        <label className="block space-y-1">
          <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Template</span>
          <select
            value={String(config.template ?? 'payment_reminder')}
            onChange={(e) => setConfigField('template', e.target.value)}
            className="w-full glass-input px-2 py-1.5 text-sm"
          >
            <option value="payment_reminder">payment_reminder</option>
            <option value="lead_nurture">lead_nurture</option>
            <option value="appointment_confirm">appointment_confirm</option>
          </select>
        </label>
      )}

      {d.nodeType === 'whatsapp' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Template</span>
            <select
              value={String(config.template ?? 'payment_reminder')}
              onChange={(e) => setConfigField('template', e.target.value)}
              className="w-full glass-input px-2 py-1.5 text-sm"
            >
              <option value="payment_reminder">payment_reminder</option>
              <option value="lead_nurture">lead_nurture</option>
              <option value="appointment_confirm">appointment_confirm</option>
              <option value="payment_received">payment_received</option>
              <option value="escalation_notice">escalation_notice</option>
            </select>
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
              Message body <span className="text-[var(--text-tertiary)]">(optional — uses template if blank)</span>
            </span>
            <textarea
              rows={3}
              value={String(config.message ?? '')}
              onChange={(e) => setConfigField('message', e.target.value)}
              placeholder="Use {{customer_name}}, {{outstanding_amount}}, etc."
              className="w-full glass-input px-2 py-1.5 text-xs"
            />
          </label>
        </>
      )}

      {d.nodeType === 'hitl_approval' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Action type</span>
            <input
              value={String(config.action_type ?? 'workflow_approval')}
              onChange={(e) => setConfigField('action_type', e.target.value)}
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Description</span>
            <textarea
              rows={2}
              value={String(config.description ?? '')}
              onChange={(e) => setConfigField('description', e.target.value)}
              className="w-full glass-input px-2 py-1.5 text-xs"
            />
          </label>
        </>
      )}

      {d.nodeType === 'sms' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
              Message body <span className="text-[var(--text-tertiary)]">(use {'{{customer_name}}'} etc.)</span>
            </span>
            <textarea
              rows={3}
              value={String(config.message ?? '')}
              onChange={(e) => setConfigField('message', e.target.value)}
              placeholder="Dear {{customer_name}}, your payment of ₹{{outstanding_amount}} is due."
              className="w-full glass-input px-2 py-1.5 text-xs"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
              To phone <span className="text-[var(--text-tertiary)]">(optional — defaults to context phone_number)</span>
            </span>
            <input
              value={String(config.to_phone ?? '')}
              onChange={(e) => setConfigField('to_phone', e.target.value)}
              placeholder="+919999999999"
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
        </>
      )}

      {d.nodeType === 'webhook' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">URL</span>
            <input
              value={String(config.url ?? '')}
              onChange={(e) => setConfigField('url', e.target.value)}
              placeholder="https://api.example.com/endpoint"
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Method</span>
            <select
              value={String(config.method ?? 'POST')}
              onChange={(e) => setConfigField('method', e.target.value)}
              className="w-full glass-input px-2 py-1.5 text-sm"
            >
              <option value="POST">POST</option>
              <option value="GET">GET</option>
            </select>
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
              Headers (JSON) <span className="text-[var(--text-tertiary)]">supports {'{{var}}'}</span>
            </span>
            <textarea
              rows={3}
              value={config.headers ? JSON.stringify(config.headers, null, 2) : '{}'}
              onChange={(e) => {
                try { setConfigField('headers', JSON.parse(e.target.value)); } catch {}
              }}
              className="w-full glass-input px-2 py-1.5 text-xs font-mono"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
              Body template <span className="text-[var(--text-tertiary)]">supports {'{{var}}'}</span>
            </span>
            <textarea
              rows={3}
              value={String(config.body_template ?? '')}
              onChange={(e) => setConfigField('body_template', e.target.value)}
              placeholder='{"customer":"{{customer_name}}","amount":{{outstanding_amount}}}'
              className="w-full glass-input px-2 py-1.5 text-xs font-mono"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Response key</span>
            <input
              value={String(config.response_key ?? 'webhook_response')}
              onChange={(e) => setConfigField('response_key', e.target.value)}
              placeholder="webhook_response"
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
        </>
      )}

      {d.nodeType === 'db_query' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
              SQL query <span className="text-[var(--text-tertiary)]">use :param_name from context</span>
            </span>
            <textarea
              rows={4}
              value={String(config.query ?? '')}
              onChange={(e) => setConfigField('query', e.target.value)}
              placeholder="SELECT name, email FROM customers WHERE id = :customer_id"
              className="w-full glass-input px-2 py-1.5 text-xs font-mono"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Result key</span>
            <input
              value={String(config.result_key ?? 'query_result')}
              onChange={(e) => setConfigField('result_key', e.target.value)}
              placeholder="query_result"
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
        </>
      )}

      {d.nodeType === 'agent_task' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Capability</span>
            <input
              value={String(config.capability ?? '')}
              onChange={(e) => setConfigField('capability', e.target.value)}
              placeholder="collections, sales, support, etc."
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Task input</span>
            <textarea
              rows={2}
              value={String(config.input ?? '')}
              onChange={(e) => setConfigField('input', e.target.value)}
              placeholder="Instructions for the target agent"
              className="w-full glass-input px-2 py-1.5 text-xs"
            />
          </label>
        </>
      )}

      {d.nodeType === 'fork' && (
        <label className="block space-y-1">
          <span className="text-[10px] font-semibold text-[var(--text-secondary)]">
            Branch start node IDs <span className="text-[var(--text-tertiary)]">(comma-separated)</span>
          </span>
          <input
            value={String((config.branches as string[] ?? []).join(', '))}
            onChange={(e) => setConfigField('branches', e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean))}
            placeholder="branch1_start, branch2_start"
            className="w-full glass-input px-2 py-1.5 text-sm"
          />
          <p className="text-[10px] text-[var(--text-tertiary)] mt-1">
            Each branch should end at a join node. Connect the fork's <strong>next</strong> edge to the join node.
          </p>
        </label>
      )}

      {d.nodeType === 'join' && (
        <p className="text-xs text-[var(--text-tertiary)]">
          Merge point for fork branches. Connect branch end nodes here. All branches must reach this node before execution continues.
        </p>
      )}

      {d.nodeType === 'escalate' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Owner role</span>
            <input
              value={String(config.owner_role ?? 'account_owner')}
              onChange={(e) => setConfigField('owner_role', e.target.value)}
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Routing Phone Number</span>
            <input
              value={String(config.routing_number ?? '')}
              onChange={(e) => setConfigField('routing_number', e.target.value)}
              placeholder="+1234567890"
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Priority</span>
            <select
              value={String(config.priority ?? 'medium')}
              onChange={(e) => setConfigField('priority', e.target.value)}
              className="w-full glass-input px-2 py-1.5 text-sm"
            >
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
          </label>
        </>
      )}

      {d.nodeType === 'end' && (
        <label className="block space-y-1">
          <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Outcome</span>
          <input
            value={String(config.outcome ?? 'completed')}
            onChange={(e) => setConfigField('outcome', e.target.value)}
            className="w-full glass-input px-2 py-1.5 text-sm"
          />
        </label>
      )}

      {d.nodeType === 'qa_node' && (
        <>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">LLM Evaluator Model</span>
            <select
              value={String(config.evaluator_model ?? 'llama-3.3-70b-versatile')}
              onChange={(e) => setConfigField('evaluator_model', e.target.value)}
              className="w-full glass-input px-2 py-1.5 text-sm"
            >
              <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Groq)</option>
              <option value="llama-3.1-8b-instant">Llama 3.1 8B (Groq)</option>
            </select>
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Evaluation Rubric (Prompt)</span>
            <textarea
              rows={4}
              value={String(config.rubric ?? '')}
              onChange={(e) => setConfigField('rubric', e.target.value)}
              placeholder="e.g. Did the agent successfully collect the user's email? Answer yes or no."
              className="w-full glass-input px-2 py-1.5 text-xs"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[10px] font-semibold text-[var(--text-secondary)]">Expected Outcome</span>
            <input
              value={String(config.expected_outcome ?? 'yes')}
              onChange={(e) => setConfigField('expected_outcome', e.target.value)}
              placeholder="yes"
              className="w-full glass-input px-2 py-1.5 text-sm"
            />
          </label>
          <p className="text-[10px] text-[var(--text-tertiary)] mt-1">
            Uses LLM to evaluate the prompt. Routes to <strong className="text-[var(--status-success)]">yes</strong> edge if it matches expected outcome, <strong className="text-[var(--status-error)]">no</strong> otherwise.
          </p>
        </>
      )}

      {d.nodeType === 'condition' && (
        <ConditionRulesEditor config={config} setConfigField={setConfigField} />
      )}
    </div>
  );
}
