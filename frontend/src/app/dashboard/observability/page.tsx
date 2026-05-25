"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2, Loader2, Activity, Bug, FlaskConical, Clock, BarChart3, ExternalLink, Gauge } from "lucide-react";
import api from "@/lib/api";

type Tab = "traces" | "failures" | "eval" | "metrics";

export default function ObservabilityPage() {
    const [activeTab, setActiveTab] = useState<Tab>("traces");
    const [traces, setTraces] = useState<any>(null);
    const [failures, setFailures] = useState<any>(null);
    const [evalRuns, setEvalRuns] = useState<any[]>([]);
    const [evalSuites, setEvalSuites] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [runningSuite, setRunningSuite] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const [traceSummary, failureData, evalData, suiteData] = await Promise.all([
                api.get("/observability/traces/summary?since_hours=24"),
                api.get("/observability/failures?limit=20"),
                api.get("/observability/eval/runs?limit=10"),
                api.get("/observability/eval/suites"),
            ]);
            setTraces(traceSummary);
            setFailures(failureData);
            setEvalRuns(evalData);
            setEvalSuites(suiteData.suites);
        } catch (error) {
            console.error("Failed to fetch observability data:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchData(); }, [fetchData]);

    const runEvalSuite = async (suiteName: string) => {
        setRunningSuite(suiteName);
        try {
            const result = await api.post(`/observability/eval/runs?suite_name=${suiteName}&model=llama-3.3-70b-versatile`, {});
            const runs = await api.get("/observability/eval/runs?limit=10");
            setEvalRuns(runs);
        } catch (error) {
            console.error("Eval run failed:", error);
        } finally {
            setRunningSuite(null);
        }
    };

    const tabs: { key: Tab; label: string; icon: any }[] = [
        { key: "traces", label: "Traces", icon: Activity },
        { key: "failures", label: "Failure Modes", icon: Bug },
        { key: "eval", label: "Evaluation", icon: FlaskConical },
        { key: "metrics", label: "Metrics", icon: Gauge },
    ];

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight">
                        <span className="text-primary">Observability</span>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        Traces, failure modes, and evaluation suite for your voice agents.
                    </p>
                </div>
                <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
                    <Activity className="w-3.5 h-3.5 mr-1.5" />
                    Refresh
                </Button>
            </div>

            {/* Tab bar */}
            <div className="flex gap-1 rounded-xl bg-muted/50 p-1 w-fit">
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        type="button"
                        onClick={() => setActiveTab(tab.key)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                            activeTab === tab.key
                                ? "bg-background shadow-sm text-foreground"
                                : "text-muted-foreground hover:text-foreground"
                        }`}
                    >
                        <tab.icon className="size-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="size-6 animate-spin text-primary" />
                </div>
            ) : (
                <>
                    {activeTab === "traces" && traces && (
                        <div className="space-y-6">
                            <div className="grid gap-4 md:grid-cols-4">
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium text-muted-foreground">Total Spans</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-semibold">{traces.total_spans}</div>
                                        <p className="text-xs text-muted-foreground mt-1">Last 24 hours</p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium text-muted-foreground">Error Spans</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-semibold text-red-600">{traces.error_spans}</div>
                                        <p className="text-xs text-muted-foreground mt-1">{traces.error_rate}% error rate</p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium text-muted-foreground">Avg Duration</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-semibold">{traces.avg_duration_ms} ms</div>
                                        <p className="text-xs text-muted-foreground mt-1">Across all spans</p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium text-muted-foreground">Service Health</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className={`text-2xl font-semibold flex items-center gap-2 ${traces.error_rate > 5 ? "text-red-600" : "text-green-600"}`}>
                                            {traces.error_rate > 5 ? (
                                                <><AlertCircle className="size-5" /> Degraded</>
                                            ) : (
                                                <><CheckCircle2 className="size-5" /> Healthy</>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <BarChart3 className="size-4 text-primary" />
                                        Span Breakdown by Type
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        {traces.by_type.map((t: any) => (
                                            <div key={t.span_type} className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
                                                <div>
                                                    <span className="text-sm font-medium capitalize">{t.span_type}</span>
                                                    <span className="text-xs text-muted-foreground ml-2">({t.count} spans)</span>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs text-muted-foreground">
                                                        <Clock className="size-3 inline mr-1" />
                                                        {t.avg_duration_ms} ms avg
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>

                            <div className="text-xs text-muted-foreground text-center">
                                Configure OTEL_EXPORTER_OTLP_ENDPOINT to send traces to an external observability backend (Grafana, SigNoz, etc.)
                            </div>
                        </div>
                    )}

                    {activeTab === "failures" && failures && (
                        <div className="space-y-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Bug className="size-4 text-red-500" />
                                        Aggregated Failure Patterns
                                    </CardTitle>
                                    <CardDescription>
                                        Most common failure modes grouped by span name and error message
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {failures.aggregated.length === 0 ? (
                                        <div className="text-center py-8 text-sm text-muted-foreground">
                                            <CheckCircle2 className="size-8 mx-auto mb-2 text-green-500" />
                                            No failures recorded. Your system is healthy.
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            {failures.aggregated.map((f: any, i: number) => (
                                                <div key={i} className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
                                                    <div className="flex-1">
                                                        <span className="text-sm font-medium">{f.span_name}</span>
                                                        <p className="text-xs text-muted-foreground mt-0.5">{f.status_message}</p>
                                                    </div>
                                                    <div className="flex items-center gap-4 text-xs text-right shrink-0">
                                                        <span className="font-mono text-red-600">{f.count}x</span>
                                                        <span className="text-muted-foreground">{f.avg_duration_ms}ms</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>Recent Failures</CardTitle>
                                    <CardDescription>Last {failures.recent?.length || 0} error spans</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {(failures.recent || []).length === 0 ? (
                                        <div className="text-center py-6 text-sm text-muted-foreground">No recent failures.</div>
                                    ) : (
                                        <div className="space-y-1">
                                            {failures.recent.map((f: any) => (
                                                <div key={f.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                                                    <div>
                                                        <span className="text-xs font-mono">{f.span_name}</span>
                                                        <span className="text-[10px] text-muted-foreground ml-2">{f.span_type}</span>
                                                        {f.status_message && (
                                                            <p className="text-[10px] text-muted-foreground truncate max-w-[300px]">{f.status_message}</p>
                                                        )}
                                                    </div>
                                                    <div className="text-[10px] text-muted-foreground text-right shrink-0 ml-4">
                                                        <div>{f.duration_ms}ms</div>
                                                        <div>{f.created_at ? new Date(f.created_at).toLocaleTimeString() : ""}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {activeTab === "metrics" && (
                        <div className="space-y-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Gauge className="size-4 text-primary" />
                                        Infrastructure Metrics
                                    </CardTitle>
                                    <CardDescription>
                                        Prometheus metrics are exposed at <code className="text-xs bg-muted px-1.5 py-0.5 rounded">/metrics</code> on the backend.
                                        The Grafana dashboard provides visualisation and alerting.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid gap-4 md:grid-cols-2">
                                        <a
                                            href="http://localhost:9090"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                                        >
                                            <div>
                                                <span className="font-medium">Prometheus</span>
                                                <p className="text-xs text-muted-foreground mt-0.5">localhost:9090</p>
                                            </div>
                                            <ExternalLink className="size-4 text-muted-foreground" />
                                        </a>
                                        <a
                                            href="http://localhost:3005"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                                        >
                                            <div>
                                                <span className="font-medium">Grafana</span>
                                                <p className="text-xs text-muted-foreground mt-0.5">admin / voise2026</p>
                                            </div>
                                            <ExternalLink className="size-4 text-muted-foreground" />
                                        </a>
                                    </div>
                                    <div className="rounded-lg bg-muted/50 p-4">
                                        <h4 className="text-sm font-medium mb-2">Available Metrics</h4>
                                        <ul className="space-y-1.5 text-xs text-muted-foreground">
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-primary shrink-0" /><code>http_requests_total</code> — request count by method/path/status</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-green-500 shrink-0" /><code>voice_calls_total</code> — call volume by agent and outcome</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-green-500 shrink-0" /><code>voice_call_duration_seconds</code> — call duration histogram</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-blue-500 shrink-0" /><code>voice_turn_latency_ms</code> — per-phase latency breakdown</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-yellow-500 shrink-0" /><code>voice_cost_total_usd</code> — accumulated cost by model</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-red-500 shrink-0" /><code>voice_errors_total</code> — error rate by type and source</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-purple-500 shrink-0" /><code>voice_active_sessions</code> — current active session count</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-purple-500 shrink-0" /><code>process_memory_usage_bytes</code> — backend RSS memory</li>
                                            <li className="flex items-center gap-2"><span className="size-1.5 rounded-full bg-purple-500 shrink-0" /><code>temporal_active_workflows</code> — active Temporal executions</li>
                                        </ul>
                                    </div>
                                    <div className="text-xs text-muted-foreground text-center">
                                        Run <code className="bg-muted px-1.5 py-0.5 rounded">docker compose up -d prometheus grafana</code> to start the observability stack.
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {activeTab === "eval" && (
                        <div className="space-y-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <FlaskConical className="size-4 text-secondary-foreground" />
                                        Eval Suites
                                    </CardTitle>
                                    <CardDescription>Run automated golden test sets against your LLM</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid gap-3 md:grid-cols-3">
                                        {evalSuites.map((suite: any) => (
                                            <Card key={suite.name} className="border-dashed hover:shadow-sm transition-all">
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium capitalize">{suite.name.replace(/_/g, " ")}</CardTitle>
                                                    <CardDescription className="text-xs">{suite.description}</CardDescription>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-xs text-muted-foreground mb-3">{suite.test_count} test cases</div>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        className="w-full"
                                                        onClick={() => runEvalSuite(suite.name)}
                                                        disabled={runningSuite === suite.name}
                                                    >
                                                        {runningSuite === suite.name ? (
                                                            <><Loader2 className="size-3 mr-1.5 animate-spin" /> Running...</>
                                                        ) : (
                                                            "Run Suite"
                                                        )}
                                                    </Button>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>Recent Eval Runs</CardTitle>
                                    <CardDescription>Last {evalRuns.length} evaluation runs</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {evalRuns.length === 0 ? (
                                        <div className="text-center py-8 text-sm text-muted-foreground">
                                            No eval runs yet. Run a suite above.
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            {evalRuns.map((run: any) => (
                                                <div key={run.id} className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
                                                    <div>
                                                        <span className="text-sm font-medium capitalize">{run.suite_name.replace(/_/g, " ")}</span>
                                                        <span className="text-xs text-muted-foreground ml-2">({run.model})</span>
                                                    </div>
                                                    <div className="flex items-center gap-4 text-xs">
                                                        <span className={`font-mono font-semibold ${
                                                            run.score >= 80 ? "text-green-600" : run.score >= 50 ? "text-yellow-600" : "text-red-600"
                                                        }`}>
                                                            {run.score ?? "—"}%
                                                        </span>
                                                        <span className="text-muted-foreground">{run.passed}/{run.total}</span>
                                                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                                                            run.status === "completed" ? "bg-green-500/10 text-green-600" : "bg-yellow-500/10 text-yellow-600"
                                                        }`}>
                                                            {run.status}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
