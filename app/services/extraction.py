from app.services.groq_client import groq_client
from app.config import get_settings
from app.models import VoiceMemoExtraction
from datetime import datetime
from fastapi import HTTPException
from pydantic import ValidationError
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

CORRECTION_PROMPT = """The following JSON was parsed successfully but failed Pydantic validation.

JSON:
{valid_json}

Validation error:
{error}

Fix the JSON to match the schema exactly. Pay attention to:
- type field must be one of: personal, work, health, self_help
- priority if present must be one of: high, medium, low
- deadline_iso must be YYYY-MM-DD format if present

Return ONLY the fixed JSON, no extra text, no markdown, no backticks."""


def _call_llm(system_prompt: str, user_message: str) -> str:
    response = groq_client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content


async def extract_structure(
    transcript: str,
    recorded_at: datetime,
) -> VoiceMemoExtraction:

    # Step 1: Call LLM with transcript
    raw_text = _call_llm(EXTRACTION_PROMPT, transcript)

    # Step 2: Parse JSON — retry same prompt once if malformed
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raw_text = _call_llm(EXTRACTION_PROMPT, transcript)
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"LLM returned malformed JSON twice: {str(e)}",
            )

    # Step 3: Validate against Pydantic — send correction prompt if invalid
    try:
        return VoiceMemoExtraction(
            recorded_at=recorded_at,
            transcript=transcript,
            **parsed,
        )
    except ValidationError as e:
        corrected_text = _call_llm(
            CORRECTION_PROMPT.format(
                valid_json=json.dumps(parsed, indent=2),
                error=str(e),
            ),
            "Fix the JSON.",
        )
        try:
            corrected_parsed = json.loads(corrected_text)
            return VoiceMemoExtraction(
                recorded_at=recorded_at,
                transcript=transcript,
                **corrected_parsed,
            )
        except Exception as final_error:
            raise HTTPException(
                status_code=500,
                detail=f"Extraction failed after correction attempt: {str(final_error)}",
            )