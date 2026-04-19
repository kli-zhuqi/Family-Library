from pathlib import Path

from app.services.ingestion import normalize_book_record, scan_folder_for_book_images


def test_scan_folder_for_images(tmp_path: Path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.txt").write_text("ignored")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.png").write_bytes(b"x")

    results = scan_folder_for_book_images(str(tmp_path))
    assert len(results) == 2


def test_normalize_book_record():
    normalized = normalize_book_record({"title": "  HELLO   WORLD  ", "author": "  jane DOE ", "publisher": ""})
    assert normalized["title"] == "Hello World"
    assert normalized["author"] == "jane DOE"
