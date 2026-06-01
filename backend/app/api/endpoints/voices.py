from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List, Dict, Any
from app.services.tts.factory import get_tts_provider
import shutil
import os
import uuid
import base64
from loguru import logger

router = APIRouter()
tts_service = get_tts_provider()


def _check_method(method: str) -> bool:
    return hasattr(tts_service, method) and callable(getattr(tts_service, method))


@router.get("/", response_model=List[Dict[str, Any]])
async def list_voices(primaryLanguage: Optional[str] = None):
    """List all available voices from the TTS provider."""
    voices = await tts_service.get_voices()
    return voices


@router.post("/design", response_model=Dict[str, str])
async def design_voice(
    text: str = Form(..., description="Sample text for the voice to speak"),
    instruct: str = Form(..., description="Description of the voice"),
):
    """Generate a sample audio for a designed voice. Returns Base64 audio."""
    if not _check_method("design_voice"):
        raise HTTPException(status_code=501, detail="Voice design not supported by current TTS provider")
    logger.info(f"Designing voice: {instruct}")
    audio_content = await tts_service.design_voice(text, instruct)
    if not audio_content:
        raise HTTPException(status_code=500, detail="Failed to design voice")
    return {
        "audio_base64": base64.b64encode(audio_content).decode("utf-8"),
        "instruct": instruct,
    }


@router.post("/register", response_model=Dict[str, str])
async def register_voice(
    name: str = Form(..., description="Name for the new voice"),
    ref_text: str = Form(..., description="Transcript of the reference audio"),
    file: UploadFile = File(..., description="Reference audio file"),
):
    """Clone a voice from an uploaded audio sample."""
    if not _check_method("register_voice"):
        raise HTTPException(status_code=501, detail="Voice cloning not supported by current TTS provider")
    logger.info(f"Registering new voice: {name}")
    temp_filename = f"temp_clone_{uuid.uuid4()}.wav"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        voice_id = await tts_service.register_voice(name, ref_text, temp_filename)
        if not voice_id:
            raise HTTPException(status_code=500, detail="Failed to register voice. Ensure TTS server is running.")
        return {
            "voice_id": voice_id,
            "name": name,
            "status": "created",
            "message": "Voice cloned successfully.",
        }
    except Exception as e:
        logger.error(f"Voice upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a registered voice."""
    if not _check_method("delete_voice"):
        raise HTTPException(status_code=501, detail="Voice deletion not supported by current TTS provider")
    logger.info(f"Deleting voice: {voice_id}")
    success = await tts_service.delete_voice(voice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Voice not found or could not be deleted")
    return {"status": "deleted", "voice_id": voice_id}
