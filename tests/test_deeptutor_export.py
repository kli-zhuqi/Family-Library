import json

from app.database import Base, SessionLocal, engine
from app.models import Book
from app.services.deeptutor_export import export_all_books_to_deeptutor, generate_deeptutor_source


def test_generate_deeptutor_source_writes_markdown(tmp_path):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        book = Book(
            title="Physics Workbook",
            author="Ada Tutor",
            publisher="STEM Press",
            image_path=str(tmp_path / "physics.jpg"),
            subject_tags=json.dumps(["physics", "practice"]),
            recommended_student_types=json.dumps(["stem_student"]),
            recommendation_explanation="Good practice for STEM learners.",
            ocr_text="Forces and motion",
            ingestion_status="reviewed",
        )
        db.add(book)
        db.commit()
        db.refresh(book)

        path = generate_deeptutor_source(book, str(tmp_path / "deeptutor"))
        content = open(path, encoding="utf-8").read()

    assert "source: family-library" in content
    assert "# Physics Workbook" in content
    assert "Forces and motion" in content


def test_export_all_books_to_deeptutor_returns_next_steps(tmp_path):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add(Book(title="Family Stories", image_path=str(tmp_path / "story.jpg")))
        db.commit()

        result = export_all_books_to_deeptutor(db, str(tmp_path / "deeptutor"))

    assert result["books_processed"] >= 1
    assert result["sources_dir"].endswith("knowledge_sources/family_library")
    assert result["next_steps"]
