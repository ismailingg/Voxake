from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks, HTTPException, Request
from datetime import datetime
from uuid import UUID, uuid4
from app.models import JobResponse, JobStatus
from app.services.whisper import transcribe_audio
from app.services.extraction import extract_structure
from app.services.supabase_client import supabase
from app.services.supabase_service import (
    create_job,
    update_job_status,
    update_job_result,
    update_job_error,
    get_job,
)
from app.limiter import limiter

router = APIRouter()


async def process_memo(
    job_id: UUID,
    file_path: str,
    recorded_at: datetime,
):
    try:
        # Step 1: transcribing
        update_job_status(job_id, JobStatus.transcribing)
        audio_response = supabase.storage.from_("memos").download(file_path)
        transcript = await transcribe_audio(audio_response, file_path)

        # Step 2: processing
        update_job_status(job_id, JobStatus.processing)
        result = await extract_structure(transcript, recorded_at)

        # Step 3: completed
        update_job_result(job_id, result)

    except Exception as e:
        update_job_error(job_id, str(e))


@router.post("/transcribe", response_model=JobResponse)
@limiter.limit("5/minute")
async def transcribe(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    recorded_at: datetime = Form(...),
):
    # Validate file type early before reading bytes
    ALLOWED_TYPES = [
        "audio/mpeg", "audio/mp4", "audio/wav",
        "audio/webm", "audio/ogg", "audio/m4a", "audio/x-m4a",
    ]
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}"
        )

    # Upload to Supabase Storage
    job_id = uuid4()
    file_path = f"memos/{job_id}_{file.filename}"
    file_bytes = await file.read()

    supabase.storage.from_("memos").upload(
        path=file_path,
        file=file_bytes,
        file_options={"content-type": file.content_type},
    )

    # Create job row in pending state
    create_job(job_id, recorded_at, file_path)

    # Kick off background task and return immediately
    background_tasks.add_task(process_memo, job_id, file_path, recorded_at)

    return JobResponse(id=job_id, status=JobStatus.pending)


@router.get("/jobs/{job_id}", response_model=JobResponse)
@limiter.limit("60/minute")
async def get_job_status(request: Request, job_id: UUID):
    return get_job(job_id)