'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import {
  ArrowLeft,
  Save,
  Play,
  CheckCircle,
  RefreshCw,
  Layout,
  FileJson,
  Upload,
  Clock,
} from 'lucide-react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const WorkflowCanvas = dynamic(() => import('@/components/workflows/WorkflowCanvas'), {
  ssr: false,
});

type Tab = 'visual' | 'sap' | 'test';

type Workflow = {
  id: string;
  name: string;
  description?: string;
  status: string;
  category?: string;
  definition: Record<string, unknown>;
};

type Instance = {
  id: string;
  status: string;
  current_node_id?: string;
  outcome?: string;
};

export default function WorkflowEditorPage() {
  const params = useParams();
  const id = params.id as string;

  const [tab, setTab] = useState<Tab>('visual');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [definition, setDefinition] = useState<Record<string, unknown>>({});
  const [definitionJson, setDefinitionJson] = useState('');
  const [name, setName] = useState('');
  const [instances, setInstances] = useState<Instance[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [sapFile, setSapFile] = useState<File | null>(null);
  const [sapCampaignName, setSapCampaignName] = useState('');
  const [sapAgentId, setSapAgentId] = useState('');
  const [agents, setAgents] = useState<{ id: string; name: string }[]>([]);
  const [testContext, setTestContext] = useState(
    JSON.stringify(
      {
        customer_name: 'Maria Gonzalez',
        customer_id: 'C-1001',
        email: 'maria@example.com',
        outstanding_amount: 284.5,
        aging_bucket: '31-60',
        aging_days: 45,
        branch_code: 'BR-01',
        vip_no_auto_call: false,
      },
      null,
      2
    )
  );

  const load = useCallback(async () => {
    try {
      const wf = await api.get(`/workflows/${id}`);
      setWorkflow(wf);
      setName(wf.name);
      setDefinition(wf.definition || {});
      setDefinitionJson(JSON.stringify(wf.definition, null, 2));
      const instList = await api.get(`/workflows/${id}/instances`);
      setInstances(instList);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
    api.get('/agents/').then((a) => setAgents(a)).catch(() => {});
  }, [load]);

  const handleSave = async (def?: Record<string, unknown>) => {
    setSaving(true);
    setMessage(null);
    try {
      const payload = def || JSON.parse(definitionJson);
      const wf = await api.put(`/workflows/${id}`, { name, definition: payload });
      setWorkflow(wf);
      setDefinition(wf.definition);
      setDefinitionJson(JSON.stringify(wf.definition, null, 2));
      setMessage('Saved');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async () => {
    await handleSave(definition);
    try {
      const wf = await api.post(`/workflows/${id}/publish`, {});
      setWorkflow(wf);
      setMessage('Published — ready for campaigns & SAP ingest');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Publish failed');
    }
  };

  const handleSapIngest = async () => {
    if (!sapFile) {
      setMessage('Select a CSV file');
      return;
    }
    const fd = new FormData();
    fd.append('file', sapFile);
    const q = new URLSearchParams({
      workflow_id: id,
      auto_start: 'true',
    });
    if (sapCampaignName) q.set('create_campaign_name', sapCampaignName);
    if (sapAgentId) q.set('agent_id', sapAgentId);
    try {
      const res = await api.postFormData(`/workflows/ingest/sap-csv?${q}`, fd);
      setMessage(
        `SAP ingest: ${res.instances_started} instances, ${res.contacts_added} contacts (campaign ${res.campaign_id?.slice(0, 8) || '—'})`
      );
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'SAP ingest failed');
    }
  };

  const handleProcessDue = async () => {
    try {
      const res = await api.post('/workflows/process-due', {});
      setMessage(`Processed ${res.processed} due instances`);
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Process due failed');
    }
  };

  const tabs: { id: Tab; label: string; icon: typeof Layout }[] = [
    { id: 'visual', label: 'Editor', icon: Layout },
    { id: 'sap', label: 'Import data', icon: Upload },
    { id: 'test', label: 'Test & runs', icon: Play },
  ];

  if (loading) return <p className="text-sm text-muted-foreground">Loading workflow…</p>;
  if (!workflow) return <p className="text-sm text-red-600">Workflow not found</p>;

  return (
    <div className="space-y-6 pb-10">
      <Link
        href="/dashboard/workflows"
        className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        Workflows
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="text-xl font-bold bg-transparent border-0 hover:bg-muted/50 focus:bg-muted/80 h-10 px-3 w-72 rounded-xl text-foreground focus-visible:ring-1 focus-visible:ring-primary shadow-none"
          />
          <p className="text-xs text-muted-foreground mt-1 px-3">
            Status: <span className="font-semibold text-primary">{workflow.status}</span>
            {workflow.status !== 'active' && ' — publish before SAP ingest or campaigns'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => handleSave()}
            disabled={saving}
            className="gap-2 rounded-xl text-sm font-semibold"
          >
            <Save className="size-4" />
            Save
          </Button>
          <Button
            type="button"
            onClick={handlePublish}
            className="gap-2 rounded-xl text-sm font-semibold cursor-pointer"
          >
            <CheckCircle className="size-4" />
            Publish
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={handleProcessDue}
            className="gap-2 rounded-xl text-sm font-semibold"
            title="Resume instances past wait time"
          >
            <Clock className="size-4" />
            Process due
          </Button>
        </div>
      </div>

      {message && (
        <p className="text-xs font-medium text-green-600 bg-green-500/10 px-4 py-2 rounded-lg">
          {message}
        </p>
      )}

      <div className="flex gap-1 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 -mb-px transition-colors ${
              tab === t.id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
        <Button
          type="button"
          variant="ghost"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="ml-auto flex items-center gap-1.5 h-8 px-3 text-[10px] font-semibold rounded-lg"
        >
          <FileJson className="size-3" />
          {showAdvanced ? 'Hide advanced' : 'Advanced'}
        </Button>
      </div>

      {tab === 'visual' && (
        <div className="space-y-4">
          <WorkflowCanvas
            definition={definition}
            name={name}
            description={workflow.description}
            category={workflow.category}
            onDefinitionChange={(def) => {
              setDefinition(def);
              setDefinitionJson(JSON.stringify(def, null, 2));
            }}
          />
          {showAdvanced && (
            <details open>
              <summary className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground cursor-pointer select-none mb-2">
                Workflow JSON (advanced)
              </summary>
              <textarea
                value={definitionJson}
                onChange={(e) => setDefinitionJson(e.target.value)}
                rows={16}
                className="w-full font-mono text-xs bg-card border text-card-foreground shadow-sm rounded-xl p-4 glass-input"
                spellCheck={false}
              />
            </details>
          )}
        </div>
      )}

      {tab === 'sap' && (
        <Card className="max-w-xl hover:shadow-md transition-all">
          <CardHeader>
            <CardTitle className="text-base">Import SAP Data</CardTitle>
            <CardDescription className="text-xs">
              Upload an SAP AR export (CSV) to trigger automated workflow runs.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-muted-foreground leading-relaxed">
              Required column: <code>phone_number</code> or <code>contact_number</code>. Optional: customer_name, customer_id, outstanding_amount, invoice_number, due_date, aging_bucket, email, branch_code.
            </p>
            <div className="space-y-1.5">
              <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">CSV Export File</Label>
              <Input
                type="file"
                accept=".csv"
                onChange={(e) => setSapFile(e.target.files?.[0] || null)}
                className="text-xs file:bg-primary/10 file:text-primary file:rounded file:px-2 file:py-0.5 border-dashed cursor-pointer"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Campaign Name</Label>
              <Input
                placeholder="New campaign name (optional)"
                value={sapCampaignName}
                onChange={(e) => setSapCampaignName(e.target.value)}
                className="bg-muted text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Assigned Agent</Label>
              <select
                value={sapAgentId}
                onChange={(e) => setSapAgentId(e.target.value)}
                className="w-full bg-muted border border-border rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Agent for new campaign (optional)</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </div>
            <Button
              type="button"
              onClick={handleSapIngest}
              className="w-full font-semibold rounded-xl text-sm shadow-md hover:opacity-95"
            >
              Ingest & start workflows
            </Button>
          </CardContent>
        </Card>
      )}

      {tab === 'test' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="hover:shadow-md transition-all">
            <CardHeader>
              <CardTitle className="text-base">Test Context</CardTitle>
              <CardDescription className="text-xs">Provide sample JSON context variables to simulate workflow execution.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <textarea
                value={testContext}
                onChange={(e) => setTestContext(e.target.value)}
                rows={10}
                className="flex min-h-[160px] w-full font-mono text-xs rounded-xl border border-input bg-transparent px-4 py-3 shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
              />
              <Button
                type="button"
                onClick={async () => {
                  try {
                    const context = JSON.parse(testContext);
                    const inst = await api.post(`/workflows/${id}/instances`, {
                      context,
                      auto_start: true,
                    });
                    setMessage(`Run: ${inst.status}`);
                    await load();
                  } catch (e) {
                    setMessage(e instanceof Error ? e.message : 'Failed');
                  }
                }}
                className="w-full font-semibold rounded-xl text-sm shadow-md"
              >
                Start test instance
              </Button>
            </CardContent>
          </Card>
          <Card className="hover:shadow-md transition-all">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <RefreshCw className="size-4 text-primary" />
                Recent runs
              </CardTitle>
              <CardDescription className="text-xs">Real-time status of active or completed test instances.</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <ul className="space-y-3 mt-2">
                {instances.map((inst) => (
                  <li key={inst.id} className="p-4 rounded-xl bg-muted border border-border space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-primary capitalize text-xs">{inst.status}</span>
                      <span className="text-[10px] text-muted-foreground font-mono">{inst.current_node_id || 'End'}</span>
                    </div>
                    {inst.status === 'waiting' && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {['answered', 'no_answer', 'promise_to_pay'].map((o) => (
                          <Button
                            key={o}
                            type="button"
                            variant="outline"
                            size="sm"
                            className="h-7 text-[10px] font-semibold px-2.5 rounded-lg border-border"
                            onClick={async () => {
                              await api.post(`/workflows/instances/${inst.id}/advance`, {
                                last_call_outcome: o,
                              });
                              await load();
                            }}
                          >
                            {o.replace(/_/g, ' ')}
                          </Button>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
                {instances.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-8">No runs simulated yet.</p>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
