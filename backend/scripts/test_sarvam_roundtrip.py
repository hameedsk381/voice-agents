"""Test Sarvam STT + TTS round-trip."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.tts.sarvam_provider import SarvamTTS
from app.services.stt.sarvam_provider import SarvamSTT


async def main():
    print("=== Sarvam Voice Pipeline Round-Trip Test ===\n")

    # 1. TTS
    print("1. TTS: synthesizing speech...")
    tts = SarvamTTS()
    audio = await tts.synthesize("Namaste, main aapki kaise madad kar sakta hoon?", voice="shubh")
    if not audio:
        print("   TTS FAILED: empty response")
        return 1
    print(f"   OK — {len(audio)} bytes of WAV audio\n")

    # 2. STT on the generated audio
    print("2. STT: transcribing the audio back...")
    stt = SarvamSTT()
    result = await stt.transcribe(audio, language="hi-IN", mimetype="audio/wav")
    if not result.text:
        print("   STT FAILED: empty transcript")
        return 1
    transcript = result.text.encode("utf-8", errors="replace").decode("utf-8")
    print(f'   Transcript: "{transcript}"')
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Provider:   {result.provider}\n")

    print("=== ROUND TRIP SUCCESS ===")
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
