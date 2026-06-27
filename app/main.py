from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import transcribe

app = FastAPI(
    title="Voxake",
    description="Voice memo to structured intelligence pipeline",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://voxake-frontend.vercel.app", 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcribe.router)