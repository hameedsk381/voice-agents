"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { UltravoxSession } from "ultravox-client";
import api from "@/lib/api";

export type ChatLine = { role: string; content: string };

type JoinResponse = {
  join_url: string;
  call_id: string;
  session_id: string;
  agent_id: string;
  agent_name: string;
  voice: string;
  language: string;
  tool_names: string[];
};

export function useUltravoxSession(agentId: string, language?: string, voice?: string) {
  const sessionRef = useRef<UltravoxSession | null>(null);
  const [status, setStatus] = useState<string>("disconnected");
  const [isConnected, setIsConnected] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatLine[]>([]);
  const [error, setError] = useState<string | null>(null);

  const syncTranscripts = useCallback((session: UltravoxSession) => {
    const lines: ChatLine[] = (session.transcripts || [])
      .filter((t) => t.isFinal && t.text?.trim())
      .map((t) => ({
        role: t.speaker === "agent" ? "assistant" : "user",
        content: t.text,
      }));
    setChatHistory(lines);
  }, []);

  const leaveCall = useCallback(async () => {
    const session = sessionRef.current;
    if (session) {
      try {
        await session.leaveCall();
      } catch {
        /* ignore */
      }
      sessionRef.current = null;
    }
    setIsCalling(false);
    setIsConnected(false);
    setAgentSpeaking(false);
    setStatus("disconnected");
  }, []);

  const startCall = useCallback(async () => {
    setError(null);
    try {
    await leaveCall();

    const join: JoinResponse = await api.post(`/orchestrator/ultravox/join/${agentId}`, {
      language: language || undefined,
      voice: voice && voice !== "auto" ? voice : undefined,
    });

    const session = new UltravoxSession();
    sessionRef.current = session;

    session.addEventListener("status", () => {
      setStatus(session.status);
      setIsConnected(session.status !== "disconnected" && session.status !== "disconnecting");
      setAgentSpeaking(session.status === "speaking");
      setIsCalling(
        session.status !== "disconnected" &&
          session.status !== "disconnecting" &&
          session.status !== "connecting"
      );
    });

    session.addEventListener("transcripts", () => syncTranscripts(session));

    for (const toolName of join.tool_names || []) {
      session.registerToolImplementation(toolName, async (parameters: Record<string, unknown>) => {
        const qs = new URLSearchParams({
          agent_id: agentId,
          session_id: join.session_id,
        });
        const res = await api.post(
          `/orchestrator/ultravox/tools/${toolName}?${qs.toString()}`,
          { parameters }
        );
        return typeof res.result === "string" ? res.result : JSON.stringify(res.result);
      });
    }

    session.joinCall(join.join_url);
    setChatHistory([{ role: "system", content: `Voice test with ${join.agent_name}` }]);
    setIsCalling(true);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not start the voice call. Please try again.";
      setError(msg);
      setChatHistory((prev) => [...prev, { role: "system", content: `Error: ${msg}` }]);
    }
  }, [agentId, language, voice, leaveCall, syncTranscripts]);

  const [isMuted, setIsMuted] = useState(false);

  const sendText = useCallback((text: string) => {
    const session = sessionRef.current;
    if (!session || !text.trim()) return;
    session.sendText(text.trim());
    setChatHistory((prev) => [...prev, { role: "user", content: text.trim() }]);
  }, []);

  const toggleMute = useCallback(() => {
    const session = sessionRef.current;
    if (!session) return;
    if (session.isMicMuted) {
      session.unmuteMic();
      setIsMuted(false);
    } else {
      session.muteMic();
      setIsMuted(true);
    }
  }, []);

  useEffect(() => {
    return () => {
      void leaveCall();
    };
  }, [leaveCall]);

  return {
    status,
    isConnected,
    isCalling,
    agentSpeaking,
    chatHistory,
    error,
    startCall,
    leaveCall,
    sendText,
    toggleMute,
    isMuted,
    setError,
  };
}
