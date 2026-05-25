'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Sparkles, Loader2, Check, Bot, Phone, Mail, Clock, GitBranch, AlertTriangle, SendHorizontal } from 'lucide-react';
import api from '@/lib/api';
import { nodeColor } from '@/lib/workflowFlow';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

const EXAMPLES = [
  {
    label: "Payment reminder",
    prompt: "Call customer up to 3 times with 4 hour gap. If no answer, send email. If answered and they promise to pay, mark success. If over 120 days overdue, get legal approval then escalate to legal team.",
  },
  {
    label: "Lead follow-up",
    prompt: "Call lead twice (2 hour gap). If they book a demo, done. If not, send nurture email.",
  },
  {
    label: "Appointment confirm",
    prompt: "Call to confirm appointment. If answer and confirmed, mark success. If no answer after 2 tries, send confirmation email.",
  },
  {
    label: "VIP customer flow",
    prompt: "If VIP customer (vip_no_auto_call), skip auto-call and escalate to relationship manager. Otherwise call 3 times, then email if no answer.",
  },
  {
    label: "भुगतान अनुस्मारक",
    prompt: "ग्राहक को 3 बार कॉल करें, 4 घंटे का अंतराल। कोई जवाब नहीं तो ईमेल भेजें। 120 दिनों से अधिक बकाया हो तो कानूनी टीम को एस्केलेट करें।",
  },
];

const NODE_ICONS: Record<string, typeof Bot> = {
  voice_call: Phone,
  email: Mail,
  wait: Clock,
  condition: GitBranch,
  hitl_approval: AlertTriangle,
  escalate: AlertTriangle,
  end: Check,
};

function getNodeEmoji(type: string): string {
  const map: Record<string, string> = {
    voice_call: '📞',
    email: '📧', 
    wait: '⏳',
    condition: '🔀',
    hitl_approval: '👤',
    escalate: '🚨',
    end: '✅',
    whatsapp: '💬',
    start: '▶️',
  };
  return map[type] || '•';
}

function StepCard({ node, index }: { node: any; index: number }) {
  const color = nodeColor(node.type);
  const label = node.label || node.id;
  const config = node.config || {};

  let detail = '';
  if (node.type === 'voice_call' && config.max_attempts) detail = `Max ${config.max_attempts} attempts`;
  else if (node.type === 'wait' && config.minutes) detail = `${config.minutes} min wait`;
  else if (node.type === 'condition') {
    const rules = config.rules || [];
    detail = rules.map((r: any) => `${r.field} ${r.op} ${r.value}`).join(', ');
  }
  else if (node.type === 'email') detail = config.template || '';

  return (
    <div className="flex items-start gap-3 group">
      <div className="flex flex-col items-center">
        <div
          className="size-10 rounded-xl flex items-center justify-center text-lg font-semibold shadow-sm shrink-0"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {getNodeEmoji(node.type)}
        </div>
        {index < 0 && (
          <div className="w-0.5 h-8 bg-border" />
        )}
      </div>
      <div className="flex-1 min-w-0 pt-1.5">
        <p className="text-sm font-semibold text-foreground capitalize">
          {node.type.replace(/_/g, ' ')}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{label}</p>
        {detail && (
          <p className="text-[10px] text-muted-foreground/70 mt-0.5 font-mono truncate">{detail}</p>
        )}
        {node.on_true && (
          <p className="text-[10px] text-green-600 mt-0.5">✅ If yes → {node.on_true}</p>
        )}
        {node.on_false && (
          <p className="text-[10px] text-red-500 mt-0.5">❌ If no → {node.on_false}</p>
        )}
        {node.next && !node.on_true && (
          <p className="text-[10px] text-muted-foreground/50 mt-0.5">→ {node.next}</p>
        )}
      </div>
    </div>
  );
}

function NewWorkflowForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const templateSlug = searchParams.get('template');

  const [prompt, setPrompt] = useState('');
  const [generated, setGenerated] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setGenerated(null);
    try {
      const res = await api.post('/workflows/ai/generate', { prompt: prompt.trim() });
      setGenerated(res.definition);
    } catch (e: any) {
      setError(e?.message || 'Failed to generate. Please try again with a simpler description.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!generated) return;
    setSaving(true);
    setError(null);
    try {
      const name = generated.name || prompt.trim().slice(0, 60);
      const wf = await api.post('/workflows', {
        name,
        description: generated.description || '',
        category: generated.category || 'custom',
        definition: generated,
        status: 'draft',
      });
      router.push(`/dashboard/workflows/${wf.id}`);
    } catch (e: any) {
      setError(e?.message || 'Failed to save workflow');
    } finally {
      setSaving(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setPrompt(example);
  };

  if (templateSlug) {
    return (
      <div className="space-y-6 pb-10 max-w-4xl">
        <Link href="/dashboard/workflows" className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="size-4" />
          Back to workflows
        </Link>
        <div className="bg-card border text-card-foreground shadow-sm rounded-xl p-8 text-center">
          <Loader2 className="size-8 animate-spin text-muted-foreground mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">Loading template…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-10 max-w-4xl">
      <Link href="/dashboard/workflows" className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" />
        Back to workflows
      </Link>

      <div className="flex items-center gap-3">
        <div className="size-10 rounded-xl bg-primary/10 flex items-center justify-center">
          <Sparkles className="size-5 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-foreground">AI Workflow Builder</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Describe your workflow in plain English or Hindi — the AI will build it for you.
          </p>
        </div>
      </div>

      <Card className="hover:shadow-md transition-all">
        <CardHeader>
          <CardTitle className="text-base">Describe your workflow</CardTitle>
          <CardDescription className="text-xs">Provide a step-by-step description of what your automated agent should execute.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            className="flex min-h-[100px] w-full rounded-xl border border-input bg-transparent px-4 py-3 text-sm leading-relaxed shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50 resize-none"
            placeholder="e.g. Call customer 3 times with gaps of 4 hours. If no answer, send email. If 120+ days overdue, escalate to Legal team."
          />
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <Button
                key={ex.label}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleExampleClick(ex.prompt)}
                className="h-8 rounded-lg text-[10px] font-semibold text-muted-foreground hover:text-foreground"
              >
                {ex.label}
              </Button>
            ))}
          </div>
          {error && (
            <p className="text-xs text-red-500 bg-red-500/10 px-3 py-2 rounded-lg">{error}</p>
          )}
          <Button
            type="button"
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="gap-2 rounded-xl text-sm font-semibold cursor-pointer shrink-0"
          >
            {loading ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Generating workflow...
              </>
            ) : (
              <>
                <Sparkles className="size-4" />
                Generate Workflow
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {generated && (
        <div className="space-y-4 animate-fade">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="size-5 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">{generated.name || 'Generated Workflow'}</h3>
              <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary text-[9px] font-semibold uppercase tracking-wider border border-primary/20">
                {generated.category || 'custom'}
              </span>
            </div>
          </div>

          {generated.description && (
            <p className="text-xs text-muted-foreground">{generated.description}</p>
          )}

          <Card className="overflow-hidden">
            <CardHeader className="px-5 py-3 border-b border-border bg-muted/30 flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Workflow Steps ({generated.nodes?.length || 0})
              </CardTitle>
              <span className="text-[9px] font-mono text-muted-foreground/50">
                Entry: {generated.entry}
              </span>
            </CardHeader>
            <CardContent className="p-5 space-y-5">
              {generated.nodes?.map((node: any, i: number) => (
                <StepCard key={node.id || i} node={node} index={i} />
              ))}
              {(!generated.nodes || generated.nodes.length === 0) && (
                <p className="text-xs text-muted-foreground text-center py-6">
                  No steps generated. Try a more detailed description.
                </p>
              )}
            </CardContent>
          </Card>

          <div className="flex items-center gap-3">
            <Button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="gap-2 rounded-xl text-sm font-semibold cursor-pointer"
            >
              {saving ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="size-4" />
                  Save & Open in Editor
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => { setGenerated(null); setPrompt(''); }}
              className="rounded-xl text-sm font-semibold"
            >
              Start over
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function NewWorkflowPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
      <NewWorkflowForm />
    </Suspense>
  );
}
