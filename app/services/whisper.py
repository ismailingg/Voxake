from app.services.groq_client import groq_client
from app.config import get_settings
from fastapi import HTTPException

settings = get_settings()

ALLOWED_EXTENSIONS = [
    ".mp3", ".mp4", ".wav", 
    ".webm", ".ogg", ".m4a"
]

async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    ext = "." + filename.split(".")[-1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {ext}. Must be an audio file."
        )

    if len(audio_bytes) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 20MB."
        )

    transcription = groq_client.audio.transcriptions.create(
        model=settings.groq_whisper_model,
        file=(filename, audio_bytes),
    )

    return transcription.text