from app.services.groq_client import groq_client
from app.config import get_settings
from fastapi import UploadFile, HTTPException

settings = get_settings()

ALLOWED_AUDIO_TYPES = [
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/webm",
    "audio/ogg",
    "audio/m4a",
    "audio/x-m4a",
]

async def transcribe_audio(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Must be an audio file."
        )

    audio_bytes = await file.read()

    if len(audio_bytes) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 20MB."
        )

    transcription = groq_client.audio.transcriptions.create(
        model=settings.groq_whisper_model,
        file=(file.filename, audio_bytes),
    )

    return transcription.text