from pathlib import Path

from app.services.ingestion import normalize_book_record, save_uploaded_files, scan_folder_for_book_images
from app.utils.image_utils import is_loadable_image


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


class _FakeUpload:
    def __init__(self, name: str, content: bytes, content_type: str = "image/jpeg"):
        self.name = name
        self._content = content
        self.type = content_type
        self.size = len(content)
        self._pos = 0

    def read(self) -> bytes:
        data = self._content[self._pos :]
        self._pos = len(self._content)
        return data

    def seek(self, pos: int) -> None:
        self._pos = pos


def test_save_uploaded_files_uses_name_attribute_for_extension(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.services.ingestion.UPLOAD_RAW_DIR", tmp_path)
    uploaded = _FakeUpload("cover.jpg", b"fake-image-bytes")
    saved = save_uploaded_files([uploaded])
    assert len(saved) == 1
    assert saved[0].endswith(".jpg")


def test_upload_new_books_accepts_iterable_uploads(tmp_path: Path, monkeypatch):
    from app.database import Base, SessionLocal, engine
    from app.services.ingestion import upload_new_books

    monkeypatch.setattr("app.services.ingestion.UPLOAD_RAW_DIR", tmp_path)
    Base.metadata.create_all(bind=engine)
    uploads = (item for item in [_FakeUpload("cover2.jpg", b"fake-image-bytes-2")])

    with SessionLocal() as session:
        summary = upload_new_books(session, uploaded_files=uploads)

    assert summary["files_scanned"] == 1


def test_is_loadable_image_rejects_invalid_bytes(tmp_path: Path):
    fake_image = tmp_path / "fake.jpg"
    fake_image.write_bytes(b"not-an-image")
    assert is_loadable_image(fake_image) is False
