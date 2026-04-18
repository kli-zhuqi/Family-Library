from __future__ import annotations

from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS
