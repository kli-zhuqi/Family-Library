from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.models import Book, SyncRun
from app.utils.markdown_utils import ensure_parent, safe_note_filename


def _json_list(value: str | None) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def generate_deeptutor_source(book: Book, workspace_path: str) -> str:
    """Write a DeepTutor-ready Markdown source document for one library book."""
    workspace = Path(workspace_path)
    source_dir = workspace / "knowledge_sources" / "family_library"
    filename = safe_note_filename(book.title, book.author, f"book-{book.id}")
    source_path = source_dir / filename
    ensure_parent(source_path)

    frontmatter = {
        "source": "family-library",
        "book_id": book.id,
        "title": book.title,
        "author": book.author,
        "publisher": book.publisher,
        "reading_level": book.reading_level,
        "subject_tags": _json_list(book.subject_tags),
        "recommended_student_types": _json_list(book.recommended_student_types),
        "ingestion_status": book.ingestion_status,
        "cover_image_path": book.image_path,
        "exported_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    body = [
        f"# {book.title or f'Book {book.id}'}",
        "",
        "## Bibliographic Metadata",
        f"- Author: {book.author or 'Unknown'}",
        f"- Publisher: {book.publisher or 'Unknown'}",
        f"- Reading level: {book.reading_level or 'Unspecified'}",
        f"- Subject tags: {', '.join(_json_list(book.subject_tags)) or 'None'}",
        "",
        "## Family Library Recommendation",
        book.recommendation_explanation or "No recommendation explanation is available yet.",
        "",
        "## Manual Notes",
        book.manual_notes or "No manual notes yet.",
        "",
        "## OCR Text",
        book.ocr_text or "No OCR text captured yet.",
    ]

    content = f"---\n{yaml.safe_dump(frontmatter, sort_keys=False)}---\n\n" + "\n".join(body) + "\n"
    source_path.write_text(content, encoding="utf-8")
    return str(source_path)


def export_all_books_to_deeptutor(session: Session, workspace_path: str) -> dict:
    """Export all Family Library records as Markdown sources for DeepTutor KB import."""
    run = SyncRun(sync_type="deeptutor_export")
    session.add(run)
    session.commit()

    exported_paths = []
    for book in session.query(Book).order_by(Book.id).all():
        exported_paths.append(generate_deeptutor_source(book, workspace_path))

    run.books_processed = len(exported_paths)
    run.notes_updated = len(exported_paths)
    run.completed_at = datetime.utcnow()
    run.notes = f"Exported to {workspace_path}"
    session.commit()

    return {
        "books_processed": len(exported_paths),
        "sources_dir": str(Path(workspace_path) / "knowledge_sources" / "family_library"),
        "exported_paths": exported_paths,
        "next_steps": [
            "Start DeepTutor with docker compose -f docker-compose.deeptutor.yml up",
            "Open http://127.0.0.1:3782 and create/import a Knowledge Base from the exported Markdown files.",
        ],
    }
