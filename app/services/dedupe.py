from __future__ import annotations

from difflib import SequenceMatcher

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Book


def _similar(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_duplicate_book(session: Session, normalized_record: dict) -> Book | None:
    image_hash = normalized_record.get("image_hash")
    if image_hash:
        existing = session.query(Book).filter(Book.image_hash == image_hash).first()
        if existing:
            return existing

    image_path = normalized_record.get("image_path")
    if image_path:
        existing = session.query(Book).filter(Book.image_path == image_path).first()
        if existing:
            return existing

    title = normalized_record.get("title")
    author = normalized_record.get("author")
    if title and author:
        existing = (
            session.query(Book)
            .filter(Book.title == title)
            .filter(or_(Book.author == author, Book.author.is_(None)))
            .first()
        )
        if existing:
            return existing

    if title:
        candidates = session.query(Book).filter(Book.title.is_not(None)).all()
        for candidate in candidates:
            if _similar(candidate.title, title) >= 0.9:
                if not author or _similar(candidate.author, author) >= 0.6 or not candidate.author:
                    return candidate
    return None
