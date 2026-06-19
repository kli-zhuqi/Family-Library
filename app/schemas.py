from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BookBase(BaseModel):
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    reading_level: str | None = None
    subject_tags: list[str] | None = None
    manual_notes: str | None = None


class BookUpdate(BookBase):
    pass


class BookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    ingestion_status: str
    ocr_text: str | None
    recommended_student_types: str | None
    recommendation_scores: str | None
    recommendation_explanation: str | None
    obsidian_note_path: str | None
    obsidian_last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IngestRequest(BaseModel):
    folder_path: str | None = None


class ObsidianRequest(BaseModel):
    vault_path: str = Field(..., description="Obsidian vault path")


class DeepTutorExportRequest(BaseModel):
    workspace_path: str = Field(default="data/deeptutor", description="Local DeepTutor workspace/data path")


class GenericSummary(BaseModel):
    summary: dict[str, Any]
