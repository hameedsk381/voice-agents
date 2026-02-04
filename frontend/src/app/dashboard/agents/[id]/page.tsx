"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mic, Send, Bot, User } from "lucide-react";

export default function AgentPlayground() {
    const params = useParams();
    const agentId = params.id as string;
    const [messages, setMessages] = useState<{ role: string, content: string }[]>([]);
    const [input, setInput] = useState("");
    const [isRecording, setIsRecording] = useState(false);
    const userHasScrolled = useRef(false);

    // Use a ref for the WebSocket to persist it across renders
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        // Connect to WebSocket
        ws.current = new WebSocket(`ws://localhost:8001/api/v1/orchestrator/ws/${agentId}`);

        ws.current.onopen = () => {
            console.log("Connected to agent orchestrator");
        };

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'session_start') {
                console.log("Session started:", data.session_id);
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: `🚀 Session started with ${data.agent_name}`
                }]);
            } else if (data.type === 'text_chunk') {
                setMessages(prev => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg && lastMsg.role === 'assistant') {
                        return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + data.text }];
                    } else {
                        return [...prev, { role: 'assistant', content: data.text }];
                    }
                });
            } else if (data.type === 'audio') {
                console.log("Received Audio Chunk");
                const audio = new Audio("data:audio/mp3;base64," + data.data);
                audio.play().catch(e => console.error("Audio playback failed", e));
            } else if (data.type === 'tool_call') {
                setMessages(prev => [...prev, {
                    role: 'tool',
                    content: `🔧 Calling tool: ${data.name}\nArgs: ${JSON.stringify(data.arguments)}`
                }]);
            } else if (data.type === 'intent_detected') {
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: `🎯 Intent detected: ${data.intent}`
                }]);
            } else if (data.type === 'agent_switch') {
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: `🔄 Routing from ${data.from} → ${data.to}\nReason: ${data.reason}`
                }]);
            } else if (data.type === 'escalation') {
                setMessages(prev => [...prev, {
                    role: 'escalation',
                    content: `⚠️ Escalating to human agent\nReason: ${data.reason}`
                }]);
            }
        };

        return () => {
            ws.current?.close();
        };
    }, [agentId]);

    const sendMessage = () => {
        if (!input.trim() || !ws.current) return;

        // Optimistic update
        setMessages(prev => [...prev, { role: 'user', content: input }]);

        // Send to backend (Simulating "Text" input as STT result for now)
        ws.current.send(JSON.stringify({ text: input }));
        setInput("");
    };

    const toggleRecording = () => {
        // TODO: Implement actual microphone streaming
        setIsRecording(!isRecording);
        if (!isRecording) {
            // Simulate voice input for now
            setTimeout(() => {
                ws.current?.send(JSON.stringify({ audio: "dummy_audio_bytes" }));
                setIsRecording(false);
            }, 2000);
        }
    };

    return (
        <div className="h-[calc(100vh-100px)] grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chat Interface */}
            <Card className="lg:col-span-2 flex flex-col h-full bg-[#0f0f10] border-white/10">
                <CardHeader className="border-b border-white/10 py-4">
                    <CardTitle className="text-white flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        Live Session
                    </CardTitle>
                </CardHeader>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-none'
                                    : msg.role === 'tool'
                                        ? 'bg-amber-500/20 text-amber-200 border border-amber-500/30 rounded-lg'
                                        : msg.role === 'system'
                                            ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 rounded-lg text-xs'
                                            : msg.role === 'escalation'
                                                ? 'bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg'
                                                : 'bg-white/10 text-gray-200 rounded-bl-none'
                                }`}>
                                <div className="flex items-center gap-2 mb-1 opacity-50 text-xs">
                                    {msg.role === 'user' ? <User className="w-3 h-3" />
                                        : msg.role === 'tool' ? '⚙️'
                                            : msg.role === 'system' ? '📡'
                                                : msg.role === 'escalation' ? '🚨'
                                                    : <Bot className="w-3 h-3" />}
                                    {msg.role === 'user' ? 'You'
                                        : msg.role === 'tool' ? 'Tool Execution'
                                            : msg.role === 'system' ? 'System'
                                                : msg.role === 'escalation' ? 'Escalation'
                                                    : 'Agent'}
                                </div>
                                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="p-4 border-t border-white/10 bg-[#0f0f10]">
                    <div className="relative flex items-center gap-2">
                        <button
                            onClick={toggleRecording}
                            className={`p-3 rounded-full transition-all ${isRecording
                                ? 'bg-red-500/20 text-red-500 animate-pulse border border-red-500/50'
                                : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                                }`}
                        >
                            <Mic className="w-5 h-5" />
                        </button>
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                            className="flex-1 bg-black/50 border border-white/10 rounded-full px-4 py-3 text-white focus:outline-none focus:border-blue-500 placeholder:text-gray-600"
                            placeholder="Type a message or press mic to speak..."
                        />
                        <button
                            onClick={sendMessage}
                            className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-500 transition-colors"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </Card>

            {/* Agent details / Live Debug */}
            <div className="space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-white">Live Metrics</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-400">Status</span>
                                <span className="text-green-400 font-medium">Listening</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-400">Latency</span>
                                <span className="text-white">320ms</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-400">Session ID</span>
                                <span className="text-gray-500 font-mono text-xs">sess_89234...23</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
