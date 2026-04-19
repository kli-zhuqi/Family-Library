from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.models import Book, SyncRun
from app.utils.markdown_utils import ensure_parent, safe_note_filename


def generate_obsidian_note(book: Book, vault_path: str) -> str:
    vault = Path(vault_path)
    notes_dir = vault / "Books"
    filename = safe_note_filename(book.title, book.author, f"book-{book.id}")
    note_path = notes_dir / filename
    ensure_parent(note_path)

    frontmatter = {
        "book_id": book.id,
        "title": book.title,
        "author": book.author,
        "publisher": book.publisher,
        "reading_level": book.reading_level,
        "subject_tags": json.loads(book.subject_tags) if book.subject_tags else [],
        "recommended_student_types": json.loads(book.recommended_student_types)
        if book.recommended_student_types
        else [],
        "ingestion_status": book.ingestion_status,
        "image_path": book.image_path,
    }

    body = [
        "# Book Summary",
        book.recommendation_explanation or "No recommendation explanation yet.",
        "",
        "# OCR Text",
        book.ocr_text or "",
        "",
        "# Manual Notes",
        book.manual_notes or "",
    ]

    content = f"---\n{yaml.safe_dump(frontmatter, sort_keys=False)}---\n\n" + "\n".join(body)
    note_path.write_text(content, encoding="utf-8")
    return str(note_path)


def sync_book_to_obsidian(session: Session, book_id: int, vault_path: str) -> dict:
    book = session.get(Book, book_id)
    if not book:
        return {"status": "not_found", "book_id": book_id}

    note_path = generate_obsidian_note(book, vault_path)
    book.obsidian_note_path = note_path
    book.obsidian_last_synced_at = datetime.utcnow()
    session.commit()
    return {"status": "synced", "book_id": book_id, "note_path": note_path}


def sync_all_books_to_obsidian(session: Session, vault_path: str) -> dict:
    run = SyncRun(sync_type="obsidian_export")
    session.add(run)
    session.commit()

    created_or_updated = 0
    for book in session.query(Book).all():
        sync_book_to_obsidian(session, book.id, vault_path)
        created_or_updated += 1

    run.books_processed = created_or_updated
    run.notes_updated = created_or_updated
    run.completed_at = datetime.utcnow()
    session.commit()
    return {"books_processed": created_or_updated, "notes_updated": created_or_updated}


def import_obsidian_edits(session: Session, vault_path: str) -> dict:
    books_dir = Path(vault_path) / "Books"
    updated = 0
    conflicts = []
    if not books_dir.exists():
        return {"updated": 0, "conflicts": ["Books directory not found"]}

    for note in books_dir.glob("*.md"):
        content = note.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        try:
            _, fm, body = content.split("---", 2)
            data = yaml.safe_load(fm) or {}
        except Exception:
            conflicts.append(f"Invalid frontmatter in {note.name}")
            continue

        book_id = data.get("book_id")
        if not book_id:
            continue
        book = session.get(Book, int(book_id))
        if not book:
            conflicts.append(f"book_id {book_id} missing for {note.name}")
            continue

        allowed_fields = ["title", "author", "publisher", "reading_level", "subject_tags"]
        changed = False
        for field in allowed_fields:
            if field in data and data[field] is not None:
                new_value = data[field]
                if field == "subject_tags":
                    new_value = json.dumps(new_value)
                if getattr(book, field) != new_value:
                    setattr(book, field, new_value)
                    changed = True

        manual_marker = "# Manual Notes"
        if manual_marker in body:
            manual_notes = body.split(manual_marker, 1)[1].strip()
            if book.manual_notes != manual_notes:
                book.manual_notes = manual_notes
                changed = True

        if changed:
            updated += 1

    session.commit()
    return {"updated": updated, "conflicts": conflicts}
