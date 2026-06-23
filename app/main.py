from fastapi import FastAPI
from app.routers import transcribe

app = FastAPI(
    title="Voxake",
    description="Voice memo to structured intelligence pipeline",
    version="0.1.0",
)

app.include_router(transcribe.router)