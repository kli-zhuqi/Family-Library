from __future__ import annotations

import json
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db
from app.services.deeptutor_export import export_all_books_to_deeptutor
from app.services.ingestion import collect_ingestion_images, ingest_folder, upload_new_books
from app.services.obsidian_sync import import_obsidian_edits, sync_all_books_to_obsidian, sync_book_to_obsidian

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Family Library Management System")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/books", response_model=list[schemas.BookResponse])
def get_books(
    search: str | None = None,
    ingestion_status: str | None = None,
    student_type: str | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_books(db, search=search, ingestion_status=ingestion_status, student_type=student_type)


@app.get("/books/{book_id}", response_model=schemas.BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books/ingest")
async def ingest_books(
    folder_path: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
    db: Session = Depends(get_db),
):
    if files:
        images = collect_ingestion_images(uploaded_files=files)
        if not images:
            raise HTTPException(status_code=400, detail="No supported images found in uploads")
        from app.services.ingestion import _process_images  # local import for explicit use

        return _process_images(db, images, mode="upload_ingest")
    if folder_path:
        return ingest_folder(db, folder_path)
    raise HTTPException(status_code=400, detail="Provide folder_path or uploaded files")


@app.post("/books/upload-new")
async def upload_new(
    folder_path: str | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
    db: Session = Depends(get_db),
):
    if not files and not folder_path:
        raise HTTPException(status_code=400, detail="Provide folder_path or uploaded files")
    return upload_new_books(db, folder_path=folder_path, uploaded_files=files)


@app.post("/books/upload-batch")
async def upload_batch(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    return upload_new_books(db, uploaded_files=files)


@app.put("/books/{book_id}", response_model=schemas.BookResponse)
def update_book(book_id: int, payload: schemas.BookUpdate, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    data = payload.model_dump(exclude_unset=True)
    if "subject_tags" in data and data["subject_tags"] is not None:
        data["subject_tags"] = json.dumps(data["subject_tags"])
    for key, value in data.items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


@app.get("/recommendations")
def recommendations(db: Session = Depends(get_db)):
    books = db.query(models.Book).all()
    return [
        {
            "book_id": b.id,
            "title": b.title,
            "recommended_student_types": b.recommended_student_types,
            "recommendation_scores": b.recommendation_scores,
            "recommendation_explanation": b.recommendation_explanation,
        }
        for b in books
    ]


@app.get("/recommendations/{book_id}")
def recommendation_for_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {
        "book_id": book.id,
        "recommended_student_types": book.recommended_student_types,
        "recommendation_scores": book.recommendation_scores,
        "recommendation_explanation": book.recommendation_explanation,
    }


@app.post("/obsidian/sync-all")
def sync_all(payload: schemas.ObsidianRequest, db: Session = Depends(get_db)):
    return sync_all_books_to_obsidian(db, payload.vault_path)


@app.post("/obsidian/sync-book/{book_id}")
def sync_book(book_id: int, payload: schemas.ObsidianRequest, db: Session = Depends(get_db)):
    return sync_book_to_obsidian(db, book_id, payload.vault_path)


@app.post("/obsidian/import-edits")
def import_edits(payload: schemas.ObsidianRequest, db: Session = Depends(get_db)):
    return import_obsidian_edits(db, payload.vault_path)


@app.get("/obsidian/status")
def obsidian_status(db: Session = Depends(get_db)):
    total = db.query(func.count(models.Book.id)).scalar() or 0
    synced = db.query(func.count(models.Book.id)).filter(models.Book.obsidian_note_path.is_not(None)).scalar() or 0
    last_sync = db.query(func.max(models.Book.obsidian_last_synced_at)).scalar()
    return {"total_books": total, "synced_books": synced, "last_sync": last_sync}


@app.post("/deeptutor/export-library")
def export_deeptutor_library(payload: schemas.DeepTutorExportRequest, db: Session = Depends(get_db)):
    return export_all_books_to_deeptutor(db, payload.workspace_path)
