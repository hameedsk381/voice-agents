"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  PhoneIncoming,
  Plus,
  GitBranch,
  Users,
  Phone,
  Clock,
  CheckCircle,
  Activity,
  ArrowRight,
  ToggleLeft,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface InboundRule {
  id: string;
  name: string;
  phone_number: string;
  first_action: "agent" | "ivr" | "voicemail";
  calls_24h: number;
  success_rate: number;
  active: boolean;
  workflow_id?: string;
}

interface QueueStats {
  active_calls: number;
  avg_wait_seconds: number;
  agents_available: number;
  agents_busy: number;
}

const ACTION_LABELS: Record<string, string> = {
  agent: "AI Agent",
  ivr: "IVR Menu",
  voicemail: "Voicemail",
};

const ACTION_COLORS: Record<string, string> = {
  agent: "bg-primary/10 text-primary",
  ivr: "bg-accent/10 text-amber-600",
  voicemail: "bg-muted text-muted-foreground",
};

export default function InboundFlowsPage() {
  const [rules, setRules] = useState<InboundRule[]>([]);
  const [queue, setQueue] = useState<QueueStats>({ active_calls: 0, avg_wait_seconds: 0, agents_available: 0, agents_busy: 0 });
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    try {
      // Inbound rules and queue stats would come from /api/v1/telephony/inbound-rules
      // and /api/v1/monitoring/queue once those endpoints are added
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <div className="flex items-center justify-center size-9 rounded-lg bg-primary/10">
              <PhoneIncoming className="size-5 text-primary" />
            </div>
            Inbound{" "}
            <span className="text-primary">Flows</span>
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Configure how incoming calls are routed to AI agents, IVR menus, or voicemail.
          </p>
        </div>
        <Link href="/dashboard/workflows/new">
          <Button className="gap-2">
            <Plus className="size-4" />
            Create Flow
          </Button>
        </Link>
      </div>

      {/* Real-time queue strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Active Calls", value: queue.active_calls, icon: Phone, color: "text-green-600" },
          { label: "Avg Wait", value: `${queue.avg_wait_seconds}s`, icon: Clock, color: "text-accent" },
          { label: "Agents Available", value: queue.agents_available, icon: Users, color: "text-primary" },
          { label: "Agents Busy", value: queue.agents_busy, icon: Activity, color: "text-muted-foreground" },
        ].map((item) => (
          <Card key={item.label} className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <item.icon className={`size-4 ${item.color}`} />
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{item.label}</span>
            </div>
            <p className="text-2xl font-black text-foreground">{item.value}</p>
          </Card>
        ))}
      </div>

      {/* Config cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Users className="size-4 text-primary" />
              </div>
              <CardTitle className="text-sm">AI Agent Pool</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Assign agents to handle inbound calls. Callers are routed to the best-fit agent based on language and role.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/dashboard/agents">
              <Button variant="outline" className="w-full gap-2 text-xs h-8">
                Manage Agents <ArrowRight className="size-3.5" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-accent/10 flex items-center justify-center">
                <GitBranch className="size-4 text-amber-600" />
              </div>
              <CardTitle className="text-sm">IVR & Routing Rules</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Build call flow trees: greet callers, collect input, branch to agents or departments, or escalate to a human.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/dashboard/workflows">
              <Button variant="outline" className="w-full gap-2 text-xs h-8">
                Open Workflow Builder <ArrowRight className="size-3.5" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-muted flex items-center justify-center">
                <Phone className="size-4 text-muted-foreground" />
              </div>
              <CardTitle className="text-sm">Phone Numbers</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Assign inbound phone numbers to specific flows. Each number can route to a different agent or IVR tree.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/dashboard/phone-numbers">
              <Button variant="outline" className="w-full gap-2 text-xs h-8">
                Manage Numbers <ArrowRight className="size-3.5" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-lg bg-green-500/10 flex items-center justify-center">
                <CheckCircle className="size-4 text-green-600" />
              </div>
              <CardTitle className="text-sm">HITL Escalation</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Configure automatic escalation to human supervisors when agent confidence drops or customers request it.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/dashboard/approvals">
              <Button variant="outline" className="w-full gap-2 text-xs h-8">
                Escalation Rules <ArrowRight className="size-3.5" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Active rules table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Active Inbound Rules</CardTitle>
          <CardDescription>
            Phone numbers and the flows they trigger on incoming calls.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-10 rounded-lg bg-muted animate-pulse" />
              ))}
            </div>
          ) : rules.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center px-4">
              <div className="flex items-center justify-center size-14 rounded-full bg-primary/10 mb-4">
                <PhoneIncoming className="size-7 text-primary" />
              </div>
              <h3 className="text-base font-semibold text-foreground">No inbound flows yet</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs leading-relaxed">
                Create a workflow and link it to a phone number to start handling inbound calls with AI agents.
              </p>
              <Link href="/dashboard/workflows/new" className="mt-4">
                <Button variant="outline" className="gap-2">
                  Create Your First Flow
                  <ArrowRight className="size-4" />
                </Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/50 border-b border-border">
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Phone Number</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Flow Name</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">First Action</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Calls 24h</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Success</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-foreground">{rule.phone_number}</td>
                      <td className="px-4 py-3 font-medium text-foreground">{rule.name}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${ACTION_COLORS[rule.first_action]}`}>
                          {ACTION_LABELS[rule.first_action]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-foreground font-mono">{rule.calls_24h}</td>
                      <td className="px-4 py-3 text-foreground font-mono">{rule.success_rate}%</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-bold ${rule.active ? "text-green-600" : "text-muted-foreground"}`}>
                          <ToggleLeft className="size-3.5" />
                          {rule.active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {rule.workflow_id && (
                          <Link href={`/dashboard/workflows/${rule.workflow_id}`}>
                            <Button variant="ghost" className="h-7 px-2 text-xs gap-1">
                              Edit <ArrowRight className="size-3" />
                            </Button>
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
