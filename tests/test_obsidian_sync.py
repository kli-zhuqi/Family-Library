import json

from app.database import Base, SessionLocal, engine
from app.models import Book
from app.services.obsidian_sync import generate_obsidian_note


def test_generate_obsidian_note(tmp_path):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        book = Book(
            title="Test Book",
            author="Author",
            image_path=str(tmp_path / "example.jpg"),
            ingestion_status="success",
            subject_tags=json.dumps(["general"]),
            recommended_student_types=json.dumps(["general_family_reading"]),
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        note_path = generate_obsidian_note(book, str(tmp_path))
        content = open(note_path, encoding="utf-8").read()
        assert "book_id" in content
        assert "Test Book" in content
