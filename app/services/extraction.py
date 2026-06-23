from app.services.groq_client import groq_client
from app.config import get_settings
from app.models import VoiceMemoExtraction
from datetime import datetime
from fastapi import HTTPException
import json

settings = get_settings()

EXTRACTION_PROMPT = """You are a language specialist. You have received a blob of plain text that you need to process.

Extract all tasks and decisions from the text.

For every task return these fields:
- title: a suitable short title for the task
- description: a small description of the task
- type: must be exactly one of: personal, work, health, self_help
- characters: list of persons involved, each with name and optional role/affiliation. Empty list if none mentioned.
- deadline_iso: ISO date string (YYYY-MM-DD) only if a specific date is mentioned. Omit if not mentioned.
- timeline_raw: rough time estimate as spoken e.g "by next thursday", "tomorrow afternoon". Omit if not mentioned.
- priority: only if explicitly mentioned by the speaker. Must be exactly one of: high, medium, low. Omit if not mentioned.

For every decision return these fields:
- title: a suitable short title
- description: to the point description of the decision, not too long

Also extract:
- people: list of all persons mentioned across the entire memo, each with name and optional role/affiliation
- summary_points: exactly 2-3 bullet points summarizing what the memo touched, not listing every task

Return ONLY a valid JSON object with this exact structure, no extra text, no markdown, no backticks:
{
    "tasks": [...],
    "decisions": [...],
    "people": [...],
    "summary_points": [...]
}"""

CORRECTION_PROMPT = """The following JSON output failed validation against our schema.

Original JSON:
{broken_json}

Validation error:
{error}

Fix the JSON to match this exact structure:
{
    "tasks": [...],
    "decisions": [...],
    "people": [...],
    "summary_points": [...]
}

Return ONLY the fixed JSON, no extra text, no markdown, no backticks."""


async def extract_structure(
    transcript: str,
    recorded_at: datetime,
) -> VoiceMemoExtraction:

    # First attempt
    try:
        raw = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": transcript},
            ],
            temperature=0.1,
        )

        raw_text = raw.choices[0].message.content
        parsed = json.loads(raw_text)

        return VoiceMemoExtraction(
            recorded_at=recorded_at,
            transcript=transcript,
            **parsed,
        )

    except (json.JSONDecodeError, Exception) as first_error:
        # Second attempt — ask LLM to fix its own output
        try:
            correction = groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": CORRECTION_PROMPT.format(
                            broken_json=raw_text if "raw_text" in dir() else "No output generated",
                            error=str(first_error),
                        ),
                    },
                    {"role": "user", "content": "Fix the JSON."},
                ],
                temperature=0.1,
            )

            corrected_text = correction.choices[0].message.content
            corrected_parsed = json.loads(corrected_text)

            return VoiceMemoExtraction(
                recorded_at=recorded_at,
                transcript=transcript,
                **corrected_parsed,
            )

        except Exception as second_error:
            raise HTTPException(
                status_code=500,
                detail=f"Extraction failed after two attempts: {str(second_error)}",
            )