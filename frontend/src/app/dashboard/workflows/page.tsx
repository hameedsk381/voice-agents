'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { GitBranch, Plus, Sparkles, FileJson } from 'lucide-react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type WorkflowRow = {
  id: string;
  name: string;
  description?: string;
  category?: string;
  status: string;
  updated_at?: string;
};

type TemplateRow = {
  slug: string;
  name: string;
  description?: string;
  category?: string;
  node_count: number;
};

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowRow[]>([]);
  const [templates, setTemplates] = useState<TemplateRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [wfList, tplRes] = await Promise.all([
          api.get('/workflows'),
          api.get('/workflows/templates'),
        ]);
        setWorkflows(wfList);
        setTemplates(tplRes.templates || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 select-none">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            Workflow <span className="text-primary">Automation</span>
          </h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-xl">
            Describe what you need in plain English — AI will build the workflow for you, or start from a template.
          </p>
        </div>
        <Link href="/dashboard/workflows/new" passHref>
          <Button className="flex items-center gap-2 rounded-xl text-sm font-semibold shadow-lg shadow-primary/10">
            <Sparkles className="size-4" />
            AI Builder
          </Button>
        </Link>
      </div>

      {/* AI Build CTA */}
      <Card className="bg-gradient-to-br from-primary/5 via-background to-accent/5 border border-border/75 shadow-md relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-80 h-80 bg-primary/5 dark:bg-primary/5 blur-[80px] rounded-full pointer-events-none transition-all group-hover:scale-110" />
        <CardContent className="p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center gap-6">
          <div className="size-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shrink-0 shadow-md shadow-primary/10">
            <Sparkles className="size-5 text-white" />
          </div>
          <div className="flex-1 space-y-1">
            <h3 className="text-base font-semibold text-foreground">What would you like to automate?</h3>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-2xl">
              Describe in your own words — &quot;Call customers who haven&apos;t paid in 30 days, check their answers, then escalate to human team if required.&quot;
            </p>
          </div>
          <Link href="/dashboard/workflows/new" passHref>
            <Button className="bg-gradient-to-r from-primary to-accent text-white font-semibold rounded-xl text-sm shadow-md hover:opacity-95 cursor-pointer shrink-0 border-0 flex items-center gap-2">
              <Sparkles className="size-4" />
              Build with AI
            </Button>
          </Link>
        </CardContent>
      </Card>

      <section className="space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/75">
          Start from a template
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {templates.map((t) => (
            <Link key={t.slug} href={`/dashboard/workflows/new?template=${t.slug}`} className="group block">
              <Card className="h-full hover:shadow-md transition-all hover:border-primary/50 flex flex-col p-5">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-primary">
                  {t.category || 'template'}
                </span>
                <h4 className="text-sm font-semibold text-foreground mt-2 group-hover:text-primary transition-colors truncate">
                  {t.name}
                </h4>
                <p className="text-xs text-muted-foreground mt-2 line-clamp-2 leading-relaxed flex-1">
                  {t.description}
                </p>
                <div className="flex items-center justify-between border-t border-border/50 pt-3 mt-4 text-[10px] text-muted-foreground/75 font-mono">
                  <span>{t.node_count} nodes</span>
                  <span className="group-hover:text-primary transition-colors flex items-center gap-1 font-sans font-medium text-xs">
                    Use Template &rarr;
                  </span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/75">
          Your workflows
        </h3>
        {loading ? (
          <div className="grid gap-3">
            {[1, 2].map((i) => (
              <Card key={i} className="h-16 animate-pulse bg-muted/50" />
            ))}
          </div>
        ) : workflows.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="py-16 text-center text-muted-foreground">
              <FileJson className="size-10 text-primary mx-auto mb-4" />
              <p className="text-sm font-semibold text-foreground">No workflows yet</p>
              <p className="text-xs text-muted-foreground mt-1">Try the AI Builder above or start from a pre-made template.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {workflows.map((w) => (
              <Link key={w.id} href={`/dashboard/workflows/${w.id}`} className="block">
                <Card className="hover:shadow-md transition-all hover:border-primary/50 px-5 py-4 flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-foreground">{w.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {w.category || 'general'} · <span className="capitalize">{w.status}</span>
                    </p>
                  </div>
                  <Button variant="secondary" size="sm" className="text-xs font-semibold rounded-lg">
                    Edit Workflow
                  </Button>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
