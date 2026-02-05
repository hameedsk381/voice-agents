from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional, List, Dict, Any
from app.services.tts.qwen_provider import QwenTTS
import shutil
import os
import uuid
import base64
from loguru import logger

router = APIRouter()
tts_service = QwenTTS() # Default: http://127.0.0.1:8008

@router.get("/", response_model=List[Dict[str, Any]])
async def list_voices():
    """List all available voices (Standard + Cloned)."""
    voices = await tts_service.get_voices()
    return voices

@router.post("/design", response_model=Dict[str, str])
async def design_voice(
    text: str = Form(..., description="Sample text for the voice to speak"),
    instruct: str = Form(..., description="Description of the voice (e.g. 'Deep male voice, calm')")
):
    """
    Generate a sample audio for a designed voice. 
    Returns Base64 audio.
    """
    logger.info(f"Designing voice: {instruct}")
    audio_content = await tts_service.design_voice(text, instruct)
    
    if not audio_content:
        raise HTTPException(status_code=500, detail="Failed to design voice (TTS Service Error)")
    
    return {
        "audio_base64": base64.b64encode(audio_content).decode('utf-8'),
        "instruct": instruct
    }

@router.post("/register", response_model=Dict[str, str])
async def register_voice(
    name: str = Form(..., description="Name for the new voice"),
    ref_text: str = Form(..., description="Transcript of the reference audio"),
    file: UploadFile = File(..., description="Reference audio file (WAV/MP3)")
):
    """
    Clone a voice from an uploaded audio sample.
    """
    logger.info(f"Registering new voice: {name}")
    
    # Save temp file
    temp_filename = f"temp_clone_{uuid.uuid4()}.wav"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        voice_id = await tts_service.register_voice(name, ref_text, temp_filename)
        
        if not voice_id:
             raise HTTPException(status_code=500, detail="Failed to register voice. Ensure QwenTTS server is running.")
             
        return {
            "voice_id": voice_id, 
            "name": name, 
            "status": "created",
            "message": "Voice cloned successfully. You can now use this voice_id in agents."
        }
        
    except Exception as e:
        logger.error(f"Error handling voice upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a registered voice."""
    logger.info(f"Deleting voice: {voice_id}")
    success = await tts_service.delete_voice(voice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Voice not found or could not be deleted")
    return {"status": "deleted", "voice_id": voice_id}
