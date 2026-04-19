from __future__ import annotations

import json
import hashlib
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import Book, IngestionRun
from app.services.dedupe import find_duplicate_book
from app.services.llm_enrichment import enrich_record
from app.services.ocr import extract_book_info_from_image
from app.services.recommendation import infer_reading_level, infer_subject_tags, recommend_student_types
from app.utils.image_utils import IMAGE_EXTENSIONS, is_supported_image
from app.utils.text_utils import clean_text, normalize_capitalization

UPLOAD_RAW_DIR = Path("uploads/raw")
UPLOAD_RAW_DIR.mkdir(parents=True, exist_ok=True)


def scan_folder_for_book_images(folder_path: str) -> list[str]:
    root = Path(folder_path)
    if not root.exists():
        return []
    return [str(path.resolve()) for path in root.rglob("*") if path.is_file() and is_supported_image(path)]


def save_uploaded_files(uploaded_files: Iterable) -> list[str]:
    saved_images: list[str] = []
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for upload in uploaded_files:
        filename = Path(getattr(upload, "filename", getattr(upload, "name", "uploaded.bin"))).name
        batch_dir = UPLOAD_RAW_DIR / timestamp
        batch_dir.mkdir(parents=True, exist_ok=True)
        target = batch_dir / filename
        print(
            f"[DEBUG] Saving file: {filename}, size={getattr(upload, 'size', 'unknown')}, "
            f"target path={target}"
        )
        content = upload.file.read() if hasattr(upload, "file") else upload.read()
        if hasattr(upload, "file"):
            upload.file.seek(0)
        elif hasattr(upload, "seek"):
            upload.seek(0)
        target.write_bytes(content)

        if target.suffix.lower() == ".zip":
            extract_dir = UPLOAD_RAW_DIR / f"extracted_{timestamp}_{target.stem}"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target, "r") as zf:
                zf.extractall(extract_dir)
            for item in extract_dir.rglob("*"):
                if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                    saved_images.append(str(item.resolve()))
        elif target.suffix.lower() in IMAGE_EXTENSIONS:
            saved_images.append(str(target.resolve()))

    return saved_images


def _compute_file_hash(image_path: str) -> str:
    digest = hashlib.sha256()
    with open(image_path, "rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_ingestion_images(folder_path: str | None = None, uploaded_files=None) -> list[str]:
    if uploaded_files:
        return save_uploaded_files(uploaded_files)
    if folder_path:
        return scan_folder_for_book_images(folder_path)
    return []


def normalize_book_record(record: dict) -> dict:
    normalized = record.copy()
    for field in ["title", "author", "publisher"]:
        normalized[field] = normalize_capitalization(clean_text(normalized.get(field)))
    return normalized


def save_book_record(session: Session, record: dict) -> tuple[Book, str]:
    duplicate = find_duplicate_book(session, record)
    if duplicate:
        changed = False
        for field, conf_field in [("title", "title_confidence"), ("author", "author_confidence"), ("publisher", "publisher_confidence")]:
            incoming = record.get(field)
            if not incoming:
                continue
            existing = getattr(duplicate, field)
            incoming_conf = record.get(conf_field) or 0.0
            existing_conf = getattr(duplicate, conf_field) or 0.0
            if not existing or incoming_conf > existing_conf:
                setattr(duplicate, field, incoming)
                setattr(duplicate, conf_field, incoming_conf)
                changed = True

        for field in [
            "ocr_text",
            "ingestion_status",
            "recommended_student_types",
            "recommendation_scores",
            "recommendation_explanation",
            "reading_level",
            "subject_tags",
            "language",
        ]:
            if record.get(field) and getattr(duplicate, field) != record.get(field):
                setattr(duplicate, field, record.get(field))
                changed = True

        if changed:
            duplicate.updated_at = datetime.utcnow()
            session.add(duplicate)
            session.commit()
            session.refresh(duplicate)
            return duplicate, "updated"
        return duplicate, "skipped"

    book = Book(**record)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book, "created"


def _process_images(session: Session, images: list[str], mode: str = "ingest") -> dict:
    run = IngestionRun(folder_path=mode, files_scanned=len(images))
    session.add(run)
    session.commit()

    summary = {"files_scanned": len(images), "records_created": 0, "records_updated": 0, "records_skipped": 0, "records_failed": 0}

    for image_path in images:
        existing = session.query(Book).filter(Book.image_path == image_path).first()
        if mode == "upload_new" and existing:
            summary["records_skipped"] += 1
            continue

        extracted = extract_book_info_from_image(image_path)
        extracted["image_path"] = image_path
        extracted["image_hash"] = _compute_file_hash(image_path)
        extracted = normalize_book_record(extracted)
        extracted = enrich_record(extracted)

        extracted["subject_tags"] = json.dumps(infer_subject_tags(extracted))
        extracted["reading_level"] = infer_reading_level(extracted)
        rec = recommend_student_types(extracted)
        extracted["recommended_student_types"] = json.dumps(rec["recommended_student_types"])
        extracted["recommendation_scores"] = json.dumps(rec["recommendation_scores"])
        extracted["recommendation_explanation"] = rec["recommendation_explanation"]

        if extracted.get("ingestion_status") == "failed":
            summary["records_failed"] += 1

        _, status = save_book_record(session, extracted)
        if status == "created":
            summary["records_created"] += 1
        elif status == "updated":
            summary["records_updated"] += 1
        else:
            summary["records_skipped"] += 1

    run.completed_at = datetime.utcnow()
    run.records_created = summary["records_created"]
    run.records_updated = summary["records_updated"]
    run.records_failed = summary["records_failed"]
    run.notes = json.dumps(summary)
    session.commit()
    print(
        f"[DEBUG] files_scanned={summary['files_scanned']}, records_created={summary['records_created']}, "
        f"records_skipped={summary['records_skipped']}, records_failed={summary['records_failed']}"
    )
    return summary


def ingest_folder(session: Session, folder_path: str) -> dict:
    images = scan_folder_for_book_images(folder_path)
    return _process_images(session, images, mode=folder_path)


def upload_new_books(session: Session, folder_path: str | None = None, uploaded_files=None) -> dict:
    print(f"[DEBUG] Uploaded files received: {uploaded_files}")
    for file_obj in uploaded_files or []:
        print(
            f"[DEBUG] Name: {getattr(file_obj, 'name', getattr(file_obj, 'filename', 'unknown'))}, "
            f"Size: {getattr(file_obj, 'size', 'unknown')}, Type: {getattr(file_obj, 'type', 'unknown')}"
        )
    images = collect_ingestion_images(folder_path=folder_path, uploaded_files=uploaded_files)
    return _process_images(session, images, mode="upload_new")
