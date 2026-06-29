"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  MessageSquare,
  Phone,
  Plus,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  Inbox,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ChannelStat {
  sent24h: number;
  received24h: number;
  quotaUsed: number;
  connected: boolean;
  number: string;
}

interface ConversationRow {
  id: string;
  contact: string;
  channel: "whatsapp" | "sms";
  preview: string;
  time: string;
  status: "open" | "resolved" | "pending";
}

const DEMO_WHATSAPP: ChannelStat = { sent24h: 0, received24h: 0, quotaUsed: 0, connected: false, number: "Not configured" };
const DEMO_SMS: ChannelStat = { sent24h: 0, received24h: 0, quotaUsed: 0, connected: false, number: "Not configured" };

const statusStyles: Record<string, string> = {
  open: "bg-green-500/10 text-green-600",
  pending: "bg-yellow-500/10 text-yellow-600",
  resolved: "bg-muted text-muted-foreground",
};

export default function ChannelsPage() {
  const [whatsapp, setWhatsapp] = useState<ChannelStat>(DEMO_WHATSAPP);
  const [sms, setSms] = useState<ChannelStat>(DEMO_SMS);
  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Stats and conversations would be fetched from /api/v1/whatsapp and /api/v1/sms once backend is wired
    setIsLoading(false);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <div className="flex items-center justify-center size-9 rounded-lg bg-primary/10">
              <MessageSquare className="size-5 text-primary" />
            </div>
            Messaging{" "}
            <span className="text-primary">Channels</span>
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage WhatsApp and SMS channels for automated messaging alongside voice.
          </p>
        </div>
        <Link href="/dashboard/settings?tab=whatsapp">
          <Button className="gap-2">
            <Plus className="size-4" />
            Connect Channel
          </Button>
        </Link>
      </div>

      {/* Channel status cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <ChannelCard
          icon={<MessageSquare className="size-5 text-green-600" />}
          name="WhatsApp Business"
          stat={whatsapp}
          configHref="/dashboard/settings?tab=whatsapp"
        />
        <ChannelCard
          icon={<Phone className="size-5 text-primary" />}
          name="SMS"
          stat={sms}
          configHref="/dashboard/settings?tab=telephony"
        />
      </div>

      {/* Conversations table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Conversations</CardTitle>
          <CardDescription>
            Inbound and outbound messages across all channels.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 rounded-lg bg-muted animate-pulse" />
              ))}
            </div>
          ) : conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center px-4">
              <div className="flex items-center justify-center size-14 rounded-full bg-primary/10 mb-4">
                <Inbox className="size-7 text-primary" />
              </div>
              <h3 className="text-base font-semibold text-foreground">No conversations yet</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs leading-relaxed">
                Connect a WhatsApp or SMS channel and send your first message to see conversations here.
              </p>
              <Link href="/dashboard/settings?tab=whatsapp" className="mt-4">
                <Button variant="outline" className="gap-2">
                  Set up WhatsApp
                  <ArrowRight className="size-4" />
                </Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/50 border-b border-border">
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Contact</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Channel</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Last Message</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Time</th>
                    <th className="text-left px-4 py-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {conversations.map((conv) => (
                    <tr key={conv.id} className="hover:bg-muted/30 cursor-pointer transition-colors">
                      <td className="px-4 py-3 font-medium text-foreground">{conv.contact}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${conv.channel === "whatsapp" ? "bg-green-500/10 text-green-600" : "bg-primary/10 text-primary"}`}>
                          {conv.channel === "whatsapp" ? <MessageSquare className="size-3" /> : <Phone className="size-3" />}
                          {conv.channel === "whatsapp" ? "WhatsApp" : "SMS"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground max-w-xs truncate">{conv.preview}</td>
                      <td className="px-4 py-3 text-muted-foreground text-xs font-mono">{conv.time}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${statusStyles[conv.status]}`}>
                          {conv.status}
                        </span>
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

function ChannelCard({ icon, name, stat, configHref }: { icon: React.ReactNode; name: string; stat: ChannelStat; configHref: string }) {
  return (
    <Card className="hover:shadow-md transition-all duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="size-8 rounded-lg bg-muted flex items-center justify-center">
              {icon}
            </div>
            <CardTitle className="text-sm font-semibold">{name}</CardTitle>
          </div>
          <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${stat.connected ? "bg-green-500/10 text-green-600" : "bg-muted text-muted-foreground"}`}>
            {stat.connected ? <CheckCircle className="size-3" /> : <AlertCircle className="size-3" />}
            {stat.connected ? "Connected" : "Not connected"}
          </span>
        </div>
        <CardDescription className="text-xs mt-1 font-mono">{stat.number}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center">
            <p className="text-lg font-black text-foreground">{stat.sent24h}</p>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Sent 24h</p>
          </div>
          <div className="text-center border-x border-border">
            <p className="text-lg font-black text-foreground">{stat.received24h}</p>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Received 24h</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-black text-foreground">{stat.quotaUsed}%</p>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Quota used</p>
          </div>
        </div>
        <Link href={configHref}>
          <Button variant="outline" className="w-full gap-2 text-xs h-8">
            <Clock className="size-3.5" />
            {stat.connected ? "Manage" : "Set up"}
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
