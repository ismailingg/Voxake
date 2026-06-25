from app.services.supabase_client import supabase
from app.models import JobStatus, JobResponse, VoiceMemoExtraction
from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
import json

def create_job(job_id: UUID, recorded_at: datetime, file_path: str) -> None:
    supabase.table("jobs").insert({
        "id": str(job_id),
        "status": JobStatus.pending.value,
        "recorded_at": recorded_at.isoformat(),
        "file_path": file_path,
    }).execute()


def update_job_status(job_id: UUID, status: JobStatus) -> None:
    supabase.table("jobs").update({
        "status": status.value,
    }).eq("id", str(job_id)).execute()


def update_job_result(job_id: UUID, result: VoiceMemoExtraction) -> None:
    supabase.table("jobs").update({
        "status": JobStatus.completed.value,
        "transcript": result.transcript,
        "result": json.loads(result.model_dump_json()),
    }).eq("id", str(job_id)).execute()


def update_job_error(job_id: UUID, error_message: str) -> None:
    supabase.table("jobs").update({
        "status": JobStatus.failed.value,
        "error_message": error_message,
    }).eq("id", str(job_id)).execute()


def get_job(job_id: UUID) -> JobResponse:
    response = supabase.table("jobs").select("*").eq(
        "id", str(job_id)
    ).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Job not found")

    row = response.data[0]

    return JobResponse(
        id=row["id"],
        status=row["status"],
        error_message=row.get("error_message"),
        result=VoiceMemoExtraction(**row["result"]) if row.get("result") else None,
    )