"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Room, RoomEvent, Track, LocalTrackPublication, LocalAudioTrack, DataPacket_Kind } from "livekit-client";
import api from "@/lib/api";

export type ChatLine = { role: string; content: string };

type JoinResponse = {
  room_name: string;
  participant_token: string;
  call_id: string;
  session_id: string;
  agent_id: string;
  agent_name: string;
  voice: string;
  language: string;
  tool_names: string[];
};

export function useLiveKitSession(agentId: string, language?: string, voice?: string) {
  const roomRef = useRef<Room | null>(null);
  const [status, setStatus] = useState<string>("disconnected");
  const [isConnected, setIsConnected] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);

  const leaveCall = useCallback(async () => {
    const room = roomRef.current;
    if (room) {
      try {
        await room.disconnect();
      } catch {
        /* ignore */
      }
      roomRef.current = null;
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

      const join: JoinResponse = await api.post(`/orchestrator/livekit/join/${agentId}`, {
        language: language || undefined,
        voice: voice && voice !== "auto" ? voice : undefined,
      });

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });
      roomRef.current = room;

      room.on(RoomEvent.Connected, () => {
        setStatus("connected");
        setIsConnected(true);
        setIsCalling(true);
        
        // Enable local microphone
        room.localParticipant.enableCameraAndMicrophone().catch(e => {
            console.error("Could not enable microphone", e);
        });
      });

      room.on(RoomEvent.Disconnected, () => {
        setStatus("disconnected");
        setIsConnected(false);
        setIsCalling(false);
        setAgentSpeaking(false);
      });

      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        // If there's an active speaker that isn't the local user, we assume the agent is speaking
        const agentIsSpeaking = speakers.some(p => p.identity !== room.localParticipant.identity);
        setAgentSpeaking(agentIsSpeaking);
      });

      room.on(RoomEvent.DataReceived, (payload, participant, kind) => {
        // Basic implementation for receiving text messages or transcripts from Pipecat via DataChannels
        try {
            const strData = new TextDecoder().decode(payload);
            const data = JSON.parse(strData);
            if (data.type === "text" || data.type === "transcript") {
                setChatHistory(prev => [...prev, { role: data.role || "assistant", content: data.text }]);
            }
        } catch (e) {
            // Ignore non-json data
        }
      });

      // We assume LiveKit server is at the same origin or configured via env variable in real deployments
      // For local development, we point to localhost:7880
      const LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880";
      
      await room.connect(LIVEKIT_URL, join.participant_token);
      
      setChatHistory([{ role: "system", content: `Voice test with ${join.agent_name}` }]);
      
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not start the voice call. Please try again.";
      setError(msg);
      setChatHistory((prev) => [...prev, { role: "system", content: `Error: ${msg}` }]);
    }
  }, [agentId, language, voice, leaveCall]);

  const sendText = useCallback((text: string) => {
    const room = roomRef.current;
    if (!room || !text.trim() || !room.localParticipant) return;
    
    // Send text to agent via LiveKit Data Channel
    const payload = JSON.stringify({ type: "text", text: text.trim(), role: "user" });
    const encoder = new TextEncoder();
    room.localParticipant.publishData(encoder.encode(payload), { reliable: true });
    
    setChatHistory((prev) => [...prev, { role: "user", content: text.trim() }]);
  }, []);

  const toggleMute = useCallback(() => {
    const room = roomRef.current;
    if (!room || !room.localParticipant) return;
    
    room.localParticipant.audioTrackPublications.forEach((pub) => {
      if (pub.track) {
        if (isMuted) {
          pub.track.unmute();
        } else {
          pub.track.mute();
        }
      }
    });
    
    setIsMuted(!isMuted);
  }, [isMuted]);

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
