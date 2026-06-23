from fastapi import APIRouter, File, UploadFile, Form
from datetime import datetime
from uuid import UUID
from app.models import JobResponse

router = APIRouter()

@router.post("/transcribe", response_model=JobResponse)
async def transcribe(
    file: UploadFile = File(...),
    recorded_at: datetime = Form(...),
):
    pass

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID):
    pass