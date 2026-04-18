from __future__ import annotations

import re


def clean_text(value: str | None) -> str | None:
    if not value:
        return value
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"([\-_=])\1{2,}", r"\1", value)
    return value


def normalize_capitalization(value: str | None) -> str | None:
    if not value:
        return value
    if value.isupper() and len(value.split()) > 1:
        return value.title()
    return value
