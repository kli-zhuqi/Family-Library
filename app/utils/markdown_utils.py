from __future__ import annotations

import re
from pathlib import Path


def safe_note_filename(title: str | None, author: str | None, fallback: str) -> str:
    raw = " - ".join(part for part in [title, author] if part) or fallback
    safe = re.sub(r"[\\/:*?\"<>|]", "_", raw)
    safe = re.sub(r"\s+", " ", safe).strip()
    return f"{safe}.md"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
