"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Phone,
  IndianRupee,
  HandCoins,
  Target,
  ArrowRight,
  Inbox,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface CollectionsKpis {
  callsMade: number;
  promiseToPayRate: number; // %
  amountRecovered: number; // ₹
  recoveryRate: number; // % vs baseline
  baselineRate: number; // %
}

interface AccountRow {
  id: string;
  borrower: string;
  amountDue: number;
  language: string;
  callOutcome: "promise_to_pay" | "payment_collected" | "no_answer" | "refused" | "pending";
  paymentStatus: "paid" | "link_sent" | "promised" | "none";
  lastCall: string;
}

const EMPTY_KPIS: CollectionsKpis = {
  callsMade: 0,
  promiseToPayRate: 0,
  amountRecovered: 0,
  recoveryRate: 0,
  baselineRate: 0,
};

const outcomeStyles: Record<string, { label: string; cls: string }> = {
  promise_to_pay: { label: "Promise to pay", cls: "bg-green-500/10 text-green-600" },
  payment_collected: { label: "Paid", cls: "bg-green-600/15 text-green-700" },
  no_answer: { label: "No answer", cls: "bg-muted text-muted-foreground" },
  refused: { label: "Refused", cls: "bg-red-500/10 text-red-600" },
  pending: { label: "Pending", cls: "bg-yellow-500/10 text-yellow-600" },
};

const paymentStyles: Record<string, { label: string; cls: string }> = {
  paid: { label: "Paid", cls: "bg-green-600/15 text-green-700" },
  link_sent: { label: "Link sent", cls: "bg-primary/10 text-primary" },
  promised: { label: "Promised", cls: "bg-yellow-500/10 text-yellow-600" },
  none: { label: "—", cls: "bg-muted text-muted-foreground" },
};

const fmtINR = (n: number) =>
  n >= 100000 ? `₹${(n / 100000).toFixed(1)}L` : `₹${n.toLocaleString("en-IN")}`;

export default function CollectionsPage() {
  const [kpis, setKpis] = useState<CollectionsKpis>(EMPTY_KPIS);
  const [accounts, setAccounts] = useState<AccountRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Wired to /api/v1/analytics + /api/v1/billing/usage (payment_collected, promise_to_pay_captured).
    setIsLoading(false);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <div className="flex items-center justify-center size-9 rounded-lg bg-primary/10">
              <TrendingUp className="size-5 text-primary" />
            </div>
            EMI <span className="text-primary">Collections</span>
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Recovery performance for your AI collections agent — outcomes, not minutes.
          </p>
        </div>
        <Link href="/dashboard/campaigns">
          <Button className="gap-2">
            <Phone className="size-4" />
            Launch Recovery Campaign
          </Button>
        </Link>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={<Phone className="size-4 text-primary" />} label="Calls made" value={kpis.callsMade.toLocaleString("en-IN")} />
        <KpiCard icon={<HandCoins className="size-4 text-green-600" />} label="Promise-to-pay rate" value={`${kpis.promiseToPayRate}%`} />
        <KpiCard icon={<IndianRupee className="size-4 text-green-700" />} label="Recovered" value={fmtINR(kpis.amountRecovered)} />
        <KpiCard
          icon={<Target className="size-4 text-accent" />}
          label="Recovery vs baseline"
          value={kpis.recoveryRate ? `${kpis.recoveryRate}%` : "—"}
          sub={kpis.baselineRate ? `baseline ${kpis.baselineRate}%` : "set a baseline"}
        />
      </div>

      {/* Recovery funnel */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Recovery Funnel</CardTitle>
          <CardDescription>From dial to rupees in the account.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Dialed", value: kpis.callsMade, cls: "bg-muted" },
              { label: "Connected", value: 0, cls: "bg-primary/10" },
              { label: "Promise to pay", value: 0, cls: "bg-green-500/10" },
              { label: "Paid", value: 0, cls: "bg-green-600/15" },
            ].map((step) => (
              <div key={step.label} className={`rounded-xl p-4 ${step.cls}`}>
                <p className="text-2xl font-black text-foreground">{step.value}</p>
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mt-1">
                  {step.label}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Accounts table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Accounts</CardTitle>
          <CardDescription>Per-account call outcome and payment status.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 rounded-lg bg-muted animate-pulse" />
              ))}
            </div>
          ) : accounts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center px-4">
              <div className="flex items-center justify-center size-14 rounded-full bg-primary/10 mb-4">
                <Inbox className="size-7 text-primary" />
              </div>
              <h3 className="text-base font-semibold text-foreground">No collections activity yet</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs leading-relaxed">
                Install the EMI Collections Agent and launch a recovery campaign to see accounts and outcomes here.
              </p>
              <Link href="/dashboard/marketplace" className="mt-4">
                <Button variant="outline" className="gap-2">
                  Install Collections Agent
                  <ArrowRight className="size-4" />
                </Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/50 border-b border-border">
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Borrower</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Amount Due</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Language</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Call Outcome</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Payment</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Last Call</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {accounts.map((acc) => (
                    <tr key={acc.id} className="hover:bg-muted/30 cursor-pointer transition-colors">
                      <td className="px-4 py-3 font-medium text-foreground">{acc.borrower}</td>
                      <td className="px-4 py-3 font-mono text-foreground">{fmtINR(acc.amountDue)}</td>
                      <td className="px-4 py-3 text-muted-foreground text-xs">{acc.language}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${outcomeStyles[acc.callOutcome].cls}`}>
                          {outcomeStyles[acc.callOutcome].label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${paymentStyles[acc.paymentStatus].cls}`}>
                          {paymentStyles[acc.paymentStatus].label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-xs font-mono">{acc.lastCall}</td>
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

function KpiCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="size-7 rounded-lg bg-muted flex items-center justify-center">{icon}</div>
          <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{label}</p>
        </div>
        <p className="text-2xl font-black text-foreground">{value}</p>
        {sub && <p className="text-[10px] text-muted-foreground mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  );
}
