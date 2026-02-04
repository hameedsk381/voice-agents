"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Phone, Clock, Users } from "lucide-react";

const stats = [
    {
        title: "Total Calls",
        value: "1,248",
        change: "+12% from last month",
        icon: Phone,
        color: "text-blue-500",
    },
    {
        title: "Active Agents",
        value: "8",
        change: "+2 new this week",
        icon: Users,
        color: "text-purple-500",
    },
    {
        title: "Avg. Duration",
        value: "2m 14s",
        change: "-5% from last month",
        icon: Clock,
        color: "text-green-500",
    },
    {
        title: "Success Rate",
        value: "94.2%",
        change: "+1.2% from last month",
        icon: Activity,
        color: "text-orange-500",
    },
];

export default function DashboardPage() {
    return (
        <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {stats.map((stat) => (
                    <Card key={stat.title}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-gray-400">
                                {stat.title}
                            </CardTitle>
                            <stat.icon className={`h-4 w-4 ${stat.color}`} />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">{stat.value}</div>
                            <p className="text-xs text-gray-500 mt-1">{stat.change}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4">
                    <CardHeader>
                        <CardTitle className="text-white">Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-sm text-gray-400">
                            placeholder for graph
                        </div>
                    </CardContent>
                </Card>
                <Card className="col-span-3">
                    <CardHeader>
                        <CardTitle className="text-white">System Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">API Latency</span>
                                <span className="text-sm text-green-400">45ms</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Database</span>
                                <span className="text-sm text-green-400">Healthy</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Redis Cache</span>
                                <span className="text-sm text-green-400">Healthy</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">Temporal Workers</span>
                                <span className="text-sm text-blue-400">Idle</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
