from app.orchestration.audio_handler import pcm16le_to_wav_bytes

def test_pcm16le_to_wav_bytes():
    # Construct a simple mock raw PCM stream (100 bytes of zeros)
    raw_pcm = b"\x00" * 100
    sample_rate = 16000
    
    # Execute conversion
    wav_data = pcm16le_to_wav_bytes(raw_pcm, sample_rate, channels=1, sample_width=2)
    
    # Assertions
    assert isinstance(wav_data, bytes)
    assert len(wav_data) > 100
    
    # Verify WAV file signature ("RIFF" .... "WAVEfmt ")
    assert wav_data.startswith(b"RIFF")
    assert b"WAVE" in wav_data
    assert b"fmt " in wav_data
    
    # Verify we can read it back using Python's standard wave library
    import io
    import wave
    with wave.open(io.BytesIO(wav_data), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.readframes(100) == raw_pcm
