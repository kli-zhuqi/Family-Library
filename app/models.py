from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    image_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    image_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    title_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    author_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    publisher_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="cover_photo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ingestion_status: Mapped[str] = mapped_column(String(30), default="needs_review", index=True)
    duplicate_of_book_id: Mapped[int | None] = mapped_column(ForeignKey("books.id"), nullable=True)
    recommended_student_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_scores: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subject_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    obsidian_note_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    obsidian_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    manual_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folder_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    files_scanned: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sync_type: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    books_processed: Mapped[int] = mapped_column(Integer, default=0)
    notes_created: Mapped[int] = mapped_column(Integer, default=0)
    notes_updated: Mapped[int] = mapped_column(Integer, default=0)
    sync_errors: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
