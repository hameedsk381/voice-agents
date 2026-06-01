import json
from typing import Any

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession
from livekit.plugins import google, silero

from app.core.config import settings

load_dotenv()


def _metadata(ctx: Any) -> dict[str, Any]:
    raw = getattr(getattr(ctx, "job", None), "metadata", "") or "{}"
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _instructions(metadata: dict[str, Any]) -> str:
    stt_lang = metadata.get("language") or settings.LIVEKIT_STT_LANGUAGE
    persona = metadata.get("persona") or "You are a concise, professional voice AI assistant."
    policy = metadata.get("policy")
    tools = metadata.get("tools") or []
    policy_hint = f"\n\nConversation policy:\n{json.dumps(policy, ensure_ascii=True)}" if policy else ""
    tools_hint = f"\n\nAvailable tool names: {', '.join(map(str, tools))}" if tools else ""
    lang_hint = "\nRespond in Hindi (hi-IN). All answers must be in Hindi." if stt_lang and stt_lang.startswith("hi") else ""
    return (
        f"{persona}\n\n"
        "You are operating in a real-time voice call. Keep responses short, natural, and easy to interrupt. "
        "Track the user's goal, avoid repeating questions, ask for clarification when confidence is low, "
        "and escalate verbally if the conversation is failing or the request is outside policy."
        f"{lang_hint}{policy_hint}{tools_hint}"
    )


class VoiseAgent(Agent):
    def __init__(self, metadata: dict[str, Any]) -> None:
        stt_lang = metadata.get("language") or settings.LIVEKIT_STT_LANGUAGE
        voice = metadata.get("voice") or settings.LIVEKIT_TTS_VOICE
        super().__init__(
            instructions=_instructions(metadata),
            stt=google.STT(
                languages=stt_lang,
                model=settings.LIVEKIT_STT_MODEL,
            ),
            llm=google.LLM(model=settings.LIVEKIT_LLM_MODEL),
            tts=google.TTS(
                language=stt_lang,
                voice_name=voice,
            ),
            vad=silero.VAD.load(),
        )

    async def on_enter(self) -> None:
        greeting = "नमस्ते! मैं आपकी आवाज़ सहायक हूँ। आपकी क्या मदद कर सकता हूँ?"
        await self.session.say(greeting)


server = AgentServer()


@server.rtc_session(agent_name=settings.LIVEKIT_AGENT_NAME)
async def voise_agent_entry(ctx: agents.JobContext):
    metadata = _metadata(ctx)

    ctx.log_context_fields = {
        "agent_id": metadata.get("agent_id", ""),
        "organization_id": metadata.get("organization_id", ""),
        "room_name": getattr(ctx.room, "name", ""),
    }

    session = AgentSession()
    await session.start(
        room=ctx.room,
        agent=VoiseAgent(metadata),
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
