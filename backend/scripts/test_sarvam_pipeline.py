"""Test Sarvam voice pipeline (TTS + STT)."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.tts.sarvam_provider import SarvamTTS
from app.services.stt.sarvam_provider import SarvamSTT


async def main():
    print("=== Sarvam Voice Pipeline Test ===\n")

    tts = SarvamTTS()
    stt = SarvamSTT()

    # --- TTS: English ---
    print("1. TTS: English")
    audio_en = await tts.synthesize(
        "Hello, welcome to Voise AI. How can I help you today?", voice="shubh"
    )
    print(f"   OK: {len(audio_en)} bytes WAV\n")

    # --- TTS: Hindi ---
    print("2. TTS: Hindi")
    audio_hi = await tts.synthesize(
        "Namaste, main aapki kaise madad kar sakta hoon?", voice="shubh"
    )
    print(f"   OK: {len(audio_hi)} bytes WAV\n")

    # --- TTS: voices ---
    print("3. TTS: voices listing")
    voices = await tts.get_voices()
    print(f"   {len(voices)} available voices")
    sample = [v["id"] for v in voices[:5]]
    print(f"   Sample: {sample}\n")

    # --- STT: English ---
    print("4. STT: transcribing English audio")
    result_en = await stt.transcribe(audio_en, language="en-IN", mimetype="audio/wav")
    print(f'   Transcript: "{result_en.text}"')
    print(f"   Confidence: {result_en.confidence:.2f}")
    print(f"   Provider:   {result_en.provider}\n")

    # --- STT: Hindi ---
    print("5. STT: transcribing Hindi audio")
    result_hi = await stt.transcribe(audio_hi, language="hi-IN", mimetype="audio/wav")
    # Write Hindi transcript to file
    out_path = os.path.join(
        os.environ.get("TEMP", r"C:\Users\hamee\AppData\Local\Temp\opencode"),
        "hi_transcript.txt",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result_hi.text)
    print(f"   Has transcript: {bool(result_hi.text)} ({len(result_hi.text)} chars)")
    print(f"   Confidence: {result_hi.confidence:.2f}")
    print(f"   Saved to: {out_path}\n")

    print("=== ALL TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
