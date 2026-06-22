from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from enum import Enum
from uuid import UUID


class TaskType(str, Enum):
    personal = "personal"
    work = "work"
    health = "health"
    self_help = "self_help"


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class JobStatus(str, Enum):
    pending = "pending"
    transcribing = "transcribing"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Person(BaseModel):
    name: str
    role: Optional[str] = None
    affiliation: Optional[str] = None


class Decision(BaseModel):
    title: str
    description: Optional[str] = None


class Task(BaseModel):
    title: str
    description: str
    type: TaskType
    characters: list[Person] = []
    deadline_iso: Optional[date] = None
    timeline_raw: Optional[str] = None
    priority: Optional[Priority] = None


class VoiceMemoExtraction(BaseModel):
    id: UUID
    recorded_at: datetime
    transcript: str
    summary_points: list[str]
    tasks: list[Task]
    decisions: list[Decision]
    people: list[Person]
    status: JobStatus = JobStatus.pending
    error_message: Optional[str] = None