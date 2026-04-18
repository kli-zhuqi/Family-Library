from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Book


def list_books(session: Session, search: str | None = None, ingestion_status: str | None = None, student_type: str | None = None):
    query = session.query(Book)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Book.title.ilike(like), Book.author.ilike(like), Book.publisher.ilike(like)))
    if ingestion_status:
        query = query.filter(Book.ingestion_status == ingestion_status)
    if student_type:
        query = query.filter(Book.recommended_student_types.ilike(f"%{student_type}%"))
    return query.order_by(Book.created_at.desc()).all()
