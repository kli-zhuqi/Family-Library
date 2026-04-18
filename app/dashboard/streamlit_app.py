from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from app.database import SessionLocal
from app.models import Book
from app.services.ingestion import upload_new_books
from app.services.obsidian_sync import sync_all_books_to_obsidian

st.set_page_config(page_title="Family Library Dashboard", layout="wide")
st.title("📚 Family Library Dashboard")

DEFAULT_FOLDER = r"C:\Users\kli\Downloads\Family Library"
DEFAULT_VAULT = r"C:\Users\kli\Documents\Obsidian\Family Library Vault"

with SessionLocal() as db:
    books = db.query(Book).all()

    st.header("Overview")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total books", len(books))
    c2.metric("Complete metadata", sum(1 for b in books if b.title and b.author and b.publisher))
    c3.metric("Needs review", sum(1 for b in books if b.ingestion_status == "needs_review"))
    c4.metric("Unique authors", len({b.author for b in books if b.author}))
    c5.metric("Unique publishers", len({b.publisher for b in books if b.publisher}))
    c6.metric("Synced to Obsidian", sum(1 for b in books if b.obsidian_note_path))

    st.header("Ingestion Controls")
    folder_path = st.text_input("Local folder path (optional)", value=DEFAULT_FOLDER)
    vault_path = st.text_input("Obsidian vault path", value=DEFAULT_VAULT)

    uploaded_images = st.file_uploader(
        "Upload cover images or zip batches", type=["jpg", "jpeg", "png", "webp", "zip"], accept_multiple_files=True
    )

    if st.button("Ingest Uploaded Files"):
        with SessionLocal() as ingest_db:
            summary = upload_new_books(ingest_db, uploaded_files=uploaded_images)
        st.success(summary)

    if st.button("Upload New Books"):
        with SessionLocal() as ingest_db:
            summary = upload_new_books(ingest_db, folder_path=folder_path, uploaded_files=uploaded_images)
        st.success(summary)

    if st.button("Sync All to Obsidian"):
        with SessionLocal() as sync_db:
            summary = sync_all_books_to_obsidian(sync_db, vault_path)
        st.success(summary)

    st.header("Book Table")
    query = st.text_input("Search by title/author/publisher")
    filtered = books
    if query:
        query_lower = query.lower()
        filtered = [
            b
            for b in books
            if query_lower in (b.title or "").lower()
            or query_lower in (b.author or "").lower()
            or query_lower in (b.publisher or "").lower()
        ]

    data = [
        {
            "id": b.id,
            "image_path": b.image_path,
            "title": b.title,
            "author": b.author,
            "publisher": b.publisher,
            "reading_level": b.reading_level,
            "subject_tags": ", ".join(json.loads(b.subject_tags)) if b.subject_tags else "",
            "ingestion_status": b.ingestion_status,
            "recommended_student_types": ", ".join(json.loads(b.recommended_student_types)) if b.recommended_student_types else "",
            "obsidian_synced": bool(b.obsidian_note_path),
        }
        for b in filtered
    ]
    st.dataframe(pd.DataFrame(data), use_container_width=True)

    st.header("Book Detail")
    selected_id = st.number_input("Select Book ID", min_value=1, step=1, value=1)
    selected = next((b for b in books if b.id == selected_id), None)
    if selected:
        c_left, c_right = st.columns([1, 2])
        with c_left:
            if Path(selected.image_path).exists():
                st.image(selected.image_path, use_container_width=True)
            else:
                st.caption("Image not found on current runtime.")
        with c_right:
            st.write({
                "title": selected.title,
                "author": selected.author,
                "publisher": selected.publisher,
                "reading_level": selected.reading_level,
                "status": selected.ingestion_status,
                "note_path": selected.obsidian_note_path,
                "recommendation": selected.recommendation_explanation,
            })
            st.text_area("OCR Text", value=selected.ocr_text or "", height=200)

            st.subheader("Edit metadata")
            new_title = st.text_input("Title", value=selected.title or "", key=f"title_{selected.id}")
            new_author = st.text_input("Author", value=selected.author or "", key=f"author_{selected.id}")
            new_publisher = st.text_input("Publisher", value=selected.publisher or "", key=f"publisher_{selected.id}")
            new_reading_level = st.text_input("Reading level", value=selected.reading_level or "", key=f"reading_{selected.id}")
            new_notes = st.text_area("Manual notes", value=selected.manual_notes or "", key=f"notes_{selected.id}")

            if st.button("Save Corrections", key=f"save_{selected.id}"):
                with SessionLocal() as edit_db:
                    editable = edit_db.get(Book, selected.id)
                    if editable:
                        editable.title = new_title or None
                        editable.author = new_author or None
                        editable.publisher = new_publisher or None
                        editable.reading_level = new_reading_level or None
                        editable.manual_notes = new_notes or None
                        edit_db.commit()
                        st.success("Book metadata updated.")
