"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getApiBaseUrl } from "@/lib/api-url";

export type ChatLine = { role: string; content: string };

type JsonMap = Record<string, unknown>;

type LiveKitParticipant = {
  setMicrophoneEnabled?: (enabled: boolean) => Promise<void>;
  sendText?: (text: string, options?: { topic?: string }) => Promise<void>;
  publishData?: (data: Uint8Array, options?: { reliable?: boolean; topic?: string }) => void;
};

type LiveKitRoomHandle = {
  state?: string;
  connect: (url: string, token: string) => Promise<void>;
  disconnect: () => void;
  on: (event: string | symbol, listener: (...args: unknown[]) => void) => LiveKitRoomHandle;
  localParticipant?: LiveKitParticipant;
};

type LiveKitAudioTrack = {
  kind?: string;
  attach: () => HTMLMediaElement;
  detach: () => HTMLMediaElement[];
};

function getWsBaseUrl(): string {
  const base = getApiBaseUrl();
  if (base.startsWith("/")) {
    const backendHost = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001";
    return backendHost.replace(/^http/, "ws");
  }
  return base.replace(/^http/, "ws");
}

function isLiveKitRuntime(): boolean {
  return process.env.NEXT_PUBLIC_VOICE_RUNTIME === "livekit";
}

export function useVoiceSession(agentId: string, language?: string, voice?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const roomRef = useRef<LiveKitRoomHandle | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBufferSourceNode[]>([]);
  const remoteAudioElsRef = useRef<HTMLMediaElement[]>([]);
  const [status, setStatus] = useState<string>("disconnected");
  const [isConnected, setIsConnected] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

  const detachRemoteAudio = () => {
    for (const el of remoteAudioElsRef.current) {
      el.pause();
      el.remove();
    }
    remoteAudioElsRef.current = [];
  };

  const leaveCall = useCallback(async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;

    if (wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({ type: "disconnect" }));
      } catch { /* ignore */ }
      wsRef.current.close();
      wsRef.current = null;
    }

    if (roomRef.current) {
      try {
        await roomRef.current.localParticipant?.setMicrophoneEnabled?.(false);
      } catch { /* ignore */ }
      roomRef.current.disconnect();
      roomRef.current = null;
    }

    detachRemoteAudio();
    audioQueueRef.current = [];
    sessionIdRef.current = null;
    setIsCalling(false);
    setIsConnected(false);
    setAgentSpeaking(false);
    setStatus("disconnected");
  }, []);

  const startLiveKitCall = useCallback(async () => {
    const lk = await import("livekit-client");
    const response = await fetch(`${getApiBaseUrl()}/api/v1/livekit/token/${agentId}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language: language || "en-IN",
        voice,
      }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Could not create LiveKit session.");
    }

    const token = await response.json() as {
      server_url: string;
      participant_token: string;
      room_name: string;
      agent_name: string;
    };
    const room = new lk.Room({
      adaptiveStream: true,
      dynacast: true,
    }) as unknown as LiveKitRoomHandle;

    roomRef.current = room;
    sessionIdRef.current = token.room_name;

    room.on(lk.RoomEvent.Connected, () => {
      setChatHistory([{ role: "system", content: `LiveKit voice session with ${token.agent_name}` }]);
      setIsCalling(true);
      setIsConnected(true);
      setStatus("connected");
    });

    room.on(lk.RoomEvent.Disconnected, () => {
      detachRemoteAudio();
      setIsCalling(false);
      setIsConnected(false);
      setAgentSpeaking(false);
      setStatus("disconnected");
    });

    room.on(lk.RoomEvent.TrackSubscribed, (trackValue: unknown) => {
      const track = trackValue as LiveKitAudioTrack;
      if (track.kind !== "audio") return;
      const el = track.attach();
      el.autoplay = true;
      el.style.display = "none";
      document.body.appendChild(el);
      remoteAudioElsRef.current.push(el);
      setAgentSpeaking(true);
    });

    room.on(lk.RoomEvent.TrackUnsubscribed, (trackValue: unknown) => {
      const track = trackValue as LiveKitAudioTrack;
      if (track.kind !== "audio") return;
      track.detach().forEach((el: HTMLMediaElement) => {
        el.pause();
        el.remove();
      });
      setAgentSpeaking(false);
    });

    const transcriptionEvent = (lk.RoomEvent as Record<string, string>).TranscriptionReceived;
    if (transcriptionEvent) {
      room.on(transcriptionEvent, (segmentsValue: unknown, participantValue: unknown) => {
        const segments = Array.isArray(segmentsValue) ? segmentsValue as JsonMap[] : [];
        const participant = participantValue as { isLocal?: boolean } | undefined;
        for (const segment of segments || []) {
          if (!segment?.final || typeof segment.text !== "string") continue;
          const transcriptText = segment.text;
          setChatHistory((prev) => [
            ...prev,
            {
              role: participant?.isLocal ? "user" : "assistant",
              content: transcriptText,
            },
          ]);
        }
      });
    }

    setStatus("connecting");
    await room.connect(token.server_url, token.participant_token);
    await room.localParticipant?.setMicrophoneEnabled?.(true);
  }, [agentId, language, voice]);

  const startMicCapture = useCallback((ws: WebSocket) => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone not available in this browser");
      return;
    }
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        const recorder = new MediaRecorder(stream, {
          mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
            ? "audio/webm;codecs=opus"
            : "audio/webm",
        });
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0 && ws.readyState === WebSocket.OPEN && !isMuted) {
            e.data.arrayBuffer().then((buffer) => {
              const bytes = new Uint8Array(buffer);
              let binary = "";
              for (let i = 0; i < bytes.length; i++) {
                binary += String.fromCharCode(bytes[i]);
              }
              ws.send(JSON.stringify({
                type: "audio",
                audio: btoa(binary),
                mimetype: recorder.mimeType,
              }));
            });
          }
        };

        recorder.start(100);
      })
      .catch((err: Error) => {
        setError(`Mic access denied: ${err.message}`);
      });
  }, [isMuted]);

  const playAudio = useCallback((base64Audio: string, sampleRate: number) => {
    try {
      const binary = atob(base64Audio);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }

      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext({ sampleRate });
      }

      audioContextRef.current.decodeAudioData(bytes.buffer, (buffer) => {
        const source = audioContextRef.current!.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContextRef.current!.destination);
        source.start();
        audioQueueRef.current.push(source);
        setAgentSpeaking(true);

        source.onended = () => {
          audioQueueRef.current = audioQueueRef.current.filter((s) => s !== source);
          if (audioQueueRef.current.length === 0) setAgentSpeaking(false);
        };
      });
    } catch { /* ignore decode errors */ }
  }, []);

  const startLegacyCall = useCallback(async () => {
    const wsUrl = `${getWsBaseUrl()}/api/v1/orchestrator/ws/${agentId}?language=${language || "en-IN"}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connecting");
    };

    ws.onmessage = async (event) => {
      let msg: JsonMap;
      try {
        msg = JSON.parse(event.data) as JsonMap;
      } catch {
        return;
      }

      switch (msg.type) {
        case "session_start":
          sessionIdRef.current = typeof msg.session_id === "string" ? msg.session_id : null;
          setChatHistory([{ role: "system", content: `Voice test with ${String(msg.agent_name || "agent")}` }]);
          setIsCalling(true);
          setIsConnected(true);
          setStatus("connected");
          startMicCapture(ws);
          break;
        case "transcript":
          setChatHistory((prev) => [
            ...prev,
            { role: msg.role === "USER" ? "user" : "assistant", content: String(msg.content || "") },
          ]);
          break;
        case "audio": {
          const audioData = typeof msg.data === "string" ? msg.data : msg.audio;
          const sampleRate = typeof msg.sample_rate === "number" ? msg.sample_rate : 24000;
          if (typeof audioData === "string") playAudio(audioData, sampleRate);
          break;
        }
        case "text_chunk":
          if (typeof msg.text === "string") {
            setChatHistory((prev) => [...prev, { role: "assistant", content: msg.text as string }]);
          }
          break;
        case "event":
          if (msg.event === "ServerInteractionEndEvent") setAgentSpeaking(false);
          break;
        case "error":
          setError(typeof msg.message === "string" ? msg.message : "Voice error");
          setChatHistory((prev) => [...prev, { role: "system", content: `Error: ${String(msg.message || "Voice error")}` }]);
          break;
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection error");
    };

    ws.onclose = () => {
      if (wsRef.current === ws) {
        setIsCalling(false);
        setIsConnected(false);
        setAgentSpeaking(false);
        setStatus("disconnected");
      }
    };
  }, [agentId, language, playAudio, startMicCapture]);

  const startCall = useCallback(async () => {
    setError(null);
    try {
      await leaveCall();
      if (isLiveKitRuntime()) {
        await startLiveKitCall();
      } else {
        await startLegacyCall();
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not start the voice call.";
      setError(msg);
      setChatHistory((prev) => [...prev, { role: "system", content: `Error: ${msg}` }]);
    }
  }, [leaveCall, startLegacyCall, startLiveKitCall]);

  const sendText = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const room = roomRef.current;
    if (room?.state === "connected") {
      const participant = room.localParticipant;
      if (typeof participant?.sendText === "function") {
        participant.sendText(trimmed, { topic: "lk.chat" }).catch(() => undefined);
      } else if (typeof participant?.publishData === "function") {
        participant.publishData(new TextEncoder().encode(trimmed), { reliable: true, topic: "lk.chat" });
      }
      setChatHistory((prev) => [...prev, { role: "user", content: trimmed }]);
      return;
    }

    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "text", text: trimmed }));
    setChatHistory((prev) => [...prev, { role: "user", content: trimmed }]);
  }, []);

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev;
      const room = roomRef.current;
      if (room?.localParticipant?.setMicrophoneEnabled) {
        room.localParticipant.setMicrophoneEnabled(!next).catch(() => undefined);
      }
      return next;
    });
  }, []);

  useEffect(() => {
    return () => {
      void leaveCall();
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
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
