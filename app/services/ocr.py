from __future__ import annotations

from pathlib import Path

from PIL import Image


def extract_book_info_from_image(image_path: str) -> dict:
    """Basic OCR pipeline with graceful fallback.

    If pytesseract is available, it is used; otherwise, the filename and image metadata
    are used to produce a partial record for manual review.
    """
    path = Path(image_path)
    result = {
        "title": None,
        "author": None,
        "publisher": None,
        "ocr_text": None,
        "title_confidence": 0.0,
        "author_confidence": 0.0,
        "publisher_confidence": 0.0,
        "ingestion_status": "needs_review",
    }
    try:
        with Image.open(path) as img:
            _ = img.size
    except Exception:
        result["ingestion_status"] = "failed"
        return result

    filename_guess = path.stem.replace("_", " ").replace("-", " ").strip()

    try:
        import pytesseract  # type: ignore

        text = pytesseract.image_to_string(Image.open(path))
        text = " ".join(text.split())
        result["ocr_text"] = text or None
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if lines:
            result["title"] = lines[0][:500]
            result["title_confidence"] = 0.72
            result["ingestion_status"] = "partial"
        if len(lines) > 1:
            result["author"] = lines[1][:255]
            result["author_confidence"] = 0.55
        if any("press" in ln.lower() or "publisher" in ln.lower() for ln in lines):
            pub = next((ln for ln in lines if "press" in ln.lower() or "publisher" in ln.lower()), None)
            result["publisher"] = pub
            result["publisher_confidence"] = 0.45
        if result["title"]:
            result["ingestion_status"] = "success" if result["author"] else "partial"
    except Exception:
        result["title"] = filename_guess.title() if filename_guess else None
        result["ocr_text"] = filename_guess
        result["title_confidence"] = 0.3 if result["title"] else 0.0
        result["ingestion_status"] = "partial" if result["title"] else "needs_review"

    return result
